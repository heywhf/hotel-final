from flask import Flask, request, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from database_setup import Settings
from extension import db

set_up = Blueprint('set_up', __name__)


# 获取和更新设置信息的 API
@set_up.route('/api/setup/settingInfo', methods=['GET', 'POST'])
def setting_info():
    if request.method == 'GET':
        setting = Settings.query.first()  # 获取第一个设置记录
        if setting:
            return jsonify({
                'status': setting.status,
                'temperatureUpper': setting.temperature_upper,
                'temperatureLower': setting.temperature_lower,
                'mode': setting.mode,
                'lowSpeedFee': setting.low_speed_fee,
                'midSpeedFee': setting.mid_speed_fee,
                'highSpeedFee': setting.high_speed_fee,
            }), 200
        else:
            return jsonify({'error': '设置信息不存在'}), 404

    elif request.method == 'POST':
        try:
            setting = Settings.query.get(1)  # 假设我们总是更新 id 为 1 的记录
            if not setting:
                return jsonify({'error': '设置信息不存在'}), 404

            request_data = request.get_json()

            if 'status' in request_data:
                setting.status = request_data['status']
            if 'temperatureUpper' in request_data:
                setting.temperature_upper = request_data['temperatureUpper']
            if 'temperatureLower' in request_data:
                setting.temperature_lower = request_data['temperatureLower']
            if 'mode' in request_data:
                setting.mode = request_data['mode']
            if 'lowSpeedFee' in request_data:
                setting.low_speed_fee = request_data['lowSpeedFee']
            if 'midSpeedFee' in request_data:
                setting.mid_speed_fee = request_data['midSpeedFee']
            if 'highSpeedFee' in request_data:
                setting.high_speed_fee = request_data['highSpeedFee']

            db.session.commit()

            return jsonify({
                'status': setting.status,
                'temperatureUpper': setting.temperature_upper,
                'temperatureLower': setting.temperature_lower,
                'mode': setting.mode,
                'lowSpeedFee': setting.low_speed_fee,
                'midSpeedFee': setting.mid_speed_fee,
                'highSpeedFee': setting.high_speed_fee
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 404
