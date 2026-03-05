import os
import atexit

import akshare as ak
from flask import Flask, jsonify, request

from scheduler import start_background_scheduler

app = Flask(__name__)
embedded_scheduler = None


@app.route('/stock_hold_management', methods=['GET'])
def get_stock_hold_management():
    code = request.args.get('code')
    name = request.args.get('name')

    if not code or not name:
        return jsonify({'error': 'Missing required parameters: code and name'}), 400

    try:
        data = ak.stock_hold_management_person_em(code, name)
        return jsonify(data.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stock_hist_day', methods=['GET'])
def get_stock_hist_day():
    code = request.args.get('code')
    begin = request.args.get('begin')
    period = request.args.get('period', 'daily')

    if not code or not begin:
        return jsonify({'error': 'Missing required parameters: code and begin'}), 400

    try:
        quote = ak.stock_zh_a_hist(symbol=code, period=period, start_date=begin)
        return jsonify(quote.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    host = os.getenv('DATA_API_HOST', '0.0.0.0')
    port = int(os.getenv('DATA_API_PORT', '5000'))

    if os.getenv('ENABLE_SCHEDULER', 'true').lower() == 'true':
        try:
            embedded_scheduler = start_background_scheduler()
            atexit.register(lambda: embedded_scheduler.shutdown(wait=False))
        except Exception:
            app.logger.exception('定时器启动失败，继续仅以 API 模式运行')

    app.run(host=host, port=port)
