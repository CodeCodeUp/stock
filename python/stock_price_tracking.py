import logging
import os

import akshare as ak
import pandas as pd
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='price_tracking.log',
)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'host.docker.internal'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'stock'),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
}

_ENGINE = None


def get_db_engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE

    connection_string = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset={DB_CONFIG['charset']}"
    )
    _ENGINE = create_engine(connection_string, pool_pre_ping=True)
    return _ENGINE


def fetch_stock_list():
    engine = get_db_engine()
    with engine.connect() as conn:
        result = conn.execute(text('SELECT stock_code, begin_time FROM stock_base'))
        rows = result.fetchall()

    if not rows:
        return pd.DataFrame(columns=['stock_code', 'begin_time'])

    df = pd.DataFrame(rows, columns=['stock_code', 'begin_time'])
    df['stock_code'] = df['stock_code'].astype(str)
    df['begin_time'] = pd.to_datetime(df['begin_time'])
    return df


def fetch_last_times(codes):
    if not codes:
        return {}

    engine = get_db_engine()
    placeholders = ', '.join([f':code_{i}' for i in range(len(codes))])
    params = {f'code_{i}': code for i, code in enumerate(codes)}

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


def prepare_quote_rows(code, quote):
    if quote is None or quote.empty:
        return []

    prepared = quote.copy()
    prepared.columns = [str(col).strip() for col in prepared.columns]

    required_columns = ['时间', '开盘', '收盘', '最高', '最低', '涨跌幅', '成交量', '成交额']
    missing_columns = [col for col in required_columns if col not in prepared.columns]
    if missing_columns:
        raise ValueError(f'行情字段缺失: {missing_columns}')

    prepared['时间'] = pd.to_datetime(prepared['时间'])
    for col in ['开盘', '收盘', '最高', '最低', '涨跌幅', '成交量', '成交额']:
        prepared[col] = pd.to_numeric(prepared[col], errors='coerce').fillna(0)

    rows = []
    for _, row in prepared.iterrows():
        track_time = pd.Timestamp(row['时间']).to_pydatetime()
        open_price = float(row['开盘'])
        current_price = float(row['收盘'])
        high_price = float(row['最高'])
        low_price = float(row['最低'])
        change_rate = float(row['涨跌幅'])
        volume = float(row['成交量'])
        amount = float(row['成交额'])

        rows.append(
            {
                'stock_code': code,
                'track_time': track_time,
                'current_price': current_price,
                'open_price': open_price,
                'high_price': high_price,
                'low_price': low_price,
                'volume': volume,
                'amount': amount,
                'change_rate': change_rate,
            }
        )

        if track_time.hour == 10 and track_time.minute == 0:
            rows.append(
                {
                    'stock_code': code,
                    'track_time': track_time.replace(hour=9, minute=30, second=0, microsecond=0),
                    'current_price': open_price,
                    'open_price': open_price,
                    'high_price': open_price,
                    'low_price': open_price,
                    'volume': 0,
                    'amount': 0,
                    'change_rate': 0,
                }
            )

    return rows


def insert_quote(code, quote):
    rows = prepare_quote_rows(code, quote)
    if not rows:
        logging.info(f'{code} 无可写入行情数据')
        return

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
    try:
        with engine.begin() as conn:
            conn.execute(sql, rows)
        logging.info(f'{code} 插入/更新 {len(rows)} 条行情记录')
    except Exception:
        logging.exception(f'{code} 插入行情数据失败')


def format_begin_time(begin):
    try:
        return pd.to_datetime(begin).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return str(begin)


def get_price(code, begin):
    quote = None
    try:
        quote = ak.stock_zh_a_hist_min_em(
            symbol=code,
            period='30',
            adjust='qfq',
            start_date=format_begin_time(begin),
        )
        if quote is None or quote.empty:
            logging.info(f'{code} 无新增行情数据')
            return
        insert_quote(code, quote)
    except Exception:
        logging.exception(f'{code} 获取数据异常, 数据: {quote}')


def run_price_tracking():
    logging.info('开始获取价格跟踪数据')
    stock_df = fetch_stock_list()
    if stock_df.empty:
        logging.info('stock_base 为空, 无需执行价格跟踪')
    else:
        codes = stock_df['stock_code'].tolist()
        last_times = fetch_last_times(codes)

        for code, begin in stock_df.itertuples(index=False):
            logging.info(f'开始获取 {code} 的数据')
            get_price(code, last_times.get(code, begin))
            logging.info(f'{code} 数据获取完成')

    logging.info('价格跟踪任务完成')


if __name__ == '__main__':
    run_price_tracking()
