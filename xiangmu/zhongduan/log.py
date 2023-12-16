from flask import Flask, render_template, request, redirect, url_for, session, Blueprint
from data import log_data

log_and_submit = Blueprint('log_and_submit', __name__)


@log_and_submit.route('/')
def login():
    """
    进入网页后先登录
    :return: 返回一个本地的网页内容
    """
    if 'username' in session:
        if session['username'] == '客户':
            return redirect(url_for('customer.homepage'))  # 导入到对应的首页
        elif session['username'] == '管理员' or session['username'] == '前台':
            return redirect(url_for('hotel_receptionist.homepage'))  # 导入到对应的首页
    else:
        return render_template('login.html')


@log_and_submit.route('/submit', methods=['POST', 'GET'])
def submit():
    """
    在登陆提交表单后依据表单中的内容确定要转到哪边，并且依据身份建立对应对话session['username']=?，如果是某个房间的使用者session可以加上对应的房间号
    return:
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        roll = request.form['roll']
    else:
        username = request.args.get('username')
        password = request.args.get('password')
        roll = request.args.get('roll')

    try:
        # 申请数据库对应的内容，返回字典与是否正确，不正确则弹出错误转到except部分
        dic = log_data(username, password, roll)
        if dic.verification == True and dic.identify == True:
            # 如果正确，则依据身份不同建立对应的session，包括房间号等
            session['username'] = username
            session['identification'] = roll
            session['token'] = dic.token
            if session['identification'] == '客户':
                session['room_id'] = dic.room_id
                return redirect(url_for('customer.homepage'))
            else:
                return redirect(url_for('hotel_receptionist.homepage'))
        raise Exception("Verification failed")  # 只要工作做不成就报错转到except，成了直接返回走

    except:
        #   出现查询不到对应内容，账号密码错误的时候弹到让这部分
        return '账号密码不正确或网络错误'
