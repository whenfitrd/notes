#! /usr/bin/env python3
#coding=utf-8

import logging
import logging.config
import logging.handlers
import os

standard_format = '[%(asctime)s][%(threadName)s:%(thread)d][%(name)s][%(filename)s:%(lineno)d]' \
                  '[%(levelname)s][%(message)s]' #其中name为getlogger指定的名字
simple_format = '[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d]%(message)s'
id_simple_format = '[%(levelname)s][%(asctime)s] %(message)s'

logfile_dir = os.path.dirname(os.path.abspath('log/all.log'))  # log文件的目录

logfile_name = 'all.log'  # log文件名
errorfile_name = 'error.log'

if not os.path.isdir(logfile_dir):
    os.mkdir(logfile_dir)

logfile_path = os.path.join(logfile_dir, logfile_name)
errorlog_path = os.path.join(logfile_dir, errorfile_name)

LOGGING_DIC = {
    'version': 1.0,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': standard_format
        },
        'simple': {
            'format': simple_format
        },
        'id_simple': {
            'format': id_simple_format
        },
    },
    'filters': {},
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': logfile_path,
            'maxBytes': 1024*1024*5, #日志大小５M
            'backupCount': 5, #日志备份数量
            'encoding': 'utf-8', #日志文件的编码
        },
        'simpleerrorfile': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'id_simple',
            'filename': errorlog_path,
            'maxBytes': 1024*1024*5, #日志大小５M
            'backupCount': 5, #日志备份数量
            'encoding': 'utf-8', #日志文件的编码
        },
    },
    'loggers': {
        #logging.getLogger(__name__)拿到的配置
        '': {
            'handlers': ['file', 'console', 'simpleerrorfile'],
            'level': 'DEBUG',
            'propagate': True, #向更高level的logger传递
        },
    },
}

class Logger(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        logging.config.dictConfig(LOGGING_DIC)

    def getLogger(self):
        return logging.getLogger(__name__)

if __name__ == '__main__':
    logger = Logger().getLogger()
    logger.error('error info')
    logger = Logger().getLogger()
    logger.error('error3 info')
