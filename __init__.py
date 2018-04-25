#! /usr/bin/env python3
#coding=utf-8

from flask import Flask
from config import Config
from flask_pagedown import PageDown

from flask_bootstrap import Bootstrap

def create_app():
    app = Flask(__name__)
    pagedown = PageDown(app)
    bootstrap = Bootstrap(app)
    app.config.from_object(Config)

    from views import views
    app.register_blueprint(views, url_prefix='')

    return app
