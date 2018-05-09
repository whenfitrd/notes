#! /usr/bin/env python3
#coding=utf-8

from flask import render_template, request, g, session, redirect,\
    abort, flash, url_for, make_response
import pymysql

from crypto import get_md5, encrypt, decrypt, get_aeskey

from flask import Blueprint

from flask_login import login_required, login_user, logout_user
from __init__ import login_manager
from models import User

from markdown import markdown
import bleach

from forms import ContentForm, LoginForm, RegisterForm, AddentryForm,\
     EditroleinfoForm, AddArticleForm

views = Blueprint('views', __name__)

from config import Config

from mylogger import Logger

mylogger = Logger().getLogger()

def connect_db():
    try:
        db = pymysql.connect(host=Config.host, user=Config.user,\
        passwd=Config.passwd, db=Config.dbname, use_unicode=True, charset='utf8')
        cur = db.cursor()
        return db, cur
    except Exception as e:
        mylogger.error(str(e))

@views.before_request
def before_request():
    g.db, g.cur = connect_db()

@views.teardown_request
def teardown_request(exception):
    g.cur.close()
    g.db.close()

@views.route('/')
def index():
    return redirect(url_for('views.login'))

@views.route('/showentries', methods=['GET'])
@views.route('/showentries/<int:currentpage>', methods=['GET'])
@login_required
def show_entries(currentpage=1):
    if session.get('search') and session['search'] and session.get('entries') and not session.get('entryupdate'):
        entries = session['entries']
        session['maxpage'] = (len(entries)-1)//5+1
        return render_template('showentries.html', entries=entries, currentpage=currentpage, maxpage=session['maxpage'])

    sql = "select id, title, content, createtime from entries where user_id=%s order by id desc"
    try:
        # user_id = get_cookie('user_id')
        # aeskey = get_cookie('aeskey')
        statu = g.cur.execute(sql, str(session['user_id']))
        entries = [dict(id=row[0], title=decrypt(row[1], session['aeskey']).decode('utf-8'),\
        text=decrypt(row[2], session['aeskey']).decode('utf-8'), createtime=row[3])\
        for row in g.cur.fetchall()]
    except Exception as e:
        mylogger.error(str(e))
        abort(401)
    session['maxpage'] = (len(entries)-1)//5+1
    session['entryupdate'] = False
    return render_template('showentries.html', entries=entries, currentpage=currentpage, maxpage=session['maxpage'])

@views.route('/prepage', methods=['GET'])
@login_required
def pre_page():
    if session['currentpage'] > 1:
        session['currentpage'] -= 1
    return redirect(url_for('views.show_entries', currentpage=session['currentpage']))

@views.route('/nextpage', methods=['GET'])
@login_required
def next_page():
    if session['currentpage'] < session['maxpage']:
        session['currentpage'] += 1
    return redirect(url_for('views.show_entries', currentpage=session['currentpage']))

@views.route('/search', methods=['POST'])
@login_required
def search():
    if request.form['search'] is None:
        redirect(url_for('views.show_entries', currentpage=session['currentpage']))

    sql = "select id, title, content, createtime from entries where user_id=%s order by id desc"
    try:
        statu = g.cur.execute(sql, str(session['user_id']))
        entries = [dict(id=row[0], title=decrypt(row[1], session['aeskey']).decode('utf-8'),\
        text=decrypt(row[2], session['aeskey']).decode('utf-8'), createtime=row[3])\
        for row in g.cur.fetchall()]
    except Exception as e:
        mylogger.error(str(e))
        abort(401)
    searchlist = list()
    for entry in entries:
        if request.form['search'] in entry['title'] or request.form['search'] in entry['text']:
            searchlist.append(entry)

    if not session.get('search'):
        session['search'] = False

    session['entries'] = searchlist
    session['currentpage'] = 1
    session['search'] = True
    session['searchkey'] = request.form['search']

    session['maxpage'] = (len(searchlist)-1)//5+1

    return render_template('showentries.html', entries=searchlist, currentpage=session['currentpage'], maxpage=session['maxpage'])

@views.route('/addentry', methods=['POST', 'GET'])
@login_required
def add_entry():
    addentryForm = AddentryForm()
    if request.method == 'POST':
        try:
            g.cur.execute('insert into entries (user_id, title, content) values (%s, %s, %s)',\
            [str(session['user_id']), encrypt(addentryForm.title.data, session['aeskey']), encrypt(addentryForm.content.data, session['aeskey'])])
            g.db.commit()
        except Exception as e:
            mylogger.error(str(e))
            g.db.rollback()
            return redirect(url_for('views.add_entry'))
        flash('提交成功')
        return redirect(url_for('views.show_entries', currentpage=session['currentpage']))
    return render_template('addentry.html', form=addentryForm)

@views.route('/editentry', methods=['POST'])
@login_required
def update_entry():
    addentryForm = AddentryForm()
    sql = "update entries set title=%s, content=%s where id=%s"
    try:
        g.cur.execute(sql, [encrypt(addentryForm.title.data, session['aeskey']), encrypt(addentryForm.content.data, session['aeskey']), request.form['id']])
        g.db.commit()
        session['entryupdate'] = True
    except Exception as e:
        mylogger.error(str(e))
        g.db.rollback()
    return redirect(url_for('views.show_entries', currentpage=session['currentpage']))

@views.route('/editentry/<int:id>', methods=['GET'])
@login_required
def edit_entry(id):
    addentryForm = AddentryForm()
    sql = "select id, title, content, createtime from entries where id=%s"
    try:
        statu = g.cur.execute(sql, [id])
        entries = [dict(id=row[0], title=decrypt(row[1], session['aeskey']).decode('utf-8'),\
        text=decrypt(row[2], session['aeskey']).decode('utf-8'), createtime=row[3])\
        for row in g.cur.fetchall()]
    except Exception as e:
        mylogger.error(str(e))
        abort(401)
    return render_template('addentry.html', entry=entries[0], form=addentryForm)

@views.route('/del/<int:id>', methods=['GET'])
@login_required
def del_entry(id):
    try:
        g.cur.execute('delete from entries where id=%s', [id])
        g.db.commit()
        flash('删除成功')
    except Exception as e:
        mylogger.error(str(e))
        g.db.rollback()
    return redirect(url_for('views.show_entries', currentpage=session['currentpage']))

@views.route('/register', methods=['GET', 'POST'])
def register():
    registerForm = RegisterForm()
    if request.method == 'POST':
        sql = "INSERT INTO users(username, password, aeskey) VALUES (%s, %s, %s)"
        if registerForm.passwd.data != registerForm.repeatPasswd.data:
            flash('输入的两次密码不相同')
            return redirect(url_for('views.register'))
        try:
            g.cur.execute(sql, [registerForm.account.data, get_md5(registerForm.passwd.data), get_aeskey()])
            g.db.commit()
            return redirect(url_for('views.login'))
        except Exception as e:
            mylogger.error(str(e))
            g.db.rollback()
            flash('注册失败')
    return render_template('register.html', form=registerForm)

@login_manager.user_loader
def user_loader(user_id):
    return User(user_id)

def set_cookie(name, value):
    resp = make_response('set cookie')
    resp.set_cookie(name, value)

def get_cookie(name):
    cookie = request.cookies.get(name)
    return cookie

@views.route('/login', methods=['GET', 'POST'])
def login():
    loginForm = LoginForm()
    if request.method == 'POST':
        sql = "select * from users where username=%s and password=%s"
        try:
            g.cur.execute(sql, [loginForm.account.data, get_md5(loginForm.passwd.data)])
            results = g.cur.fetchall()
            if len(results) == 1:
                session['logged_in'] = True
                session['user_id'] = results[0][0]
                session['username'] = results[0][1]
                session['aeskey'] = results[0][3]
                # set_cookie('user_id', results[0][0])
                # set_cookie('aeskey', results[0][3])
                flash('You were logged in')
                mylogger.info(str(session['user_id'])+": 登入成功")
                session['currentpage'] = 1

                user = User(session['user_id'])
                if loginForm.checkbox.data:
                    # login_user(user, remember=True)
                    session.permanent = True
                else:
                    # login_user(user)
                    session.permanent = False

                login_user(user)

                sql = "select nickname, sex, old, city, signature from roleinfo where user_id=%s"
                try:
                    statu = g.cur.execute(sql, [session['user_id']])
                    roleinfo = [dict(nickname=row[0], sex=row[1], old=row[2], city=row[3], signature=row[4]) for row in g.cur.fetchall()]
                    if len(roleinfo) >= 1:
                        session['roleinfo'] = roleinfo[0]
                    else:
                        session['roleinfo'] = [dict(nickname='default')]
                except Exception as e:
                    mylogger.error(str(e))
                    abort(401)

                return redirect(url_for('views.show_entries', currentpage=session['currentpage']))
            else:
                flash('Invalid username/password')
        except Exception as e:
            mylogger.error(str(e))
            g.db.rollback()
    return render_template('login.html', form=loginForm)

@views.route('/logout')
@login_required
def logout():
    mylogger.info(str(session['user_id'])+": 登出")
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('aeskey', None)
    session.pop('currentpage', None)
    session.pop('maxpage', None)
    session.pop('search', None)
    session.pop('searchkey', None)
    logout_user()
    flash('you are logged out')
    return redirect(url_for('views.login'))

@views.route('/roleinfo', methods=['POST'])
@login_required
def role_info():
    editroleinfoForm = EditroleinfoForm()
    sql = "select nickname, sex, old, city, signature from roleinfo where user_id=%s"
    sqlinsert = "insert into roleinfo (user_id, nickname, sex, old, city, signature) values (%s, %s, %s, %s, %s, %s)"
    sqlupdate = "update roleinfo set nickname=%s, sex=%s, old=%s, city=%s, signature=%s where user_id=%s"
    try:
        g.cur.execute(sql, [session['user_id']])
        roleinfo = [dict(nickname=row[0], sex=row[1], old=row[2], city=row[3], signature=row[4]) for row in g.cur.fetchall()]
        if len(roleinfo) >= 1:
            try:
                g.cur.execute(sqlupdate, [request.form.get('nickname') or roleinfo[0].nickname, \
                request.form.get('sex') or roleinfo[0]['sex'], request.form.get('old') or roleinfo[0]['old'] or 0, \
                request.form.get('city') or roleinfo[0]['city'], request.form.get('signature') or roleinfo[0]['signature'], session['user_id']])
                g.db.commit()
            except Exception as e:
                mylogger.error(str(e))
                g.db.rollback()
                abort(401)
        else:
            try:
                g.cur.execute(sqlinsert, [session['user_id'], request.form.get('nickname'), \
                request.form.get('sex'), request.form.get('old') or 0, request.form.get('city'), request.form.get('signature')])
                g.db.commit()
            except Exception as e:
                mylogger.error(str(e))
                g.db.rollback()
                abort(401)
    except Exception as e:
        mylogger.error(str(e))
        abort(401)
    return redirect(url_for('views.show_roleinfo'))

@views.route('/showroleinfo', methods=['GET'])
@login_required
def show_roleinfo():
    editroleinfoForm = EditroleinfoForm()
    sql = "select nickname, sex, old, city, signature from roleinfo where user_id=%s"
    try:
        statu = g.cur.execute(sql, [session['user_id']])
        roleinfo = [dict(nickname=row[0], sex=row[1], old=row[2], city=row[3], signature=row[4]) for row in g.cur.fetchall()]
        if len(roleinfo) >= 1:
            session['roleinfo'] = roleinfo[0]
        else:
            session['roleinfo'] = [dict(nickname='default')]
    except Exception as e:
        mylogger.error(str(e))
        abort(401)
    return render_template('editroleinfo.html', roleinfo=roleinfo, form=editroleinfoForm)

@views.route('/addarticle', methods=['POST', 'GET'])
@login_required
def add_article():
    form = AddArticleForm()
    if request.method == 'POST':
        sql = "insert into articles (user_id, title, article) values (%s, %s, %s)"
        try:
            title = form.title.data
            text = form.content.data
            g.cur.execute(sql, [session['user_id'], title, text])
            g.db.commit()
        except Exception as e:
            mylogger.error(str(e))
            g.db.rollback()
            abort(401)
        #print(text)
        # do something interesting with the Markdown text
        # allowed_tags=['a','ul','strong','p','h1','h2','h3']
        # html_body=markdown(text,output_format='html')
        # html_body=bleach.clean(html_body,tags=allowed_tags,strip=True)
        # html_body=bleach.linkify(html_body)
        #
        # pagedown = html_body
        # print(pagedown)

    return render_template('addarticle.html', form=form)

@views.route('/newlogin')
def newlogin():
    return render_template('newlogin.html')

@views.route('/markdown', methods=['POST', 'GET'])
def post():
    form = ContentForm()
    # if form.validate_on_submit():
    #     text = form.pagedown.data
    #     print(text)
    #     # do something interesting with the Markdown text
    #     # allowed_tags=['a','ul','strong','p','h1','h2','h3']
    #     # html_body=markdown(value,output_format='html')
    #     # html_body=bleach.clean(html_body,tags=allowed_tags,strip=True)
    #     # html_body=bleach.linkify(html_body)
    #
    #     pagedown = html_body
    #     print(pagedown)

    return render_template('markdown.html', form = form)

@views.errorhandler(404)
def page_not_found(error):
    abort('404')
