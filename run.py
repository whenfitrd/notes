#! /usr/bin/env python3
#coding=utf-8

from __init__ import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, threaded=True, host='0.0.0.0')
