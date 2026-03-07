import os
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

import akshare as ak
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger

from runtime import get_logger
from stock_change_importer import run_importer
from stock_price_tracking import run_price_tracking

logger = get_logger('scheduler')

TIMEZONE = ZoneInfo(os.getenv('SCHEDULER_TIMEZONE', 'Asia/Shanghai'))
ENABLE_IMPORTER = os.getenv('ENABLE_IMPORTER', 'true').lower() == 'true'
ENABLE_PRICE_TRACKING = os.getenv('ENABLE_PRICE_TRACKING', 'true').lower() == 'true'

_TRADE_DAYS = set()
_TRADE_DAYS_REFRESHED_AT = None
_IMPORTER_LOCK = threading.Lock()
_PRICE_TRACKING_LOCK = threading.Lock()


def refresh_trade_days_if_needed():
    global _TRADE_DAYS_REFRESHED_AT

    today = datetime.now(TIMEZONE).date()
    if _TRADE_DAYS_REFRESHED_AT == today and _TRADE_DAYS:
        return

    try:
        trade_date_df = ak.tool_trade_date_hist_sina()
        trade_dates = pd.to_datetime(trade_date_df['trade_date'], errors='coerce').dt.date.dropna()
        _TRADE_DAYS.clear()
        _TRADE_DAYS.update(trade_dates.tolist())
        _TRADE_DAYS_REFRESHED_AT = today
    except Exception:
        logger.exception('刷新交易日历失败，回退到工作日判断')
        _TRADE_DAYS.clear()
        _TRADE_DAYS_REFRESHED_AT = today


def is_trading_day(current_time: datetime):
    refresh_trade_days_if_needed()
    if _TRADE_DAYS:
        return current_time.date() in _TRADE_DAYS
    return current_time.weekday() < 5


def run_locked_job(job_name, lock, job_func, trading_day_only=True):
    now = datetime.now(TIMEZONE)

    if trading_day_only and not is_trading_day(now):
        logger.info('[%s] 非交易日，跳过执行', job_name)
        return

    if not lock.acquire(blocking=False):
        logger.warning('[%s] 上一次任务未结束，跳过本次执行', job_name)
        return

    try:
        logger.info('[%s] 开始执行', job_name)
        job_func()
        logger.info('[%s] 执行完成', job_name)
    except Exception:
        logger.exception('[%s] 执行失败', job_name)
        raise
    finally:
        lock.release()


def register_jobs(scheduler: BaseScheduler):
    if ENABLE_PRICE_TRACKING:
        scheduler.add_job(
            lambda: run_locked_job('price-tracking', _PRICE_TRACKING_LOCK, run_price_tracking),
            CronTrigger(day_of_week='mon-fri', hour='9-11,13-14', minute='5,35', timezone=TIMEZONE),
            id='price_tracking_session',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )
        scheduler.add_job(
            lambda: run_locked_job('price-tracking-close', _PRICE_TRACKING_LOCK, run_price_tracking),
            CronTrigger(day_of_week='mon-fri', hour='15', minute='5', timezone=TIMEZONE),
            id='price_tracking_close',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )

    if ENABLE_IMPORTER:
        scheduler.add_job(
            lambda: run_locked_job('change-importer', _IMPORTER_LOCK, run_importer),
            CronTrigger(day_of_week='mon-fri', hour='18', minute='10', timezone=TIMEZONE),
            id='change_importer',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=600,
        )

    return scheduler


def create_scheduler(scheduler_cls=BlockingScheduler):
    scheduler = scheduler_cls(timezone=TIMEZONE)
    return register_jobs(scheduler)


def log_registered_jobs(scheduler: BaseScheduler):
    jobs = scheduler.get_jobs()
    if not jobs:
        logger.warning('未启用任何定时任务，请检查 ENABLE_IMPORTER / ENABLE_PRICE_TRACKING')
        return

    for job in jobs:
        try:
            next_run_time = job.next_run_time
        except AttributeError:
            next_run_time = 'pending'

        logger.info('已注册任务: id=%s next_run=%s', job.id, next_run_time)


def start_background_scheduler():
    scheduler = create_scheduler(BackgroundScheduler)
    scheduler.start()
    log_registered_jobs(scheduler)
    logger.info('内嵌调度器已启动，时区=%s', TIMEZONE)
    return scheduler


def start_blocking_scheduler():
    scheduler = create_scheduler(BlockingScheduler)
    log_registered_jobs(scheduler)
    logger.info('独立调度器启动，时区=%s', TIMEZONE)
    scheduler.start()


if __name__ == '__main__':
    start_blocking_scheduler()
