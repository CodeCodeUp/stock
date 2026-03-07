from datetime import date, datetime, timedelta

import akshare as ak
import pandas as pd
from sqlalchemy import text

from runtime import dataframe_to_records, get_db_engine, get_env_int, get_logger

logger = get_logger('stock_change_importer')

IMPORT_LOOKBACK_DAYS = max(get_env_int('IMPORT_LOOKBACK_DAYS', 7), 0)
DB_WRITE_BATCH_SIZE = max(get_env_int('DB_WRITE_BATCH_SIZE', 2000), 1)
MIN_TRADE_DATE = date(2000, 1, 1)


def get_latest_trade_date():
    engine = get_db_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT IFNULL(MAX(trade_date), '2000-01-01') FROM daily_stock_change"))
        return result.scalar()


def get_sync_start_date():
    latest_date = get_latest_trade_date()
    if isinstance(latest_date, str):
        latest_date = datetime.strptime(latest_date, '%Y-%m-%d').date()
    if latest_date is None:
        return MIN_TRADE_DATE
    return max(MIN_TRADE_DATE, latest_date - timedelta(days=IMPORT_LOOKBACK_DAYS))


def fetch_incremental_data(sync_start_date):
    logger.info('开始拉取增减持明细，回看天数=%s，起始日期=%s', IMPORT_LOOKBACK_DAYS, sync_start_date)
    data = ak.stock_hold_management_detail_em()
    data = data.rename(
        columns={
            '日期': 'trade_date',
            '代码': 'stock_code',
            '名称': 'stock_name',
            '变动人': 'changer_name',
            '职务': 'changer_position',
            '变动股数': 'change_shares',
            '成交均价': 'price',
            '变动金额': 'total_price',
            '变动后持股数': 'after_shares',
            '变动比例': 'change_ratio',
            '变动原因': 'change_reason',
        }
    )

    data['trade_date'] = pd.to_datetime(data['trade_date'], errors='coerce').dt.date
    data = data[data['trade_date'].notna()]
    filtered = data[data['trade_date'] >= sync_start_date]
    logger.info('增减持原始记录=%s，过滤后记录=%s', len(data), len(filtered))
    return filtered


def parse_change_type(share: float) -> str:
    return '减持' if share < 0 else '增持'


def normalize_data(df):
    logger.info('开始规范化增减持数据')
    normalized = df.copy()
    normalized['change_type'] = normalized['change_shares'].apply(parse_change_type)
    normalized['change_shares'] = normalized['change_shares'].abs()
    normalized['price'] = normalized['price'].fillna(0)
    normalized['total_price'] = normalized['total_price'].fillna(0)
    normalized['after_shares'] = normalized['after_shares'].fillna(0)
    normalized['change_ratio'] = normalized['change_ratio'].apply(
        lambda value: round(value / 100, 6) if pd.notna(value) else None
    )

    final_df = normalized[
        [
            'trade_date',
            'stock_code',
            'stock_name',
            'change_type',
            'changer_name',
            'changer_position',
            'change_shares',
            'price',
            'total_price',
            'after_shares',
            'change_ratio',
            'change_reason',
        ]
    ]

    return dataframe_to_records(final_df)


def insert_rows(conn, rows: list[dict]):
    if not rows:
        logger.info('没有需要写入的增减持记录')
        return

    insert_stmt = text(
        """
        INSERT INTO daily_stock_change (
            trade_date, stock_code, stock_name, change_type, changer_name,
            changer_position, change_shares, price, total_price, after_shares,
            change_ratio, change_reason
        )
        VALUES (
            :trade_date, :stock_code, :stock_name, :change_type, :changer_name,
            :changer_position, :change_shares, :price, :total_price, :after_shares,
            :change_ratio, :change_reason
        )
        ON DUPLICATE KEY UPDATE
            stock_name = VALUES(stock_name),
            changer_name = VALUES(changer_name),
            changer_position = VALUES(changer_position),
            change_shares = VALUES(change_shares),
            price = VALUES(price),
            total_price = VALUES(total_price),
            after_shares = VALUES(after_shares),
            change_ratio = VALUES(change_ratio),
            change_reason = VALUES(change_reason),
            update_time = CURRENT_TIMESTAMP
        """
    )

    for start in range(0, len(rows), DB_WRITE_BATCH_SIZE):
        batch = rows[start : start + DB_WRITE_BATCH_SIZE]
        conn.execute(insert_stmt, batch)

    logger.info('增减持写入完成，总记录=%s，批次大小=%s', len(rows), DB_WRITE_BATCH_SIZE)


def refresh_stock_base(conn):
    logger.info('开始刷新 stock_base 派生数据')
    result = conn.execute(
        text(
            """
            SELECT
                stock_code,
                SUBSTRING_INDEX(GROUP_CONCAT(stock_name ORDER BY trade_date DESC SEPARATOR ','), ',', 1) AS stock_name,
                MIN(trade_date) AS begin_time
            FROM daily_stock_change
            GROUP BY stock_code
            """
        )
    )
    rows = [dict(row._mapping) for row in result.fetchall()]

    if not rows:
        logger.info('daily_stock_change 为空，跳过刷新 stock_base')
        return

    upsert_stmt = text(
        """
        INSERT INTO stock_base (stock_code, stock_name, begin_time)
        VALUES (:stock_code, :stock_name, :begin_time)
        ON DUPLICATE KEY UPDATE
            stock_name = VALUES(stock_name),
            begin_time = VALUES(begin_time)
        """
    )

    for start in range(0, len(rows), DB_WRITE_BATCH_SIZE):
        batch = rows[start : start + DB_WRITE_BATCH_SIZE]
        conn.execute(upsert_stmt, batch)

    logger.info('stock_base 刷新完成，总股票数=%s', len(rows))


def run_importer():
    logger.info('=== 增减持导入任务开始 ===')
    sync_start_date = get_sync_start_date()
    df = fetch_incremental_data(sync_start_date)
    if df.empty:
        logger.info('回看窗口内没有新增或修正数据')
        logger.info('=== 增减持导入任务结束 ===')
        return

    records = normalize_data(df)
    engine = get_db_engine()
    try:
        with engine.begin() as conn:
            insert_rows(conn, records)
            refresh_stock_base(conn)
    except Exception:
        logger.exception('增减持导入任务失败')
        raise

    logger.info('=== 增减持导入任务结束，写入记录=%s ===', len(records))


if __name__ == '__main__':
    run_importer()
