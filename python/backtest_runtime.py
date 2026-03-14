import os
from datetime import date, datetime, timedelta
from typing import Iterable

from sqlalchemy import text

from runtime import get_db_engine, get_env_int, get_logger

logger = get_logger('backtest_runtime')

BACKTEST_DAILY_LOOKBACK_DAYS = max(get_env_int('BACKTEST_DAILY_LOOKBACK_DAYS', 7), 1)
BACKTEST_BAR_SYNC_OVERLAP_DAYS = max(get_env_int('BACKTEST_BAR_SYNC_OVERLAP_DAYS', 10), 0)
BACKTEST_BUILD_BATCH_STOCKS = max(get_env_int('BACKTEST_BUILD_BATCH_STOCKS', 200), 1)
BACKTEST_EVENT_VERSION = max(get_env_int('BACKTEST_EVENT_VERSION', 1), 1)
BACKTEST_CALC_VERSION = max(get_env_int('BACKTEST_CALC_VERSION', 1), 1)


def parse_backtest_horizons() -> list[int]:
    raw_value = os.getenv('BACKTEST_HORIZONS', '5,10,20,60')
    parsed: list[int] = []

    for chunk in raw_value.split(','):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            value = int(chunk)
        except ValueError:
            logger.warning('忽略非法回测窗口配置: %s', chunk)
            continue
        if value > 0:
            parsed.append(value)

    return parsed or [5, 10, 20, 60]


BACKTEST_HORIZONS = parse_backtest_horizons()


def chunked(items: list, size: int) -> Iterable[list]:
    if size <= 0:
        raise ValueError('size 必须大于 0')

    for start in range(0, len(items), size):
        yield items[start : start + size]


def build_in_clause(values: list[str], prefix: str = 'value') -> tuple[str, dict]:
    placeholders = []
    params = {}

    for index, value in enumerate(values):
        key = f'{prefix}_{index}'
        placeholders.append(f':{key}')
        params[key] = value

    return ', '.join(placeholders), params


def get_incremental_stock_codes(lookback_days: int = BACKTEST_DAILY_LOOKBACK_DAYS) -> list[str]:
    engine = get_db_engine()
    query = text(
        """
        SELECT DISTINCT stock_code
        FROM daily_stock_change
        WHERE update_time >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL :lookbackDays DAY)
        ORDER BY stock_code
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {'lookbackDays': lookback_days}).fetchall()

    return [str(row[0]) for row in rows]


def get_all_signal_stock_codes() -> list[str]:
    engine = get_db_engine()
    query = text(
        """
        SELECT DISTINCT stock_code
        FROM daily_stock_change
        ORDER BY stock_code
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    return [str(row[0]) for row in rows]


def resolve_target_stock_codes(run_mode: str) -> list[str]:
    if run_mode == 'full':
        return get_all_signal_stock_codes()
    return get_incremental_stock_codes()


def get_event_start_dates(stock_codes: list[str]) -> dict[str, date]:
    if not stock_codes:
        return {}

    placeholders, params = build_in_clause(stock_codes, 'stock_code')
    query = text(
        f"""
        SELECT stock_code, MIN(trade_date) AS start_date
        FROM daily_stock_change
        WHERE stock_code IN ({placeholders})
        GROUP BY stock_code
        """
    )

    engine = get_db_engine()
    with engine.connect() as conn:
        rows = conn.execute(query, params).fetchall()

    return {
        str(row[0]): row[1]
        for row in rows
        if row[1] is not None
    }


def get_last_daily_bar_dates(stock_codes: list[str]) -> dict[str, date]:
    if not stock_codes:
        return {}

    placeholders, params = build_in_clause(stock_codes, 'stock_code')
    query = text(
        f"""
        SELECT stock_code, MAX(trade_date) AS last_trade_date
        FROM stock_daily_bar
        WHERE stock_code IN ({placeholders})
        GROUP BY stock_code
        """
    )

    engine = get_db_engine()
    with engine.connect() as conn:
        rows = conn.execute(query, params).fetchall()

    return {
        str(row[0]): row[1]
        for row in rows
        if row[1] is not None
    }


def resolve_sync_start_dates(stock_codes: list[str], run_mode: str) -> dict[str, date]:
    event_start_dates = get_event_start_dates(stock_codes)
    if run_mode == 'full':
        return event_start_dates

    last_trade_dates = get_last_daily_bar_dates(stock_codes)
    start_dates: dict[str, date] = {}

    for stock_code, event_start_date in event_start_dates.items():
        last_trade_date = last_trade_dates.get(stock_code)
        if last_trade_date is None:
            start_dates[stock_code] = event_start_date
            continue

        incremental_start = last_trade_date - timedelta(days=BACKTEST_BAR_SYNC_OVERLAP_DAYS)
        start_dates[stock_code] = max(event_start_date, incremental_start)

    return start_dates


def delete_existing_backtest_rows(stock_codes: list[str], conn=None) -> None:
    if not stock_codes:
        return

    engine = get_db_engine()

    for batch in chunked(stock_codes, 500):
        placeholders, params = build_in_clause(batch, 'stock_code')
        delete_metric_query = text(
            f"""
            DELETE metric
            FROM stock_backtest_metric metric
            INNER JOIN stock_signal_event event
                ON event.event_id = metric.event_id
            WHERE event.stock_code IN ({placeholders})
            """
        )
        delete_event_query = text(
            f"""
            DELETE FROM stock_signal_event
            WHERE stock_code IN ({placeholders})
            """
        )
        delete_summary_query = text(
            f"""
            DELETE FROM stock_backtest_summary
            WHERE stock_code IN ({placeholders})
            """
        )

        if conn is not None:
            conn.execute(delete_metric_query, params)
            conn.execute(delete_event_query, params)
            conn.execute(delete_summary_query, params)
        else:
            with engine.begin() as auto_conn:
                auto_conn.execute(delete_metric_query, params)
                auto_conn.execute(delete_event_query, params)
                auto_conn.execute(delete_summary_query, params)


def record_job_log(
    job_type: str,
    run_mode: str,
    status: str,
    affected_stock_count: int,
    fetched_bar_count: int,
    event_count: int,
    metric_count: int,
    started_at: datetime,
    finished_at: datetime,
    error_message: str | None = None,
) -> None:
    engine = get_db_engine()
    query = text(
        """
        INSERT INTO backtest_job_log (
            job_type,
            run_mode,
            run_date,
            status,
            affected_stock_count,
            fetched_bar_count,
            event_count,
            metric_count,
            error_message,
            started_at,
            finished_at
        ) VALUES (
            :jobType,
            :runMode,
            :runDate,
            :status,
            :affectedStockCount,
            :fetchedBarCount,
            :eventCount,
            :metricCount,
            :errorMessage,
            :startedAt,
            :finishedAt
        )
        """
    )

    with engine.begin() as conn:
        conn.execute(
            query,
            {
                'jobType': job_type,
                'runMode': run_mode,
                'runDate': date.today(),
                'status': status,
                'affectedStockCount': affected_stock_count,
                'fetchedBarCount': fetched_bar_count,
                'eventCount': event_count,
                'metricCount': metric_count,
                'errorMessage': error_message,
                'startedAt': started_at,
                'finishedAt': finished_at,
            },
        )
