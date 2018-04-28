#! /usr/bin/env python3
#coding=utf-8

from flask import render_template, request, g, session, redirect,\
    abort, flash, url_for
import pymysql

from crypto import get_md5, encrypt, decrypt, get_aeskey

from flask import Blueprint

#from markdown import markdown
#import bleach

from forms import ContentForm

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
    return render_template('login.html')

@views.route('/showentries')
def show_entries():
    if not session.get('logged_in'):
        abort(401)
    if not session.get('user_id'):
        abort(401)
    if not session.get('aeskey'):
        abort(401)
    sql = "select id, title, content, createtime from entries where user_id=%s order by id desc"
    try:
        statu = g.cur.execute(sql, str(session['user_id']))
        entries = [dict(id=row[0], title=decrypt(row[1], session['aeskey']).decode('utf-8'),\
        text=decrypt(row[2], session['aeskey']).decode('utf-8'), createtime=row[3])\
        for row in g.cur.fetchall()]
    except Exception as e:
        mylogger.error(str(e))
        abort(401)
    return render_template('showentries.html', entries=entries)

@views.route('/addentry', methods=['POST', 'GET'])
def add_entry():
    if request.method == 'POST':
        if not session.get('logged_in'):
            abort(401)
        if not session.get('aeskey'):
            abort(401)
        try:
            g.cur.execute('insert into entries (user_id, title, content) values (%s, %s, %s)',\
            [str(session['user_id']), encrypt(request.form['title'], session['aeskey']), encrypt(request.form['text'], session['aeskey'])])
            g.db.commit()
        except Exception as e:
            mylogger.error(str(e))
            g.db.rollback()
            return render_template('addentry.html')
        flash('提交成功')
        return redirect(url_for('views.show_entries'))
    return render_template('addentry.html')

@views.route('/editentry', methods=['POST'])
def update_entry():
    if not session.get('logged_in'):
        abort(401)
    if not session.get('aeskey'):
        abort(401)
    sql = "update entries set title=%s, content=%s where id=%s"
    try:
        g.cur.execute(sql, [encrypt(request.form['title'], session['aeskey']), encrypt(request.form['text'], session['aeskey']), request.form['id']])
        g.db.commit()
    except Exception as e:
        mylogger.error(str(e))
        g.db.rollback()
    return redirect(url_for('views.show_entries'))

@views.route('/editentry/<int:id>', methods=['GET'])
def edit_entry(id):
    if not session.get('logged_in'):
        abort(401)
    if not session.get('aeskey'):
        abort(401)
    sql = "select id, title, content, createtime from entries where id=%s"
    try:
        statu = g.cur.execute(sql, [id])
        entries = [dict(id=row[0], title=decrypt(row[1], session['aeskey']).decode('utf-8'),\
        text=decrypt(row[2], session['aeskey']).decode('utf-8'), createtime=row[3])\
        for row in g.cur.fetchall()]
    except Exception as e:
        mylogger.error(str(e))
        abort(401)
    return render_template('addentry.html', entry=entries[0])

@views.route('/del/<int:id>', methods=['GET'])
def del_entry(id):
    if not session.get('logged_in'):
        abort(401)
    if not session.get('aeskey'):
        abort(401)
    try:
        g.cur.execute('delete from entries where id=%s', [id])
        g.db.commit()
        flash('删除成功')
    except Exception as e:
        mylogger.error(str(e))
        g.db.rollback()
    return redirect(url_for('views.show_entries'))

@views.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        sql = "INSERT INTO users(username, password, aeskey) VALUES (%s, %s, %s)"
        if request.form.get('password') != request.form.get('repetition'):
            flash('输入的两次密码不相同')
            return render_template('register.html')
        try:
            g.cur.execute(sql, [request.form.get('username'), get_md5(request.form.get('password')), get_aeskey()])
            g.db.commit()
            return render_template('login.html')
        except Exception as e:
            mylogger.error(str(e))
            g.db.rollback()
            flash('注册失败')
    return render_template('register.html')

@views.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        sql = "select * from users where username=%s and password=%s"
        try:
            g.cur.execute(sql, [request.form.get('username'), get_md5(request.form.get('password'))])
            results = g.cur.fetchall()
            if len(results) == 1:
                session['logged_in'] = True
                session['user_id'] = results[0][0]
                session['aeskey'] = results[0][3]
                flash('You were logged in')
                mylogger.info(str(session['user_id'])+": 登入成功")
                return redirect(url_for('views.show_entries'))
            else:
                flash('Invalid username/password')
        except Exception as e:
            mylogger.error(str(e))
            g.db.rollback()
    return render_template('login.html')

@views.route('/logout')
def logout():
    mylogger.info(str(session['user_id'])+": 登出")
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('aeskey', None)
    flash('you are logged out')
    return redirect(url_for('views.login'))

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
