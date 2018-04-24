# -*- coding:utf-8 -*-

import pymysql

def connectDB():
    db = pymysql.connect(host='localhost', user='fitrd',\
    passwd='123456', db='notesdb', use_unicode=True, charset='utf8')
    cur = db.cursor()
    return db, cur

def insertData(db, cur, data):
    sql = 'insert into entries (user_id, title, content) values\
     (2, "标题", "测试用");'
    status = cur.execute(sql)
    cur = db.commit()
    return status

def deleteData(db, cur, ids):
    sql = 'delete from entries where user_id=%s'
    for id in ids:
        print(id)
        cur.execute(sql %id)
    db.commit();

def connClose(db, cur):
    cur.close()
    db.close()

if __name__ == '__main__':
    db, cur = connectDB()
    insertData(db, cur, 'hello')
    #deleteData(conn, [1])
    connClose(db, cur)
