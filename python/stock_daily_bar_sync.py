import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import akshare as ak
import pandas as pd
from sqlalchemy import text

from backtest_runtime import chunked, resolve_sync_start_dates, resolve_target_stock_codes
from backtest_schema import ensure_backtest_schema
from runtime import get_db_engine, get_env_int, get_logger, wait_for_rate_limit

logger = get_logger('stock_daily_bar_sync')

DAILY_BAR_RETRY_TIMES = max(get_env_int('BACKTEST_DAILY_BAR_RETRY_TIMES', 3), 1)
DAILY_BAR_RETRY_DELAY_SECONDS = max(get_env_int('BACKTEST_DAILY_BAR_RETRY_DELAY_SECONDS', 2), 0)
DAILY_BAR_BATCH_SIZE = max(get_env_int('DB_WRITE_BATCH_SIZE', 2000), 1)
DAILY_BAR_MAX_WORKERS = max(get_env_int('BACKTEST_DAILY_BAR_MAX_WORKERS', 4), 1)
DAILY_BAR_ADJUST = (os.getenv('BACKTEST_DAILY_BAR_ADJUST', 'qfq') or 'qfq').strip().lower()
DAILY_BAR_SOURCE = 'akshare_eastmoney'
EASTMONEY_KLINE_INTERVAL_SECONDS = max(get_env_int('EASTMONEY_KLINE_INTERVAL_SECONDS', 10), 0)


def _fetch_daily_quote(code: str, start_date: date) -> pd.DataFrame:
    last_exception = None
    start_date_text = start_date.strftime('%Y%m%d')

    for attempt in range(1, DAILY_BAR_RETRY_TIMES + 1):
        try:
            wait_for_rate_limit(
                'eastmoney-kline-daily',
                EASTMONEY_KLINE_INTERVAL_SECONDS,
                logger=logger,
                label='回测历史日线同步',
            )
            quote = ak.stock_zh_a_hist(
                symbol=code,
                period='daily',
                start_date=start_date_text,
                adjust=DAILY_BAR_ADJUST,
            )
            return quote if quote is not None else pd.DataFrame()
        except Exception as exception:
            last_exception = exception
            logger.exception('%s 第 %s 次同步日线失败', code, attempt)
            if attempt < DAILY_BAR_RETRY_TIMES and DAILY_BAR_RETRY_DELAY_SECONDS > 0:
                time.sleep(DAILY_BAR_RETRY_DELAY_SECONDS * attempt)

    if last_exception is not None:
        raise last_exception

    raise RuntimeError(f'{code} 历史日线同步失败')


def _to_float(value, default=None):
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_daily_quote(code: str, quote: pd.DataFrame) -> list[dict]:
    if quote is None or quote.empty:
        return []

    prepared = quote.copy()
    prepared.columns = [str(column).strip() for column in prepared.columns]
    required_columns = ['日期', '开盘', '收盘', '最高', '最低']
    missing_columns = [column for column in required_columns if column not in prepared.columns]
    if missing_columns:
        raise ValueError(f'{code} 历史日线缺少字段: {missing_columns}')

    prepared['日期'] = pd.to_datetime(prepared['日期'], errors='coerce').dt.date
    for column in ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅']:
        if column in prepared.columns:
            prepared[column] = pd.to_numeric(prepared[column], errors='coerce')

    prepared = prepared.dropna(subset=['日期', '开盘', '收盘', '最高', '最低']).copy()
    if prepared.empty:
        return []

    rows = []
    for _, row in prepared.iterrows():
        rows.append(
            {
                'stock_code': code,
                'trade_date': row['日期'],
                'open_price': _to_float(row['开盘']),
                'close_price': _to_float(row['收盘']),
                'high_price': _to_float(row['最高']),
                'low_price': _to_float(row['最低']),
                'volume': _to_float(row.get('成交量')),
                'amount': _to_float(row.get('成交额')),
                'change_rate': _to_float(row.get('涨跌幅')),
                'adjust_type': DAILY_BAR_ADJUST,
                'data_source': DAILY_BAR_SOURCE,
            }
        )

    return rows


def _upsert_daily_bars(rows: list[dict]) -> int:
    if not rows:
        return 0

    query = text(
        """
        INSERT INTO stock_daily_bar (
            stock_code,
            trade_date,
            open_price,
            close_price,
            high_price,
            low_price,
            volume,
            amount,
            change_rate,
            adjust_type,
            data_source
        ) VALUES (
            :stock_code,
            :trade_date,
            :open_price,
            :close_price,
            :high_price,
            :low_price,
            :volume,
            :amount,
            :change_rate,
            :adjust_type,
            :data_source
        ) ON DUPLICATE KEY UPDATE
            open_price = VALUES(open_price),
            close_price = VALUES(close_price),
            high_price = VALUES(high_price),
            low_price = VALUES(low_price),
            volume = VALUES(volume),
            amount = VALUES(amount),
            change_rate = VALUES(change_rate),
            adjust_type = VALUES(adjust_type),
            data_source = VALUES(data_source),
            updated_at = CURRENT_TIMESTAMP
        """
    )

    engine = get_db_engine()
    with engine.begin() as conn:
        for batch in chunked(rows, DAILY_BAR_BATCH_SIZE):
            conn.execute(query, batch)

    return len(rows)


def _sync_single_stock(stock_code: str, start_date: date) -> tuple[str, list[dict]]:
    quote = _fetch_daily_quote(stock_code, start_date)
    rows = _normalize_daily_quote(stock_code, quote)
    return stock_code, rows


def run_daily_bar_sync(run_mode: str = 'incremental', stock_codes: list[str] | None = None) -> dict:
    ensure_backtest_schema()

    target_stock_codes = stock_codes or resolve_target_stock_codes(run_mode)
    if not target_stock_codes:
        logger.info('当前没有需要同步的回测股票，模式=%s', run_mode)
        return {
            'stock_codes': [],
            'fetched_bar_count': 0,
            'failed_codes': [],
        }

    sync_start_dates = resolve_sync_start_dates(target_stock_codes, run_mode)
    fetched_bar_count = 0
    success_codes: list[str] = []
    failed_codes: list[str] = []

    valid_targets = [
        (stock_code, sync_start_dates[stock_code])
        for stock_code in target_stock_codes
        if sync_start_dates.get(stock_code) is not None
    ]

    missing_start_dates = [
        stock_code
        for stock_code in target_stock_codes
        if sync_start_dates.get(stock_code) is None
    ]
    for stock_code in missing_start_dates:
        logger.warning('%s 缺少增减持起始日期，跳过历史日线同步', stock_code)

    max_workers = min(DAILY_BAR_MAX_WORKERS, max(len(valid_targets), 1))
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='daily-bar-sync') as executor:
        futures = {
            executor.submit(_sync_single_stock, stock_code, start_date): (stock_code, start_date)
            for stock_code, start_date in valid_targets
        }

        for future in as_completed(futures):
            stock_code, start_date = futures[future]
            try:
                _, rows = future.result()
                fetched_bar_count += _upsert_daily_bars(rows)
                success_codes.append(stock_code)
                logger.info('%s 历史日线同步完成，起始日期=%s，写入记录=%s', stock_code, start_date, len(rows))
            except Exception:
                failed_codes.append(stock_code)
                logger.exception('%s 历史日线同步失败', stock_code)

    logger.info(
        '历史日线同步结束，模式=%s，目标股票=%s，并发=%s，成功=%s，失败=%s，写入记录=%s',
        run_mode,
        len(target_stock_codes),
        max_workers,
        len(success_codes),
        len(failed_codes),
        fetched_bar_count,
    )
    return {
        'stock_codes': success_codes,
        'fetched_bar_count': fetched_bar_count,
        'failed_codes': failed_codes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='同步回测历史日线')
    parser.add_argument('--mode', choices=['incremental', 'full'], default='incremental')
    args = parser.parse_args()

    run_daily_bar_sync(run_mode=args.mode)


if __name__ == '__main__':
    main()
