import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import akshare as ak
import pandas as pd
from sqlalchemy import text

from runtime import get_db_engine, get_env_int, get_logger, wait_for_rate_limit

logger = get_logger('stock_price_tracking')

PRICE_TRACKING_MAX_WORKERS = max(get_env_int('PRICE_TRACKING_MAX_WORKERS', 4), 1)
PRICE_TRACKING_RETRY_TIMES = max(get_env_int('PRICE_TRACKING_RETRY_TIMES', 3), 1)
PRICE_TRACKING_RETRY_DELAY_SECONDS = max(get_env_int('PRICE_TRACKING_RETRY_DELAY_SECONDS', 1), 0)
DB_WRITE_BATCH_SIZE = max(get_env_int('DB_WRITE_BATCH_SIZE', 2000), 1)
EASTMONEY_KLINE_INTERVAL_SECONDS = max(get_env_int('EASTMONEY_KLINE_INTERVAL_SECONDS', 10), 0)


def fetch_stock_list():
    engine = get_db_engine()
    with engine.connect() as conn:
        result = conn.execute(text('SELECT stock_code, begin_time FROM stock_base'))
        rows = result.fetchall()

    if not rows:
        return pd.DataFrame(columns=['stock_code', 'begin_time'])

    df = pd.DataFrame(rows, columns=['stock_code', 'begin_time'])
    df['stock_code'] = df['stock_code'].astype(str)
    df['begin_time'] = pd.to_datetime(df['begin_time'], errors='coerce')
    return df[df['begin_time'].notna()].copy()


def fetch_last_times(codes):
    if not codes:
        return {}

    engine = get_db_engine()
    placeholders = ', '.join([f':code_{index}' for index in range(len(codes))])
    params = {f'code_{index}': code for index, code in enumerate(codes)}

    with engine.connect() as conn:
        query = text(
            f"""
            SELECT stock_code, MAX(track_time) AS last_time
            FROM stock_price_tracking
            WHERE stock_code IN ({placeholders})
            GROUP BY stock_code
            """
        )
        rows = conn.execute(query, params).fetchall()

    return {str(row[0]): row[1] for row in rows}


def to_float(value, default=None):
    if pd.isna(value):
        return default
    return float(value)


def prepare_quote_rows(code, quote):
    if quote is None or quote.empty:
        return []

    prepared = quote.copy()
    prepared.columns = [str(col).strip() for col in prepared.columns]

    required_columns = ['时间', '开盘', '收盘', '最高', '最低', '涨跌幅', '成交量', '成交额']
    missing_columns = [column for column in required_columns if column not in prepared.columns]
    if missing_columns:
        raise ValueError(f'行情字段缺失: {missing_columns}')

    prepared['时间'] = pd.to_datetime(prepared['时间'], errors='coerce')
    for column in ['开盘', '收盘', '最高', '最低', '涨跌幅', '成交量', '成交额']:
        prepared[column] = pd.to_numeric(prepared[column], errors='coerce')

    prepared = prepared[prepared['时间'].notna()].copy()
    prepared = prepared.dropna(subset=['开盘', '收盘', '最高', '最低'])
    if prepared.empty:
        logger.warning('%s 行情数据缺少有效价格列，全部跳过', code)
        return []

    rows = []
    for _, row in prepared.iterrows():
        track_time = pd.Timestamp(row['时间']).to_pydatetime()
        rows.append(
            {
                'stock_code': code,
                'track_time': track_time,
                'current_price': to_float(row['收盘']),
                'open_price': to_float(row['开盘']),
                'high_price': to_float(row['最高']),
                'low_price': to_float(row['最低']),
                'volume': to_float(row['成交量'], 0.0),
                'amount': to_float(row['成交额'], 0.0),
                'change_rate': to_float(row['涨跌幅'], 0.0),
            }
        )

    return rows


def insert_quotes(rows: list[dict]):
    if not rows:
        return 0

    sql = text(
        """
        INSERT INTO stock_price_tracking (
            stock_code, track_time, current_price, open_price, high_price, low_price,
            volume, amount, change_rate
        ) VALUES (
            :stock_code, :track_time, :current_price, :open_price, :high_price, :low_price,
            :volume, :amount, :change_rate
        ) ON DUPLICATE KEY UPDATE
            current_price = VALUES(current_price),
            open_price = VALUES(open_price),
            high_price = VALUES(high_price),
            low_price = VALUES(low_price),
            volume = VALUES(volume),
            amount = VALUES(amount),
            change_rate = VALUES(change_rate)
        """
    )

    engine = get_db_engine()
    with engine.begin() as conn:
        for start in range(0, len(rows), DB_WRITE_BATCH_SIZE):
            batch = rows[start : start + DB_WRITE_BATCH_SIZE]
            conn.execute(sql, batch)

    return len(rows)


def format_begin_time(begin):
    try:
        return pd.to_datetime(begin).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return str(begin)


def fetch_quote_rows(code, begin):
    start_time = format_begin_time(begin)
    for attempt in range(1, PRICE_TRACKING_RETRY_TIMES + 1):
        try:
            wait_for_rate_limit(
                'eastmoney-kline-minute',
                EASTMONEY_KLINE_INTERVAL_SECONDS,
                logger=logger,
                label='30 分钟行情采集',
            )
            quote = ak.stock_zh_a_hist_min_em(
                symbol=code,
                period='30',
                adjust='qfq',
                start_date=start_time,
            )
            if quote is None or quote.empty:
                logger.info('%s 无新增行情数据', code)
                return []

            rows = prepare_quote_rows(code, quote)
            logger.info('%s 采集完成，记录=%s', code, len(rows))
            return rows
        except Exception:
            logger.exception('%s 第 %s 次采集失败', code, attempt)
            if attempt == PRICE_TRACKING_RETRY_TIMES:
                raise
            time.sleep(PRICE_TRACKING_RETRY_DELAY_SECONDS * attempt)

    return []


def run_price_tracking():
    logger.info(
        '开始价格跟踪，最大并发=%s，重试次数=%s，东财 K 线最小间隔=%s 秒',
        PRICE_TRACKING_MAX_WORKERS,
        PRICE_TRACKING_RETRY_TIMES,
        EASTMONEY_KLINE_INTERVAL_SECONDS,
    )
    stock_df = fetch_stock_list()
    if stock_df.empty:
        logger.info('stock_base 为空，无需执行价格跟踪')
        return

    codes = stock_df['stock_code'].tolist()
    last_times = fetch_last_times(codes)
    max_workers = min(PRICE_TRACKING_MAX_WORKERS, len(stock_df))
    failed_codes = []
    buffered_rows = []
    written_count = 0

    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='price-track') as executor:
        futures = {
            executor.submit(fetch_quote_rows, code, last_times.get(code, begin)): code
            for code, begin in stock_df.itertuples(index=False)
        }

        for future in as_completed(futures):
            code = futures[future]
            try:
                rows = future.result()
                if rows:
                    buffered_rows.extend(rows)
                    if len(buffered_rows) >= DB_WRITE_BATCH_SIZE * 2:
                        written_count += insert_quotes(buffered_rows)
                        logger.info('已批量写入行情数据，累计记录=%s', written_count)
                        buffered_rows = []
            except Exception:
                failed_codes.append(code)
                logger.exception('%s 行情任务失败', code)

    if buffered_rows:
        written_count += insert_quotes(buffered_rows)

    logger.info('价格跟踪任务完成，写入记录=%s，失败股票数=%s', written_count, len(failed_codes))
    if failed_codes:
        preview = ','.join(failed_codes[:10])
        raise RuntimeError(f'价格跟踪存在失败股票，数量={len(failed_codes)}，示例={preview}')


if __name__ == '__main__':
    run_price_tracking()
