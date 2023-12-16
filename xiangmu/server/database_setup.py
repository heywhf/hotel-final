from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from extension import db
from datetime import datetime
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    identity = db.Column(db.String(50), nullable=False)


class Conditioner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature_now = db.Column(db.Float, nullable=False)
    temperature_set = db.Column(db.Float, nullable=False)
    mode = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Boolean, nullable=False)
    room_number = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    update_times = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    queue_status = db.Column(db.Boolean, nullable=False)
    queue_time = db.Column(db.DateTime, nullable=False)


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(100), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    operator = db.Column(db.String(50), nullable=False)
    object_id = db.Column(db.Integer, db.ForeignKey('conditioner.id'), nullable=False)
    remark = db.Column(db.Text, nullable=True)


class Detail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.Integer, nullable=False)
    request_duration = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    service_duration = db.Column(db.Integer, nullable=False)
    speed = db.Column(db.String(50), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, nullable=False)


class Settings(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Boolean, default=False)  # 开关状态
    temperature_upper = db.Column(db.Integer)  # 温度上限
    temperature_lower = db.Column(db.Integer)  # 温度下限
    mode = db.Column(db.String(20))  # 模式，只有三种选择：制冷，制热，通风
    # 新增的字段
    low_speed_fee = db.Column(db.Float, default=1)  # 低速风费率 (元/1C°)
    mid_speed_fee = db.Column(db.Float, default=1)  # 中速风费率 (元/1C°)
    high_speed_fee = db.Column(db.Float, default=1)  # 高速风费率 (元/1C°)
