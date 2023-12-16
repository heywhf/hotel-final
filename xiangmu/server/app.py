from flask import Flask
from extension import db
from conditioner import conditioner
from users import users
from log import Log
from set_up import set_up
def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.register_blueprint(conditioner,url_prefix='/conditioner')
    app.register_blueprint(users,url_prefix='/users')
    app.register_blueprint(Log,url_prefix='/Log')
    app.register_blueprint(set_up,url_prefix='/set_up')

    return app
