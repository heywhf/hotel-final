from flask import Flask, request, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from database_setup import User,Conditioner,Log
from sqlalchemy import or_

hotel_receptionist = Blueprint('users', __name__)
from extension import db

users = Blueprint('users', __name__)


# 用户登录
@users.route('/api/accounts/login/', methods=['POST'])
def login():
    try:
        username = request.json.get('name')
        password = request.json.get('password')
        user = User.query.filter_by(name=username, password=password).first()
        if user:
            return jsonify({'success': '登录成功', 'user_id': user.name}), 200
        else:
            return jsonify({'error': '用户名或密码错误'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 添加用户
@users.route('/api/accounts/add_room/', methods=['POST'])
def add_room():
    try:
        name = request.json.get('name')
        password = request.json.get('password')
        identity = request.json.get('identity')
        new_user = User(name=name, password=password, identity=identity)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'success': '新用户添加成功', 'user_id': new_user.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 更改密码
@users.route('/api/accounts/change_password/', methods=['POST'])
def change_password():
    try:
        user_name = request.json.get('name')
        old_password = request.json.get('old_password')
        new_password = request.json.get('new_password')
        user = User.query.filter(User.username == user_name).first()
        if user and user.password == old_password:
            user.password = new_password
            db.session.commit()
            return jsonify({'success': '密码更改成功'}), 200
        else:
            return jsonify({'error': '旧密码错误或用户不存在'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 获取所有用户名称
@users.route('/api/accounts/get_unused_rooms_name/', methods=['GET'])
def get_rooms_name():

    try:
        roomNumber = {}
        for conditioner in Conditioner.query.order_by(Conditioner.room_number).all():
            roomNumber[conditioner.room_number] = True

        for log in Log.query.filter(or_(Log.type == '入住', Log.type == '结算')).all():
            if log.type == '入住':
                roomNumber[log.object_id] = True
            else:
                roomNumber[log.object_id] = False

        # 生成入住房间列表
        rooms_name = [room for room, occupied in roomNumber.items() if not occupied]

        # 返回入住房间列表
        return jsonify({'rooms_name': rooms_name}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
