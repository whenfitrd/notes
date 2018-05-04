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

@views.route('/showentries', methods=['GET'])
@views.route('/showentries/<int:currentpage>', methods=['GET'])
def show_entries(currentpage=1):
    if not session.get('logged_in') or not session.get('user_id') or not session.get('aeskey'):
        return render_template('login.html')

    if session.get('search') and session.get('entries') and session['search']:
        entries = session['entries']
        session['maxpage'] = (len(entries)-1)//5+1
        return render_template('showentries.html', entries=entries, currentpage=currentpage, maxpage=session['maxpage'])

    sql = "select id, title, content, createtime from entries where user_id=%s order by id desc"
    try:
        statu = g.cur.execute(sql, str(session['user_id']))
        entries = [dict(id=row[0], title=decrypt(row[1], session['aeskey']).decode('utf-8'),\
        text=decrypt(row[2], session['aeskey']).decode('utf-8'), createtime=row[3])\
        for row in g.cur.fetchall()]
    except Exception as e:
        mylogger.error(str(e))
        abort(401)
    session['maxpage'] = (len(entries)-1)//5+1
    return render_template('showentries.html', entries=entries, currentpage=currentpage, maxpage=session['maxpage'])

@views.route('/prepage', methods=['GET'])
def pre_page():
    if not session.get('logged_in') or not session.get('user_id') or not session.get('aeskey'):
        return render_template('login.html')

    if session['currentpage'] > 1:
        session['currentpage'] -= 1
    return redirect(url_for('views.show_entries', currentpage=session['currentpage']))

@views.route('/nextpage', methods=['GET'])
def next_page():
    if not session.get('logged_in') or not session.get('user_id') or not session.get('aeskey'):
        return render_template('login.html')

    if session['currentpage'] < session['maxpage']:
        session['currentpage'] += 1
    return redirect(url_for('views.show_entries', currentpage=session['currentpage']))

@views.route('/search', methods=['POST'])
def search():
    if not session.get('logged_in') or not session.get('user_id') or not session.get('aeskey'):
        return render_template('login.html')

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
def add_entry():
    if request.method == 'POST':
        if not session.get('logged_in') or not session.get('user_id') or not session.get('aeskey'):
            return render_template('login.html')

        try:
            g.cur.execute('insert into entries (user_id, title, content) values (%s, %s, %s)',\
            [str(session['user_id']), encrypt(request.form['title'], session['aeskey']), encrypt(request.form['text'], session['aeskey'])])
            g.db.commit()
        except Exception as e:
            mylogger.error(str(e))
            g.db.rollback()
            return render_template('addentry.html')
        flash('提交成功')
        return redirect(url_for('views.show_entries', currentpage=session['currentpage']))
    return render_template('addentry.html')

@views.route('/editentry', methods=['POST'])
def update_entry():
    if not session.get('logged_in') or not session.get('user_id') or not session.get('aeskey'):
        return render_template('login.html')

    sql = "update entries set title=%s, content=%s where id=%s"
    try:
        g.cur.execute(sql, [encrypt(request.form['title'], session['aeskey']), encrypt(request.form['text'], session['aeskey']), request.form['id']])
        g.db.commit()
    except Exception as e:
        mylogger.error(str(e))
        g.db.rollback()
    return redirect(url_for('views.show_entries', currentpage=session['currentpage']))

@views.route('/editentry/<int:id>', methods=['GET'])
def edit_entry(id):
    if not session.get('logged_in') or not session.get('user_id') or not session.get('aeskey'):
        return render_template('login.html')

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
    if not session.get('logged_in') or not session.get('user_id') or not session.get('aeskey'):
        return render_template('login.html')

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
                session['username'] = results[0][1]
                session['aeskey'] = results[0][3]
                flash('You were logged in')
                mylogger.info(str(session['user_id'])+": 登入成功")
                session['currentpage'] = 1

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
    return render_template('login.html')

@views.route('/logout')
def logout():
    mylogger.info(str(session['user_id'])+": 登出")
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('aeskey', None)
    session.pop('currentpage', None)
    session.pop('maxpage', None)
    session.pop('search', None)
    session.pop('searchkey', None)
    flash('you are logged out')
    return redirect(url_for('views.login'))

@views.route('/roleinfo', methods=['POST'])
def role_info():
    if not session.get('logged_in') or not session.get('user_id') or not session.get('aeskey'):
        return render_template('login.html')

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
def show_roleinfo():
    if not session.get('logged_in') or not session.get('user_id') or not session.get('aeskey'):
        return render_template('login.html')

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
    return render_template('editroleinfo.html', roleinfo=roleinfo)


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
