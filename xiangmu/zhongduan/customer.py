from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, jsonify
import requests
import json
import data
from data import log_data,hotel_data
customer = Blueprint('customer', __name__)
PATH = data.PATH



base_data = {
            'roomNumber': 0,
            'currentTemperature': 0,
            'targetTemperature': 0,
            'acStatus': '',
            'acMode': '',
            'cost': 0,
            'totalCost': 0,
            'queueStatus': '',
        }

@customer.route('/')
def homepage():
    """
    检查是否是房间使用者，返回使用者房间的首页
    :return: 首页
    """
    if 'username' in session:
        if session['identification'] == '客户':
            return render_template('customer_homepage.html')
        else:
            return render_template('customer_homepage.html')


    else:
        # 连注册都没注册的话送到登录页面去
        #return render_template('customer_homepage.html')
        return redirect(url_for('log_and_submit.login'))


@customer.route('/open_condition')
def open_condition():
    """
    依据数据库内容开启或关闭空调（修改对应空调状态）
    :return: 成功开启/关闭空调的信息或者未能成功关闭
    """
    if 'username' in session:
        # 检查是不是房间使用者，是的话依据数据库内容开启或关闭空调（修改对应空调状态），不是的话返回管理者或者前台首页
        # if session['username' ]==?:
        #     return render_template('')
        # else:
        #     url_for('customer.homepage')
        pass

    else:
        # 连注册都没注册的话送到登录页面去
        return redirect(url_for('log_and_submit.login'))

@customer.route('/air_conditioner/', methods=['POST'])
def post():
    print('start')
    print(request.form.to_dict())
    print(session)
    if 'username' in session:
        print('username')
        if session['identification'] == '客户':
            if 'room_id' in session:
                function = hotel_data('')
                print(session)
                function.update_ac(session['room_id'],request.form.to_dict(),session['token'])
                return jsonify({'msg':'成功'}),200
            else:
                return jsonify({'msg':'请先登记入住'}),404



@customer.route('/check')
def check():
    """
    检查自身房间的状态
    :return: 房间状态信息页面
    """
    if 'username' in session:
        # 检查是不是房间使用者，是的话查询数据库并返回空调状态页面，不是的话返回管理者或者顾客首页
        # if session['username' ]==?:
        #     return render_template('')
        # else:
        #     url_for('customer.homepage')
        pass

    else:
        # 连注册都没注册的话送到登录页面去
        return redirect(url_for('log_and_submit.login'))


@customer.route('/change')
def change():
    """
    修改自身房间的状态
    :return: 修改是否成功的信息
    """
    if 'username' in session:
        # 检查是不是房间使用者，是的话依据对应信息进行修改，返回是否成功，不是的话返回管理者或者顾客首页
        # if session['username' ]==?:
        #     return render_template('')
        # else:
        #     url_for('customer.homepage')
        pass

    else:
        # 连注册都没注册的话送到登录页面去
        return redirect(url_for('log_and_submit.login'))
