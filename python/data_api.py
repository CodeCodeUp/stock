import atexit
import os
import threading
import time
from urllib.parse import unquote

import akshare as ak
import requests
from flask import Flask, jsonify, request

from backtest_pipeline import run_backtest_pipeline
from runtime import dataframe_to_records, get_env_int, get_logger, wait_for_rate_limit
from scheduler import start_background_scheduler

app = Flask(__name__)
embedded_scheduler = None
logger = get_logger('data_api')
AKSHARE_RETRY_TIMES = max(get_env_int('AKSHARE_RETRY_TIMES', 3), 1)
AKSHARE_RETRY_DELAY_SECONDS = max(get_env_int('AKSHARE_RETRY_DELAY_SECONDS', 1), 0)
EASTMONEY_KLINE_INTERVAL_SECONDS = max(get_env_int('EASTMONEY_KLINE_INTERVAL_SECONDS', 10), 0)
_BACKTEST_REBUILD_LOCK = threading.Lock()
_BACKTEST_REBUILD_STATUS = {
    'status': 'idle',
    'mode': None,
    'message': '暂无回测任务',
}


def call_akshare_with_retry(
    label: str,
    func,
    *args,
    rate_limit_key: str | None = None,
    rate_limit_seconds: int = 0,
    **kwargs,
):
    last_exception = None

    for attempt in range(1, AKSHARE_RETRY_TIMES + 1):
        try:
            if rate_limit_key:
                wait_for_rate_limit(rate_limit_key, rate_limit_seconds, logger=logger, label=label)
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as exception:
            last_exception = exception
            if attempt >= AKSHARE_RETRY_TIMES:
                break

            delay_seconds = AKSHARE_RETRY_DELAY_SECONDS * attempt
            logger.warning(
                '%s 第 %s 次请求失败，将在 %s 秒后重试',
                label,
                attempt,
                delay_seconds,
                exc_info=exception,
            )
            if delay_seconds > 0:
                time.sleep(delay_seconds)

    if last_exception is not None:
        raise last_exception

    raise RuntimeError(f'{label} 调用失败')


def error_response(message: str, status: int):
    return jsonify({'code': status, 'message': message, 'data': None}), status


def success_response(data, message: str = 'success'):
    return jsonify({'code': 0, 'message': message, 'data': data})


@app.route('/stock_hold_management', methods=['GET'])
def get_stock_hold_management():
    code = (request.args.get('code') or '').strip()
    name = unquote((request.args.get('name') or '').strip())

    if not code or not name:
        return error_response('缺少必填参数: code 和 name', 400)

    try:
        data = call_akshare_with_retry('获取增减持详情', ak.stock_hold_management_person_em, code, name)
        return jsonify(dataframe_to_records(data))
    except TypeError:
        logger.warning('增减持详情为空，返回空结果 code=%s name=%s', code, name)
        return jsonify([])
    except requests.exceptions.RequestException:
        logger.exception('获取增减持详情网络异常，降级为空结果 code=%s name=%s', code, name)
        return jsonify([])
    except Exception:
        logger.exception('获取增减持详情失败 code=%s name=%s', code, name)
        return error_response('获取增减持详情失败', 500)


@app.route('/stock_hist_day', methods=['GET'])
def get_stock_hist_day():
    code = (request.args.get('code') or '').strip()
    begin = (request.args.get('begin') or '').strip()
    period = (request.args.get('period') or 'daily').strip().lower()

    if not code or not begin:
        return error_response('缺少必填参数: code 和 begin', 400)

    if period not in {'daily', 'weekly', 'monthly'}:
        return error_response('period 仅支持 daily、weekly、monthly', 400)

    try:
        quote = call_akshare_with_retry(
            '获取历史行情',
            ak.stock_zh_a_hist,
            rate_limit_key='eastmoney-kline-daily',
            rate_limit_seconds=EASTMONEY_KLINE_INTERVAL_SECONDS,
            symbol=code,
            period=period,
            start_date=begin,
        )
        return jsonify(dataframe_to_records(quote))
    except requests.exceptions.RequestException:
        logger.exception('获取历史行情网络异常，降级为空结果 code=%s begin=%s period=%s', code, begin, period)
        return jsonify([])
    except Exception:
        logger.exception('获取历史行情失败 code=%s begin=%s period=%s', code, begin, period)
        return error_response('获取历史行情失败', 500)


def _run_backtest_rebuild(mode: str) -> None:
    try:
        _BACKTEST_REBUILD_STATUS.update(
            {
                'status': 'running',
                'mode': mode,
                'message': f'回测任务执行中: {mode}',
            }
        )
        run_backtest_pipeline(mode)
        _BACKTEST_REBUILD_STATUS.update(
            {
                'status': 'completed',
                'mode': mode,
                'message': f'回测任务执行完成: {mode}',
            }
        )
    except Exception:
        logger.exception('回测任务执行失败 mode=%s', mode)
        _BACKTEST_REBUILD_STATUS.update(
            {
                'status': 'failed',
                'mode': mode,
                'message': f'回测任务执行失败: {mode}',
            }
        )
    finally:
        _BACKTEST_REBUILD_LOCK.release()


@app.route('/backtest/rebuild', methods=['POST'])
def rebuild_backtest():
    mode = (request.args.get('mode') or request.form.get('mode') or 'incremental').strip().lower()
    if mode not in {'incremental', 'full'}:
        return error_response('mode 仅支持 incremental 或 full', 400)

    if not _BACKTEST_REBUILD_LOCK.acquire(blocking=False):
        return success_response(
            {
                'status': 'running',
                'mode': _BACKTEST_REBUILD_STATUS.get('mode'),
                'message': '已有回测任务在执行中',
            },
            message='accepted',
        )

    try:
        worker = threading.Thread(target=_run_backtest_rebuild, args=(mode,), daemon=True, name='backtest-rebuild')
        worker.start()
    except Exception:
        _BACKTEST_REBUILD_LOCK.release()
        logger.exception('回测后台线程启动失败 mode=%s', mode)
        return error_response('回测任务启动失败', 500)

    return success_response(
        {
            'status': 'accepted',
            'mode': mode,
            'message': '回测任务已提交到后台执行',
        },
        message='accepted',
    )


if __name__ == '__main__':
    host = os.getenv('DATA_API_HOST', '0.0.0.0')
    port = int(os.getenv('DATA_API_PORT', '5000'))

    if os.getenv('ENABLE_SCHEDULER', 'true').lower() == 'true':
        try:
            embedded_scheduler = start_background_scheduler()
            atexit.register(lambda: embedded_scheduler.shutdown(wait=False))
        except Exception:
            logger.exception('定时器启动失败，继续仅以 API 模式运行')

    logger.info('data-api 启动 host=%s port=%s', host, port)
    app.run(host=host, port=port)
