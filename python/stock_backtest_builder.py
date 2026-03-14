import argparse
from bisect import bisect_right
import math

import pandas as pd
from sqlalchemy import text

from backtest_runtime import (
    BACKTEST_BUILD_BATCH_STOCKS,
    BACKTEST_CALC_VERSION,
    BACKTEST_EVENT_VERSION,
    BACKTEST_HORIZONS,
    build_in_clause,
    chunked,
    delete_existing_backtest_rows,
    resolve_target_stock_codes,
)
from backtest_schema import ensure_backtest_schema
from runtime import get_db_engine, get_env_int, get_logger

logger = get_logger('stock_backtest_builder')

DB_WRITE_BATCH_SIZE = max(get_env_int('DB_WRITE_BATCH_SIZE', 2000), 1)


def _empty_event_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            'stock_code',
            'stock_name',
            'signal_date',
            'event_scope',
            'increase_count',
            'increase_amount',
            'increase_ratio_sum',
            'increase_ratio_max',
            'changer_count',
            'changer_names',
            'position_tags',
            'has_same_day_decrease',
            'same_day_decrease_amount',
            'consecutive_increase_days',
            'signal_score',
            'event_version',
        ]
    )


def _empty_bar_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            'stock_code',
            'trade_date',
            'open_price',
            'close_price',
            'high_price',
            'low_price',
        ]
    )


def _load_raw_signal_events(stock_codes: list[str]) -> pd.DataFrame:
    if not stock_codes:
        return _empty_event_dataframe()

    placeholders, params = build_in_clause(stock_codes, 'stock_code')
    query = text(
        f"""
        SELECT
            d.stock_code AS stock_code,
            SUBSTRING_INDEX(
                GROUP_CONCAT(d.stock_name ORDER BY d.trade_date DESC SEPARATOR ','),
                ',',
                1
            ) AS stock_name,
            d.trade_date AS signal_date,
            'day' AS event_scope,
            SUM(CASE WHEN d.change_type = '增持' THEN 1 ELSE 0 END) AS increase_count,
            SUM(CASE WHEN d.change_type = '增持' THEN ABS(COALESCE(d.total_price, 0)) ELSE 0 END) AS increase_amount,
            SUM(CASE WHEN d.change_type = '增持' THEN COALESCE(d.change_ratio, 0) ELSE 0 END) AS increase_ratio_sum,
            MAX(CASE WHEN d.change_type = '增持' THEN COALESCE(d.change_ratio, 0) ELSE 0 END) AS increase_ratio_max,
            COUNT(DISTINCT CASE WHEN d.change_type = '增持' THEN NULLIF(d.changer_name, '') END) AS changer_count,
            GROUP_CONCAT(
                DISTINCT CASE WHEN d.change_type = '增持' THEN NULLIF(d.changer_name, '') END
                ORDER BY d.changer_name
                SEPARATOR ','
            ) AS changer_names,
            GROUP_CONCAT(
                DISTINCT CASE WHEN d.change_type = '增持' THEN NULLIF(d.changer_position, '') END
                ORDER BY d.changer_position
                SEPARATOR ','
            ) AS position_tags,
            MAX(CASE WHEN d.change_type = '减持' THEN 1 ELSE 0 END) AS has_same_day_decrease,
            SUM(CASE WHEN d.change_type = '减持' THEN ABS(COALESCE(d.total_price, 0)) ELSE 0 END) AS same_day_decrease_amount
        FROM daily_stock_change d
        WHERE d.stock_code IN ({placeholders})
        GROUP BY d.stock_code, d.trade_date
        HAVING SUM(CASE WHEN d.change_type = '增持' THEN 1 ELSE 0 END) > 0
        ORDER BY d.stock_code, d.trade_date
        """
    )

    engine = get_db_engine()
    with engine.connect() as conn:
        dataframe = pd.read_sql(query, conn, params=params)

    if dataframe.empty:
        return _empty_event_dataframe()

    dataframe['signal_date'] = pd.to_datetime(dataframe['signal_date'], errors='coerce').dt.date
    dataframe['increase_count'] = pd.to_numeric(dataframe['increase_count'], errors='coerce').fillna(0).astype(int)
    dataframe['changer_count'] = pd.to_numeric(dataframe['changer_count'], errors='coerce').fillna(0).astype(int)
    dataframe['has_same_day_decrease'] = (
        pd.to_numeric(dataframe['has_same_day_decrease'], errors='coerce').fillna(0).astype(int)
    )

    for column in ['increase_amount', 'increase_ratio_sum', 'increase_ratio_max', 'same_day_decrease_amount']:
        dataframe[column] = pd.to_numeric(dataframe[column], errors='coerce').fillna(0.0)

    return dataframe


def _load_daily_bars(stock_codes: list[str]) -> pd.DataFrame:
    if not stock_codes:
        return _empty_bar_dataframe()

    placeholders, params = build_in_clause(stock_codes, 'stock_code')
    query = text(
        f"""
        SELECT
            stock_code,
            trade_date,
            open_price,
            close_price,
            high_price,
            low_price
        FROM stock_daily_bar
        WHERE stock_code IN ({placeholders})
        ORDER BY stock_code, trade_date
        """
    )

    engine = get_db_engine()
    with engine.connect() as conn:
        dataframe = pd.read_sql(query, conn, params=params)

    if dataframe.empty:
        return _empty_bar_dataframe()

    dataframe['trade_date'] = pd.to_datetime(dataframe['trade_date'], errors='coerce').dt.date
    for column in ['open_price', 'close_price', 'high_price', 'low_price']:
        dataframe[column] = pd.to_numeric(dataframe[column], errors='coerce')

    return dataframe.dropna(subset=['trade_date', 'open_price', 'close_price', 'high_price', 'low_price'])


def _score_amount(value: float) -> int:
    if value >= 50_000_000:
        return 25
    if value >= 10_000_000:
        return 20
    if value >= 5_000_000:
        return 16
    if value >= 1_000_000:
        return 10
    if value >= 300_000:
        return 6
    if value >= 100_000:
        return 4
    return 2


def _score_ratio(value: float) -> int:
    if value >= 0.01:
        return 20
    if value >= 0.005:
        return 16
    if value >= 0.002:
        return 12
    if value >= 0.001:
        return 8
    if value >= 0.0003:
        return 4
    return 1


def _score_changer_count(value: int) -> int:
    if value >= 4:
        return 15
    if value == 3:
        return 12
    if value == 2:
        return 9
    if value == 1:
        return 4
    return 0


def _score_position_tags(tags: str | None) -> int:
    if not tags:
        return 2

    normalized = tags.strip()
    if any(keyword in normalized for keyword in ['董事长', '实际控制人', '实控人']):
        return 15
    if any(keyword in normalized for keyword in ['总经理', '总裁', '首席执行官']):
        return 13
    if '董事' in normalized:
        return 11
    if any(keyword in normalized for keyword in ['高管', '高级管理人员', '副总经理', '董秘']):
        return 9
    if any(keyword in normalized for keyword in ['监事', '核心技术人员']):
        return 6
    return 3


def _score_consecutive_days(value: int) -> int:
    if value >= 4:
        return 15
    if value == 3:
        return 12
    if value == 2:
        return 8
    return 4


def _same_day_decrease_penalty(has_same_day_decrease: int, same_day_decrease_amount: float) -> int:
    if not has_same_day_decrease:
        return 0
    if same_day_decrease_amount >= 10_000_000:
        return 10
    if same_day_decrease_amount >= 1_000_000:
        return 8
    if same_day_decrease_amount >= 300_000:
        return 6
    return 4


def _clip_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def _safe_number(value: float | int | None) -> float | None:
    if value is None:
      return None
    if isinstance(value, bool):
      return float(value)
    numeric_value = float(value)
    if math.isnan(numeric_value) or math.isinf(numeric_value):
      return None
    return numeric_value


def _compute_consecutive_days(raw_events: pd.DataFrame, daily_bars: pd.DataFrame) -> pd.Series:
    if raw_events.empty:
        return pd.Series(dtype='int64')

    result = pd.Series(index=raw_events.index, dtype='int64')

    for stock_code, event_group in raw_events.groupby('stock_code', sort=False):
        stock_bars = daily_bars[daily_bars['stock_code'] == stock_code]
        trade_index_map = {
            trade_date: index
            for index, trade_date in enumerate(stock_bars['trade_date'].tolist())
        }

        sorted_group = event_group.sort_values('signal_date')
        previous_index = None
        streak = 0

        for row_index, event_row in sorted_group.iterrows():
            current_index = trade_index_map.get(event_row['signal_date'])
            if current_index is not None and previous_index is not None and current_index == previous_index + 1:
                streak += 1
            else:
                streak = 1

            result.loc[row_index] = streak
            previous_index = current_index

    return result.fillna(1).astype(int)


def _prepare_signal_events(raw_events: pd.DataFrame, daily_bars: pd.DataFrame) -> pd.DataFrame:
    if raw_events.empty:
        return _empty_event_dataframe()

    prepared = raw_events.copy()
    prepared['consecutive_increase_days'] = _compute_consecutive_days(prepared, daily_bars)
    prepared['signal_score'] = prepared.apply(
        lambda row: _clip_score(
            _score_amount(float(row['increase_amount']))
            + _score_ratio(float(row['increase_ratio_max']))
            + _score_changer_count(int(row['changer_count']))
            + _score_position_tags(row['position_tags'])
            + _score_consecutive_days(int(row['consecutive_increase_days']))
            - _same_day_decrease_penalty(int(row['has_same_day_decrease']), float(row['same_day_decrease_amount']))
        ),
        axis=1,
    )
    prepared['event_version'] = BACKTEST_EVENT_VERSION

    return prepared[
        [
            'stock_code',
            'stock_name',
            'signal_date',
            'event_scope',
            'increase_count',
            'increase_amount',
            'increase_ratio_sum',
            'increase_ratio_max',
            'changer_count',
            'changer_names',
            'position_tags',
            'has_same_day_decrease',
            'same_day_decrease_amount',
            'consecutive_increase_days',
            'signal_score',
            'event_version',
        ]
    ].copy()


def _insert_signal_events(events: pd.DataFrame, conn=None) -> None:
    if events.empty:
        return

    query = text(
        """
        INSERT INTO stock_signal_event (
            stock_code,
            stock_name,
            signal_date,
            event_scope,
            increase_count,
            increase_amount,
            increase_ratio_sum,
            increase_ratio_max,
            changer_count,
            changer_names,
            position_tags,
            has_same_day_decrease,
            same_day_decrease_amount,
            consecutive_increase_days,
            signal_score,
            event_version
        ) VALUES (
            :stock_code,
            :stock_name,
            :signal_date,
            :event_scope,
            :increase_count,
            :increase_amount,
            :increase_ratio_sum,
            :increase_ratio_max,
            :changer_count,
            :changer_names,
            :position_tags,
            :has_same_day_decrease,
            :same_day_decrease_amount,
            :consecutive_increase_days,
            :signal_score,
            :event_version
        )
        """
    )

    records = events.to_dict(orient='records')
    if conn is not None:
        for batch in chunked(records, DB_WRITE_BATCH_SIZE):
            conn.execute(query, batch)
    else:
        engine = get_db_engine()
        with engine.begin() as auto_conn:
            for batch in chunked(records, DB_WRITE_BATCH_SIZE):
                auto_conn.execute(query, batch)


def _load_persisted_events(stock_codes: list[str], conn=None) -> pd.DataFrame:
    if not stock_codes:
        return pd.DataFrame(columns=['event_id', 'stock_code', 'stock_name', 'signal_date', 'signal_score'])

    placeholders, params = build_in_clause(stock_codes, 'stock_code')
    query = text(
        f"""
        SELECT
            event_id,
            stock_code,
            stock_name,
            signal_date,
            signal_score
        FROM stock_signal_event
        WHERE stock_code IN ({placeholders})
        """
    )

    if conn is not None:
        dataframe = pd.read_sql(query, conn, params=params)
    else:
        engine = get_db_engine()
        with engine.connect() as auto_conn:
            dataframe = pd.read_sql(query, auto_conn, params=params)

    if dataframe.empty:
        return dataframe

    dataframe['signal_date'] = pd.to_datetime(dataframe['signal_date'], errors='coerce').dt.date
    dataframe['signal_score'] = pd.to_numeric(dataframe['signal_score'], errors='coerce').fillna(0).astype(int)
    return dataframe


def _build_metric_rows(events: pd.DataFrame, daily_bars: pd.DataFrame) -> list[dict]:
    if events.empty or daily_bars.empty:
        return []

    metric_rows: list[dict] = []

    for stock_code, event_group in events.groupby('stock_code', sort=False):
        stock_bars = daily_bars[daily_bars['stock_code'] == stock_code].sort_values('trade_date').reset_index(drop=True)
        if stock_bars.empty:
            continue

        trade_dates = stock_bars['trade_date'].tolist()

        for _, event_row in event_group.sort_values('signal_date').iterrows():
            entry_index = bisect_right(trade_dates, event_row['signal_date'])
            if entry_index >= len(stock_bars):
                continue

            entry_row = stock_bars.iloc[entry_index]
            entry_price = float(entry_row['open_price'])
            if entry_price <= 0:
                continue

            for horizon in BACKTEST_HORIZONS:
                exit_index = entry_index + horizon - 1
                if exit_index >= len(stock_bars):
                    continue

                window = stock_bars.iloc[entry_index : exit_index + 1]
                exit_row = stock_bars.iloc[exit_index]
                exit_price = float(exit_row['close_price'])
                max_return_pct = float(window['high_price'].max() / entry_price - 1)
                max_drawdown_pct = float(window['low_price'].min() / entry_price - 1)
                return_pct = float(exit_price / entry_price - 1)
                close_returns = window['close_price'].pct_change().dropna()
                volatility_pct = float(close_returns.std(ddof=0)) if not close_returns.empty else 0.0

                metric_rows.append(
                    {
                        'event_id': int(event_row['event_id']),
                        'horizon_days': int(horizon),
                        'entry_date': entry_row['trade_date'],
                        'entry_price': entry_price,
                        'entry_price_type': 'next_open',
                        'exit_date': exit_row['trade_date'],
                        'exit_price': exit_price,
                        'return_pct': _safe_number(return_pct) or 0.0,
                        'max_return_pct': _safe_number(max_return_pct) or 0.0,
                        'max_drawdown_pct': _safe_number(max_drawdown_pct) or 0.0,
                        'volatility_pct': _safe_number(volatility_pct),
                        'hit_3pct_flag': int(max_return_pct >= 0.03),
                        'hit_5pct_flag': int(max_return_pct >= 0.05),
                        'hit_10pct_flag': int(max_return_pct >= 0.10),
                        'is_positive_flag': int(return_pct > 0),
                        'bars_count': int(len(window)),
                        'calc_version': BACKTEST_CALC_VERSION,
                    }
                )

    return metric_rows


def _insert_metrics(metric_rows: list[dict], conn=None) -> None:
    if not metric_rows:
        return

    query = text(
        """
        INSERT INTO stock_backtest_metric (
            event_id,
            horizon_days,
            entry_date,
            entry_price,
            entry_price_type,
            exit_date,
            exit_price,
            return_pct,
            max_return_pct,
            max_drawdown_pct,
            volatility_pct,
            hit_3pct_flag,
            hit_5pct_flag,
            hit_10pct_flag,
            is_positive_flag,
            bars_count,
            calc_version
        ) VALUES (
            :event_id,
            :horizon_days,
            :entry_date,
            :entry_price,
            :entry_price_type,
            :exit_date,
            :exit_price,
            :return_pct,
            :max_return_pct,
            :max_drawdown_pct,
            :volatility_pct,
            :hit_3pct_flag,
            :hit_5pct_flag,
            :hit_10pct_flag,
            :is_positive_flag,
            :bars_count,
            :calc_version
        )
        """
    )

    if conn is not None:
        for batch in chunked(metric_rows, DB_WRITE_BATCH_SIZE):
            conn.execute(query, batch)
    else:
        engine = get_db_engine()
        with engine.begin() as auto_conn:
            for batch in chunked(metric_rows, DB_WRITE_BATCH_SIZE):
                auto_conn.execute(query, batch)


def _scale(value: float | None, lower: float, upper: float) -> float:
    if value is None or pd.isna(value):
        return 0.0
    if value <= lower:
        return 0.0
    if value >= upper:
        return 1.0
    return float((value - lower) / (upper - lower))


def _scale_inverse(value: float | None, lower: float, upper: float) -> float:
    return 1.0 - _scale(value, lower, upper)


def _build_summary_rows(events: pd.DataFrame, metric_rows: list[dict]) -> list[dict]:
    if events.empty:
        return []

    event_counts = (
        events.groupby('stock_code')
        .agg(stock_name=('stock_name', 'last'), sample_event_count=('event_id', 'count'), last_event_date=('signal_date', 'max'))
        .reset_index()
    )

    metrics_df = pd.DataFrame(metric_rows)
    if metrics_df.empty:
        return [
            {
                'stock_code': row['stock_code'],
                'stock_name': row['stock_name'],
                'sample_event_count': int(row['sample_event_count']),
                'win_rate_5d': None,
                'win_rate_10d': None,
                'win_rate_20d': None,
                'avg_return_5d': None,
                'avg_return_10d': None,
                'avg_return_20d': None,
                'median_return_20d': None,
                'avg_max_drawdown_20d': None,
                'hit_5pct_rate_20d': None,
                'hit_10pct_rate_60d': None,
                'historical_response_score': 0,
                'backtest_score': 0,
                'last_event_date': row['last_event_date'],
            }
            for _, row in event_counts.iterrows()
        ]

    metrics_with_code = metrics_df.merge(events[['event_id', 'stock_code']], on='event_id', how='left')
    summary_rows: list[dict] = []

    for _, event_count_row in event_counts.iterrows():
        stock_code = event_count_row['stock_code']
        stock_metrics = metrics_with_code[metrics_with_code['stock_code'] == stock_code]

        def get_metric_value(horizon: int, column: str, agg: str):
            horizon_metrics = stock_metrics[stock_metrics['horizon_days'] == horizon]
            if horizon_metrics.empty:
                return None
            series = pd.to_numeric(horizon_metrics[column], errors='coerce').dropna()
            if series.empty:
                return None
            if agg == 'mean':
                return float(series.mean())
            if agg == 'median':
                return float(series.median())
            raise ValueError(f'不支持的聚合: {agg}')

        win_rate_5d = get_metric_value(5, 'is_positive_flag', 'mean')
        win_rate_10d = get_metric_value(10, 'is_positive_flag', 'mean')
        win_rate_20d = get_metric_value(20, 'is_positive_flag', 'mean')
        avg_return_5d = get_metric_value(5, 'return_pct', 'mean')
        avg_return_10d = get_metric_value(10, 'return_pct', 'mean')
        avg_return_20d = get_metric_value(20, 'return_pct', 'mean')
        median_return_20d = get_metric_value(20, 'return_pct', 'median')
        avg_max_drawdown_20d = get_metric_value(20, 'max_drawdown_pct', 'mean')
        hit_5pct_rate_20d = get_metric_value(20, 'hit_5pct_flag', 'mean')
        hit_10pct_rate_60d = get_metric_value(60, 'hit_10pct_flag', 'mean')

        historical_response_score = _clip_score(
            _scale(win_rate_20d, 0.35, 0.75) * 35
            + _scale(avg_return_20d, -0.02, 0.12) * 20
            + _scale(median_return_20d, -0.02, 0.10) * 15
            + _scale_inverse(abs(avg_max_drawdown_20d) if avg_max_drawdown_20d is not None else None, 0.03, 0.18) * 15
            + _scale(hit_10pct_rate_60d, 0.05, 0.45) * 15
        )

        sample_bonus = _scale(float(event_count_row['sample_event_count']), 3, 20) * 10
        backtest_score = _clip_score(historical_response_score * 0.9 + sample_bonus)

        summary_rows.append(
            {
                'stock_code': stock_code,
                'stock_name': event_count_row['stock_name'],
                'sample_event_count': int(event_count_row['sample_event_count']),
                'win_rate_5d': _safe_number(win_rate_5d),
                'win_rate_10d': _safe_number(win_rate_10d),
                'win_rate_20d': _safe_number(win_rate_20d),
                'avg_return_5d': _safe_number(avg_return_5d),
                'avg_return_10d': _safe_number(avg_return_10d),
                'avg_return_20d': _safe_number(avg_return_20d),
                'median_return_20d': _safe_number(median_return_20d),
                'avg_max_drawdown_20d': _safe_number(avg_max_drawdown_20d),
                'hit_5pct_rate_20d': _safe_number(hit_5pct_rate_20d),
                'hit_10pct_rate_60d': _safe_number(hit_10pct_rate_60d),
                'historical_response_score': historical_response_score,
                'backtest_score': backtest_score,
                'last_event_date': event_count_row['last_event_date'],
            }
        )

    return summary_rows


def _insert_summaries(summary_rows: list[dict], conn=None) -> None:
    if not summary_rows:
        return

    query = text(
        """
        INSERT INTO stock_backtest_summary (
            stock_code,
            stock_name,
            sample_event_count,
            win_rate_5d,
            win_rate_10d,
            win_rate_20d,
            avg_return_5d,
            avg_return_10d,
            avg_return_20d,
            median_return_20d,
            avg_max_drawdown_20d,
            hit_5pct_rate_20d,
            hit_10pct_rate_60d,
            historical_response_score,
            backtest_score,
            last_event_date
        ) VALUES (
            :stock_code,
            :stock_name,
            :sample_event_count,
            :win_rate_5d,
            :win_rate_10d,
            :win_rate_20d,
            :avg_return_5d,
            :avg_return_10d,
            :avg_return_20d,
            :median_return_20d,
            :avg_max_drawdown_20d,
            :hit_5pct_rate_20d,
            :hit_10pct_rate_60d,
            :historical_response_score,
            :backtest_score,
            :last_event_date
        )
        """
    )

    if conn is not None:
        for batch in chunked(summary_rows, DB_WRITE_BATCH_SIZE):
            conn.execute(query, batch)
    else:
        engine = get_db_engine()
        with engine.begin() as auto_conn:
            for batch in chunked(summary_rows, DB_WRITE_BATCH_SIZE):
                auto_conn.execute(query, batch)


def run_backtest_build(run_mode: str = 'incremental', stock_codes: list[str] | None = None) -> dict:
    ensure_backtest_schema()

    target_stock_codes = stock_codes or resolve_target_stock_codes(run_mode)
    if not target_stock_codes:
        logger.info('当前没有需要重建回测结果的股票，模式=%s', run_mode)
        return {
            'stock_codes': [],
            'event_count': 0,
            'metric_count': 0,
        }

    total_event_count = 0
    total_metric_count = 0

    for batch_index, stock_code_batch in enumerate(chunked(target_stock_codes, BACKTEST_BUILD_BATCH_STOCKS), start=1):
        raw_events = _load_raw_signal_events(stock_code_batch)
        daily_bars = _load_daily_bars(stock_code_batch)
        prepared_events = _prepare_signal_events(raw_events, daily_bars)

        engine = get_db_engine()
        with engine.begin() as conn:
            delete_existing_backtest_rows(stock_code_batch, conn=conn)
            _insert_signal_events(prepared_events, conn=conn)
            persisted_events = _load_persisted_events(stock_code_batch, conn=conn)
            metric_rows = _build_metric_rows(persisted_events, daily_bars)
            _insert_metrics(metric_rows, conn=conn)
            summary_rows = _build_summary_rows(persisted_events, metric_rows)
            _insert_summaries(summary_rows, conn=conn)

        total_event_count += len(persisted_events)
        total_metric_count += len(metric_rows)
        logger.info(
            '回测批次完成，模式=%s，批次=%s，股票数=%s，事件数=%s，指标数=%s',
            run_mode,
            batch_index,
            len(stock_code_batch),
            len(persisted_events),
            len(metric_rows),
        )

    logger.info(
        '回测构建完成，模式=%s，股票数=%s，事件数=%s，指标数=%s',
        run_mode,
        len(target_stock_codes),
        total_event_count,
        total_metric_count,
    )
    return {
        'stock_codes': target_stock_codes,
        'event_count': total_event_count,
        'metric_count': total_metric_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='构建增持事件回测结果')
    parser.add_argument('--mode', choices=['incremental', 'full'], default='incremental')
    args = parser.parse_args()

    run_backtest_build(run_mode=args.mode)


if __name__ == '__main__':
    main()
