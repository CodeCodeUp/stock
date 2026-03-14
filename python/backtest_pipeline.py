import argparse
from datetime import datetime

from backtest_runtime import record_job_log
from backtest_schema import ensure_backtest_schema
from runtime import get_logger
from stock_backtest_builder import run_backtest_build
from stock_daily_bar_sync import run_daily_bar_sync

logger = get_logger('backtest_pipeline')


def run_backtest_pipeline(run_mode: str = 'incremental') -> dict:
    started_at = datetime.now()
    ensure_backtest_schema()

    sync_result = {
        'stock_codes': [],
        'fetched_bar_count': 0,
        'failed_codes': [],
    }
    build_result = {
        'stock_codes': [],
        'event_count': 0,
        'metric_count': 0,
    }
    status = 'SUCCESS'
    error_message = None

    try:
        sync_result = run_daily_bar_sync(run_mode=run_mode)
        build_result = run_backtest_build(run_mode=run_mode, stock_codes=sync_result['stock_codes'])
        if sync_result['failed_codes']:
            status = 'PARTIAL'
            error_message = f"部分股票历史日线同步失败: {','.join(sync_result['failed_codes'][:10])}"
    except Exception as exception:
        status = 'FAILED'
        error_message = str(exception)
        logger.exception('回测流水线执行失败，模式=%s', run_mode)
        raise
    finally:
        finished_at = datetime.now()
        try:
            record_job_log(
                job_type='backtest_pipeline',
                run_mode=run_mode,
                status=status,
                affected_stock_count=len(build_result['stock_codes']),
                fetched_bar_count=sync_result['fetched_bar_count'],
                event_count=build_result['event_count'],
                metric_count=build_result['metric_count'],
                started_at=started_at,
                finished_at=finished_at,
                error_message=error_message,
            )
        except Exception:
            logger.exception('记录回测任务日志失败，模式=%s', run_mode)

    logger.info(
        '回测流水线执行完成，模式=%s，状态=%s，股票数=%s，事件数=%s，指标数=%s',
        run_mode,
        status,
        len(build_result['stock_codes']),
        build_result['event_count'],
        build_result['metric_count'],
    )
    return {
        'status': status,
        **sync_result,
        **build_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='执行增持事件回测流水线')
    parser.add_argument('--mode', choices=['incremental', 'full'], default='incremental')
    args = parser.parse_args()

    run_backtest_pipeline(run_mode=args.mode)


if __name__ == '__main__':
    main()
