from flask import Flask, request, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from database_setup import Conditioner, Log, Detail, Settings,User
from extension import db

Log = Blueprint('log', __name__)


def write_log(log_type, operator, ac, remark='无', request_data=None, up=True):
    if log_type == '开关机':
        log_entry = Log(
            type=log_type,
            time=datetime.now(),
            operator=operator,
            object_id=ac.id,
            remark='关机' if ac.status else '开机'
        )
        db.session.add(log_entry)

    elif log_type == '调温':
        target_temperature = request_data.get('targetTemperature') if request_data else ac.temperature_set
        log_entry = Log(
            type=log_type,
            time=datetime.now(),
            operator=operator,
            object_id=ac.id,
            remark=f'温度从{ac.temperature_set}°C调整到{target_temperature}°C'
        )
        db.session.add(log_entry)

    elif log_type == '调风':
        ac_mode = request_data.get('acMode') if request_data else ac.mode
        log_entry = Log(
            type=log_type,
            time=datetime.now(),
            operator=operator,
            object_id=ac.id,
            remark=f'从{ac.mode}调整到{ac_mode}'
        )
        db.session.add(log_entry)

    elif log_type == '请求服务' or log_type == '调度':
        log_entry = Log(
            type=log_type,
            time=datetime.now(),
            operator=operator,
            object_id=ac.id,
            remark=remark
        )
        db.session.add(log_entry)

    elif log_type == '结束服务':
        final_remark = remark
        if remark == '无':
            final_remark = f'温度已达标,当前温度{ac.temperature_now}°C,目标温度{ac.temperature_set}°C,当前模式{ac.mode},服务结束'
        log_entry = Log(
            type=log_type,
            time=datetime.now(),
            operator=operator,
            object_id=ac.id,
            remark=final_remark
        )
        db.session.add(log_entry)

    elif log_type == '产生费用':
        setting = Settings.query.get(1)
        fee_rate = 0
        if ac.mode == '低风速':
            fee_rate = setting.low_speed_fee
        elif ac.mode == '中风速':
            fee_rate = setting.mid_speed_fee
        elif ac.mode == '高风速':
            fee_rate = setting.high_speed_fee
        fee = fee_rate * 0.5
        new_temp = ac.temperature_now + 0.5 if up else ac.temperature_now - 0.5
        log_entry = Log(
            type=log_type,
            time=datetime.now(),
            operator=operator,
            object_id=ac.id,
            remark=f'温度从{ac.temperature_now}°C{"升高" if up else "降低"}到{new_temp}°C,当前风速为{ac.mode},对应费率为{fee_rate * 2}元/1°C,产生费用{fee}元,费用从{round(ac.cost, 2)}元增加到{round(ac.cost + fee, 2)}元'
        )
        db.session.add(log_entry)

    elif log_type == '入住' or log_type == '结算':
        log_entry = Log(
            type=log_type,
            time=datetime.now(),
            operator=operator,
            object_id=ac.id,
            remark=remark
        )
        db.session.add(log_entry)

    db.session.commit()


def write_detail(ac):
    # 获取与当前conditioner相关的请求服务的Log对象,取最新的一个
    request_log = Log.query.filter_by(object_id=ac.id, type='请求服务').order_by(Log.time.desc()).first()
    if not request_log:
        return  # 如果没有相关日志，则不执行后续操作

    # 开始时间
    start_time = request_log.time

    # 结束时间
    end_service_log = Log.query.filter(Log.object_id == ac.id, Log.type == '结束服务',
                                       Log.time > request_log.time).order_by(Log.time).first()
    if not end_service_log:
        return  # 如果没有结束服务日志，则不执行后续操作

    end_time = end_service_log.time

    # 请求时长
    request_duration = (end_time - start_time).total_seconds()

    # 计算服务时长
    server_time = timedelta(0)
    dispatch_logs = Log.query.filter(Log.object_id == ac.id, Log.type == '调度', Log.time > start_time,
                                     Log.time < end_time).order_by(Log.time).all()
    for dispatch_log in dispatch_logs:
        if dispatch_log.remark.endswith('运行态'):
            next_dispatch_log = Log.query.filter(Log.time > dispatch_log.time, Log.object_id == ac.id,
                                                 Log.type == '调度').order_by(Log.time).first()
            end_run_time = next_dispatch_log.time if next_dispatch_log else datetime.now()
            server_time += end_run_time - dispatch_log.time

    # 计算费用
    cost_logs = Log.query.filter(Log.object_id == ac.id, Log.type == '产生费用', Log.time > start_time,
                                 Log.time < end_time).all()
    cost = sum(float(log.remark.split('产生费用')[1].strip('元').split(' ')[0]) for log in cost_logs)

    # 累计费用
    total_cost = ac.cost

    # 费率
    setting = Settings.query.get(1)
    fee = getattr(setting, f"{ac.mode.lower()}_speed_fee")

    # 写入detail
    detail_entry = Detail(
        room_number=ac.room_number,  # 假设这是房间号
        request_duration=request_duration,
        start_time=start_time,
        end_time=end_time,
        service_duration=server_time.total_seconds(),
        speed=ac.mode,
        cost=cost,
        total_cost=total_cost,
        fee=fee
    )
    db.session.add(detail_entry)
    db.session.commit()


# 获取特定空调信息
@Log.route('/api/logs/get_ac_info/', methods=['POST'])
def get_ac_info():
    try:
        data = request.get_json()
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        if start_time_str != 'init' and end_time_str != 'init':
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
            logs_query = Log.query.filter(Log.time >= start_time, Log.time <= end_time)
        else:
            logs_query = Log.query

        conditioners = Conditioner.query.order_by(Conditioner.room_number).all()
        detail = {}
        for conditioner in conditioners:
            room_name = conditioner.room_number
            detail[room_name] = {
                'roomNumber': room_name,
                'on_off_times': 0,
                'dispatch_times': 0,
                'detail_times': 0,
                'temperature_times': 0,
                'mode_times': 0,
                'request_time': 0,
                'total_cost': 0,
            }

        for log in logs_query.all():
            if log.object_id:
                conditioner = Conditioner.query.get(log.object_id)
                if conditioner:
                    room_name = conditioner.room_number
                    detail[room_name]['detail_times'] += 1

                    if log.type == '开关机':
                        detail[room_name]['on_off_times'] += 1
                    elif log.type == '调度':
                        detail[room_name]['dispatch_times'] += 1
                    elif log.type == '调温':
                        detail[room_name]['temperature_times'] += 1
                    elif log.type == '调风':
                        detail[room_name]['mode_times'] += 1

                    # 计算请求时长
                    if log.type == '请求服务':
                        end_service_log = Log.query.filter(
                            Log.object_id == conditioner.id,
                            Log.type == '结束服务',
                            Log.time > log.time
                        ).first()
                        if end_service_log:
                            request_time = end_service_log.time - log.time
                        else:
                            request_time = datetime.now() - log.time
                        detail[room_name]['request_time'] += request_time.total_seconds()

                    # 计算总费用
                    if log.type == '产生费用':
                        fee = float(log.remark.split('产生费用')[1].strip('元').split(' ')[0])
                        detail[room_name]['total_cost'] += fee

        detail_array = list(detail.values())
        return jsonify({'detail': detail_array}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 获取所有日志信息
@Log.route('/api/logs/get_all_logs/', methods=['GET'])
def get_all_logs():
    current_time = datetime.now()
    start_time = current_time - timedelta(days=30)

    room_expense = []
    for ac in Conditioner.query.join(User, Conditioner.room_number == User.id).order_by(User.name).all():
        logs = Log.query.filter_by(object_id=ac.id, type='产生费用').filter(Log.time >= start_time).all()

        cost_per_day = {}
        for log in logs:
            log_date = log.time.date()
            fee_str = log.remark.split('产生费用')[1].strip('元').split(' ')[0]
            fee = float(fee_str)

            if log_date not in cost_per_day:
                cost_per_day[log_date] = 0
            cost_per_day[log_date] += fee

        cost_per_day_array = [{'label': str(date), 'cost': cost} for date, cost in cost_per_day.items()]
        cost_per_day_array.sort(key=lambda x: x['label'])

        room_expense.append({
            'labels': ac.room_number.name,  # 房间号，通过关联的 User 对象获取
            'datasets': cost_per_day_array,
        })

    return jsonify({'roomExpense': room_expense}), 200


# 获取房间费用信息
@Log.route('/api/logs/get_all_logs/', methods=['GET'])
def get_logs():
    log_list = []
    for ac in Conditioner.query.all():
        # 获取最新的入住日志
        check_in_log = Log.query.filter_by(object_id=ac.id, type='入住').order_by(Log.time.desc()).first()
        if check_in_log:
            # 获取入住之后的所有日志
            logs_after_check_in = Log.query.filter(Log.object_id == ac.id, Log.time >= check_in_log.time).order_by(Log.time).all()
            for log in logs_after_check_in:
                user = User.query.get(ac.room_number)
                room_name = user.name if user else '未知房间'  # 如果找不到对应的 User，使用 '未知房间'

                log_list.append({
                    'type': log.type,
                    'operator': log.operator,
                    'object': room_name,
                    'time': log.time.isoformat(),
                    'remark': log.remark,
                })
    return jsonify({'log': log_list}), 200


# 获取所有详细信息
@Log.route('/api/logs/get_all_details/', methods=['GET'])
def get_all_details():
    detail_list = []
    for ac in Conditioner.query.all():
        # 获取最新的入住日志
        check_in_log = Log.query.filter_by(object_id=ac.id, type='入住').order_by(Log.time.desc()).first()
        if check_in_log:
            # 获取入住之后的所有详单记录
            details_after_check_in = Detail.query.filter(Detail.room_number == ac.id, Detail.start_time >= check_in_log.time).order_by(Detail.start_time).all()
            for detail in details_after_check_in:
                detail_list.append({
                    'roomNumber': detail.room_number,  # 假设这是房间号
                    'requestDuaration': detail.request_duration,
                    'startTime': (detail.start_time + timedelta(hours=8)).isoformat(),
                    'endTime': (detail.end_time + timedelta(hours=8)).isoformat(),
                    'serviceDuaration': detail.service_duration,
                    'speed': detail.speed,
                    'cost': detail.cost,
                    'fee': detail.fee,
                })
    return jsonify({'detail': detail_list}), 200