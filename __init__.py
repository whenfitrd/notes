#! /usr/bin/env python3
#coding=utf-8

from flask import Flask
from config import Config
from flask_pagedown import PageDown

from flask_bootstrap import Bootstrap
from flask_login import LoginManager

from datetime import timedelta

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'views.login'

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    login_manager.init_app(app)
    pagedown = PageDown(app)
    bootstrap = Bootstrap(app)

    app.permanent_session_lifetime = timedelta(minutes=5)

    login_manager.remenber_coocie_duration=timedelta(minutes=60)

    from views import views
    app.register_blueprint(views, url_prefix='')

    return app
