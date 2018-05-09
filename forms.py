#! /usr/bin/env python3
#coding=utf-8

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, TextAreaField, RadioField
from wtforms.validators import DataRequired, Length

from flask_pagedown.fields import PageDownField

class ContentForm(FlaskForm):
    pagedown = PageDownField('Enter your markdown')
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    account = StringField('账号', id='inputAccount')
    passwd = PasswordField(id='repeatPassword')
    checkbox = BooleanField()
    submit = SubmitField('登入')

class RegisterForm(FlaskForm):
    account = StringField('账号', id='inputAccount')
    passwd = PasswordField(id='Password')
    repeatPasswd = PasswordField(id='repeatPassword')
    submit = SubmitField('注册')

class AddentryForm(FlaskForm):
    title = StringField('标题', id='name')
    content = TextAreaField(id='content')
    submit = SubmitField('提交')

class EditroleinfoForm(FlaskForm):
    nickname = StringField(id="inputnickname")
    sex = RadioField(choices=[('男', 1), ('女', 2)])
    old = StringField(id='inputold')
    city = StringField(id='inputcity')
    signature = TextAreaField(id='inputsignature')
    submit = SubmitField('提交')

class AddArticleForm(FlaskForm):
    title = StringField()
    content = PageDownField('Enter your markdown')
    submit = SubmitField('submit')
