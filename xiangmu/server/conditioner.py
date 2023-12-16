from flask import Flask, request, jsonify, Blueprint
from log import  write_log
from datetime import datetime
from database_setup import Conditioner, User, Log, Settings
from extension import db

conditioner = Blueprint('conditioner', __name__)


@conditioner.route('/api/conditioners/get_ac_info/', methods=['GET'])
def get_ac_info():
    token = request.args.get('token')
    user = User.query.filter_by(name=token).first()
    if user:
        ac = Conditioner.query.filter_by(room_number=user.id).first()
        if ac:
            ac_info = {
                'roomNumber': user.name,  # 假设 User.name 是房间号
                'currentTemperature': ac.temperature_now,
                'targetTemperature': ac.temperature_set,
                'acStatus': ac.status,
                'acMode': ac.mode,
                'cost': ac.cost,
                'totalCost': ac.total_cost,
                'queueStatus': ac.queue_status,
            }
            return jsonify(ac_info), 200
        else:
            return jsonify({'error': '空调信息不存在'}), 404
    else:
        return jsonify({'error': '用户信息不存在'}), 404


@conditioner.route('/api/conditioners/update_ac_info/', methods=['POST'])
def update_ac_info():
    data = request.get_json()
    token = data.get('token')
    user = User.query.filter_by(name=token).first()

    if not user:
        return jsonify({'error': '用户信息不存在'}), 404

    ac = Conditioner.query.filter_by(room_number=user.id).first()
    if not ac:
        return jsonify({'error': '空调信息不存在'}), 404

    target_temperature = data.get('targetTemperature')
    ac_status = data.get('acStatus')
    ac_mode = data.get('acMode')

    # 写日志的函数（根据需要实现）
    def write_log(log_type, operator, ac, remark=''):
        log_entry = Log(type=log_type, time=datetime.now(), operator=operator, object_id=ac.id, remark=remark)
        db.session.add(log_entry)

    if ac.temperature_set != target_temperature:
        write_log('调温', '客户', ac, f'温度从{ac.temperature_set}°C调整到{target_temperature}°C')
        ac.temperature_set = target_temperature

    if ac.status != ac_status:
        write_log('开关机', '客户', ac, '关机' if ac_status else '开机')
        ac.status = ac_status

    if ac.mode != ac_mode:
        write_log('调风', '客户', ac, f'从{ac.mode}调整到{ac_mode}')
        ac.mode = ac_mode

    db.session.commit()

    return jsonify({
        'room_number': user.name,  # 假设 User.name 是房间号
        'currentTemperature': ac.temperature_now,
        'targetTemperature': ac.temperature_set,
        'acStatus': ac.status,
        'acMode': ac.mode,
        'cost': ac.cost,
        'totalCost': ac.total_cost,
    }), 200


@conditioner.route('/api/conditioners/get_all_ac_info/', methods=['POST'])
def get_all_ac_info():
    data = request.get_json()
    token = data.get('token')
    user = User.query.filter_by(name=token).first()

    if not user:
        return jsonify({'error': '用户信息不存在'}), 404

    acs = Conditioner.query.order_by(Conditioner.room_number).all()
    acs_info = []
    for ac in acs:
        acs_info.append({
            'roomNumber': ac.room_number,  # 假设 room_number 直接是房间号
            'currentTemperature': ac.temperature_now,
            'targetTemperature': ac.temperature_set,
            'acStatus': ac.status,
            'acMode': ac.mode,
            'cost': ac.cost,
            'totalCost': ac.total_cost,
            'queueStatus': ac.queue_status,
        })

    return jsonify({'acs_info': acs_info}), 200


@conditioner.route('/api/conditioners/admin_update_ac_info/', methods=['POST'])
def admin_update_ac_info():
    data = request.get_json()
    room_number = data.get('roomNumber')
    user = User.query.filter_by(name=room_number).first()

    if not user:
        return jsonify({'error': '用户信息不存在'}), 404

    ac = Conditioner.query.filter_by(room_number=user.id).first()
    if not ac:
        return jsonify({'error': '空调信息不存在'}), 404

    target_temperature = data.get('targetTemperature')
    ac_status = data.get('acStatus')
    ac_mode = data.get('acMode')

    # 写日志的函数（根据需要实现）
    def write_log(log_type, operator, ac, remark=''):
        log_entry = Log(type=log_type, time=datetime.now(), operator=operator, object_id=ac.id, remark=remark)
        db.session.add(log_entry)

    if ac.temperature_set != target_temperature:
        write_log('调温', '管理员', ac, f'温度从{ac.temperature_set}°C调整到{target_temperature}°C')
        ac.temperature_set = target_temperature

    if ac.status != ac_status:
        write_log('开关机', '管理员', ac, '关机' if ac_status else '开机')
        ac.status = ac_status

    if ac.mode != ac_mode:
        write_log('调风', '管理员', ac, f'从{ac.mode}调整到{ac_mode}')
        ac.mode = ac_mode

    db.session.commit()

    return jsonify({
        'room_number': user.name,  # 假设 User.name 是房间号
        'currentTemperature': ac.temperature_now,
        'targetTemperature': ac.temperature_set,
        'acStatus': ac.status,
        'acMode': ac.mode,
        'cost': ac.cost,
        'totalCost': ac.total_cost,
        'queueStatus': ac.queue_status,
    }), 200


@conditioner.route('/api/conditioners/reception_get_room_numbers/', methods=['GET'])
def reception_get_room_numbers():
    # 初始假设所有房间都是空闲的
    room_numbers = {conditioner.room_number: True for conditioner in Conditioner.query.all()}

    # 查找所有的入住和结算日志
    logs = Log.query.filter(Log.type.in_(['入住', '结算'])).all()
    for log in logs:
        if log.type == '入住':
            room_numbers[log.conditioner.room_number] = False  # 房间不空闲
        else:
            room_numbers[log.conditioner.room_number] = True  # 房间空闲

    return jsonify({'room_numbers': room_numbers}), 200


@conditioner.route('/api/conditioners/reception_register_for_customer/', methods=['POST'])
def reception_register_for_customer():
    data = request.get_json()
    password = data.get('password')
    room_number = data.get('room_number')

    # 检查房间是否空闲
    room_numbers = {conditioner.room_number: True for conditioner in Conditioner.query.all()}
    logs = Log.query.filter(Log.type.in_(['入住', '结算'])).all()
    for log in logs:
        if log.type == '入住':
            room_numbers[log.conditioner.room_number] = False
        else:
            room_numbers[log.conditioner.room_number] = True

    if not room_numbers.get(room_number, False):
        return jsonify({'error': '房间已被入住'}), 400

    # 注册新用户
    user = User.query.filter_by(name=room_number).first()
    if not user:
        user = User(name=room_number, password=password, identity='customer')
        db.session.add(user)
    else:
        user.password = password  # 更新密码

    # 写入入住日志
    def write_log(log_type, operator, conditioner, remark=''):
        log_entry = Log(type=log_type, time=datetime.now(), operator=operator, object_id=conditioner.id, remark=remark)
        db.session.add(log_entry)

    ac = Conditioner.query.filter_by(room_number=user.id).first()
    if ac:
        write_log('入住', '前台', ac, remark='无')
    else:
        return jsonify({'error': '对应的空调设备不存在'}), 404

    db.session.commit()

    return jsonify({'success': '客户注册成功', 'user_id': user.id}), 200


@conditioner.route('/api/conditioners/reception_check_out_for_customer/', methods=['POST'])
def reception_check_out_for_customer():
    data = request.get_json()
    room_number = data.get('room_number')

    # 检查房间是否已经入住
    room_numbers = {conditioner.room_number: True for conditioner in Conditioner.query.all()}
    logs = Log.query.filter(Log.type.in_(['入住', '结算'])).all()
    for log in logs:
        if log.type == '入住':
            room_numbers[log.conditioner.room_number] = False
        else:
            room_numbers[log.conditioner.room_number] = True

    if room_numbers.get(room_number, True):
        return jsonify({'error': '房间未被入住'}), 400

    user = User.query.filter_by(name=room_number).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    # 写入结算日志
    def write_log(log_type, operator, conditioner, remark=''):
        log_entry = Log(type=log_type, time=datetime.now(), operator=operator, object_id=conditioner.id, remark=remark)
        db.session.add(log_entry)

    ac = Conditioner.query.filter_by(room_number=user.id).first()
    if ac:
        write_log('结算', '前台', ac, remark='无')

        # 更新空调状态
        ac.status = False
        ac.temperature_set = 25
        ac.mode = '中风速'
        ac.total_cost += ac.cost
        ac.cost = 0

        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': '客户退房成功'}), 200
    else:
        return jsonify({'error': '对应的空调设备不存在'}), 404


@conditioner.route('/api/conditioners/reset/', methods=['POST'])
def reset_all_ac_info():
    # 假设的初始状态和密码
    temperature_now = {
        "房间101": 10,
        "房间102": 15,
        "房间103": 18,
        "房间104": 12,
        "房间105": 14,
    }
    password = {
        "房间101": "1111",
        "房间102": "2222",
        "房间103": "3333",
        "房间104": "4444",
        "房间105": "5555",
    }

    conditioners = Conditioner.query.all()
    for ac in conditioners:
        user = User.query.get(ac.room_number)
        if user:
            # 退房
            user.password = ''
            # 写日志
            write_log('结算', '前台', ac, remark='无')

            # 重置空调
            ac.status = False
            ac.temperature_set = 22
            ac.temperature_now = temperature_now.get(user.name, 20)  # 为每个房间设置初始温度
            ac.mode = '中风速'
            ac.total_cost += ac.cost
            ac.cost = 0

            # 重新入住
            user.password = password.get(user.name, '0000')  # 为每个房间设置新密码
            # 写日志
            write_log('入住', '前台', ac, remark='无')

    # 重置设置
    setting = Settings.query.get(1)
    if setting:
        setting.mode = '制热'
        setting.temperature_upper = 25
        setting.temperature_lower = 18
        setting.low_speed_fee = 1
        setting.mid_speed_fee = 1
        setting.high_speed_fee = 1

    db.session.commit()
    return jsonify({'success': '所有空调和设置重置成功'}), 200


