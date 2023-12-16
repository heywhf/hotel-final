from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, send_file
from data import hotel_data
import pandas as pd
import os

hotel_receptionist = Blueprint('hotel_receptionist', __name__)


# 功能：办理入住，打印某房间详单，退房，查询或修改某房间状态
@hotel_receptionist.route('/')
def homepage():
    '''
    检查是否是前台，返回前台的首页
    :return: 首页
    '''
    if 'username' in session:
        # 检查是不是前台，是的话返回前台首页，不是的话返回顾客首页
        if session['identification'] == '客户':
            return redirect(url_for('customer.homepage'))
        else:
            return render_template('receptionist_homepage.html', name=session['username'])
        pass

    else:
        # 连注册都没注册的话送到登录页面去
        return redirect(url_for('log_and_submit.login'))


@hotel_receptionist.route('/query')
def query():
    """
    查询房间状态，返回一个列表
    :return: 列表展示的页面，包括返回的相关内容
    """
    if 'username' in session:
        # 检查是不是前台，是的话返回前台首页，不是的话返回顾客首页
        if session['identification'] == '客户':
            return redirect(url_for('customer.homepage'))
        else:
            action = request.args.get('action')
            dic = hotel_data(session['username'])
            dic.room(session['token'])
            print(dic.room_id, dic.used_id, dic.used_id)
            if action == 'check_in':
                return render_template('query.html', list1=dic.room_id, list2=dic.nused_id, message='该房间已被使用',
                                       target_url='/receptionist/check_in')
            elif action == 'print_receipt':
                return render_template('query.html', list1=dic.room_id, list2=dic.used_id, message='该房间无人使用',
                                       target_url='/receptionist/print_receipt')
            elif action == 'check_out':
                return render_template('query.html', list1=dic.room_id, list2=dic.used_id, message='该房间无人使用',
                                       target_url='/receptionist/check_out')
            elif action == 'look':
                return render_template('query.html', list1=dic.room_id, list2=dic.room_id, message='啊？',
                                       target_url='/receptionist/look')
        pass

    else:
        # 连注册都没注册的话送到登录页面去
        return redirect(url_for('log_and_submit.login'))


@hotel_receptionist.route('/check_in', methods=['POST', 'GET'])
def check_in():
    """
    办理入住，输入相关信息，办理入住，修改状态
    :return: 办理成功或失败的信息
    """
    if 'username' in session:
        # 检查是不是前台，是的话返回前台首页，不是的话返回顾客首页
        if session['identification'] == '客户':
            return redirect(url_for('customer.homepage'))
        else:
            if request.method == 'POST':
                password = request.form['password']
                room_id = request.form['roomNumber']
                user_name = request.form['user_name']
                dic = hotel_data('username')
                print(password, room_id, user_name)
                try:
                    if dic.check_in(roomNumber=room_id, password=password, token=session['token'], user_name=user_name):
                        return render_template('good_check_in.html', roomNumber=room_id)
                    raise Exception("Verification failed")  # 只要工作做不成就报错转到except，成了直接返回走
                except:
                    return '房间号不正确或网络错误'
            else:
                room_id = request.args.get('element')
                return render_template('check-in.html', roomNumber=room_id)
        pass

    else:
        # 连注册都没注册的话送到登录页面去
        return redirect(url_for('log_and_submit.login'))


@hotel_receptionist.route('/check_out')
def check_out():
    """
    办理退房，将状态修改回最初
    :return: 办理成功或失败的信息
    """
    if 'username' in session:
        # 检查是不是前台，是的话返回前台首页，不是的话返回顾客首页
        if session['identification'] == '客户':
            return redirect(url_for('customer.homepage'))
        else:
            dic = hotel_data(session['username'])
            room_id = request.args.get('element')
            judgment, data = dic.check_out(room_id, session['token'])
            if judgment:
                # 创建Excel文件
                df = pd.DataFrame(data)
                filename = f'checkout_{room_id}.xlsx'
                df.to_excel(filename, index=False)
                # 在session中存储文件名
                session['excel_filename'] = filename
                return render_template('good_check_out.html', room_id=room_id)
            else:
                return '房间号不正确或网络错误'
        pass

    else:
        # 连注册都没注册的话送到登录页面去
        return redirect(url_for('log_and_submit.login'))


@hotel_receptionist.route('/download_excel')
def download_excel():
    filename = session['excel_filename']
    if filename and os.path.exists(filename):
        response = send_file(filename, as_attachment=True)
        return response
    else:
        return "文件不存在", 404


@hotel_receptionist.route('/query_all')
def query_all():
    """
    查询全部信息
    :return :信息页面
    """
    if 'username' in session:
        # 检查是不是前台，是的话返回前台首页，不是的话返回顾客首页
        if session['identification'] == '客户':
            return redirect(url_for('customer.homepage'))
        else:
            return render_template('receptionist_homepage.html', name=session['username'])
        pass

    else:
        # 连注册都没注册的话送到登录页面去
        return redirect(url_for('log_and_submit.login'))


@hotel_receptionist.route('/print_receipt')
def print_receipt():
    """
    打印收据
    :return :下载excel表格
    """
    if 'username' in session:
        # 检查是不是前台，是的话返回前台首页，不是的话返回顾客首页
        if session['identification'] == '客户':
            return redirect(url_for('customer.homepage'))
        else:
            dic = hotel_data(session['username'])
            room_id = request.args.get('element')
            data = dic.check_room_expense(room_id,session['token'])
            if data:
                df = pd.DataFrame(data)
                filename = f'checkout_{room_id}.xlsx'
                df.to_excel(filename, index=False)
                # 在session中存储文件名
                session['excel_filename'] = filename
                return render_template('print_receipt.html', room_id=room_id)
            else:
                return '房间号不正确或网络错误'
    else:
        # 连注册都没注册的话送到登录页面去
        return redirect(url_for('log_and_submit.login'))


@hotel_receptionist.route('/change')
def change():
    """
    依据方法进入对应房间修改页面或者修改房间内容
    :return :下载excel表格
    """
    if 'username' in session:
        # 检查是不是前台，是的话返回前台首页，不是的话返回顾客首页
        if session['identification'] == '客户':
            return redirect(url_for('customer.homepage'))
        else:
            return render_template('receptionist_homepage.html', name=session['username'])
    else:
        # 连注册都没注册的话送到登录页面去
        return redirect(url_for('log_and_submit.login'))


@hotel_receptionist.route('/operate_set', methods=['POST', 'GET'])
def operate_set():
    """
    依据方法进入对应房间修改页面或者修改房间内容
    :return :下载excel表格
    """
    if 'username' in session:
        # 检查是不是前台，是的话返回前台首页，不是的话返回顾客首页
        if session['identification'] == '客户':
            return redirect(url_for('customer.homepage'))
        else:
            dic = hotel_data(session['username'])
            if request.method == 'GET':
                try:
                    temp_upper_limit, temp_lower_limit, work_modes, speed_rates = dic.getoperate()
                    return render_template('operate_set.html',
                                           temp_upper_limit=temp_upper_limit,
                                           temp_lower_limit=temp_lower_limit,
                                           work_modes=work_modes,
                                           speed_rates=speed_rates)
                except:
                    return '网络/权限出现问题'
            else:
                try:
                    dic = hotel_data(session['username'])
                    temp_upper_limit = request.form.get('tempUpperLimit')
                    temp_lower_limit = request.form.get('tempLowerLimit')
                    work_mode = request.form.get('workMode')
                    rate_low = request.form.get('rateLow')
                    rate_medium = request.form.get('rateMedium')
                    rate_high = request.form.get('rateHigh')
                    print(temp_upper_limit, temp_lower_limit, work_mode, rate_low, rate_medium, rate_high)
                    if not dic.operate_set(temp_upper_limit, temp_lower_limit, work_mode, rate_low, rate_medium,
                                           rate_high):
                        raise Exception("Verification failed")
                    return render_template('receptionist_homepage.html', name=session['username'])
                except:
                    return '网络/权限出现问题'
    else:
        # 连注册都没注册的话送到登录页面去
        return redirect(url_for('log_and_submit.login'))


@hotel_receptionist.route('/log_out')
def log_out():
    """
    依据方法进入对应房间修改页面或者修改房间内容
    :return :下载excel表格
    """
    if 'username' in session:
        # 检查是不是前台，是的话返回前台首页，不是的话返回顾客首页
        if session['identification'] == '客户':
            return redirect(url_for('customer.homepage'))
        else:
            session.clear()
    else:
        # 连注册都没注册的话送到登录页面去
        return redirect(url_for('log_and_submit.login'))
