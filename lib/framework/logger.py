# -*- coding: utf-8 -*-
import os
import logging
import logging.handlers
from datetime import datetime
from framework import path_data
from pytz import timezone, utc

"""
def logger_init(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # formmater 생성
    formatter = logging.Formatter(u'[%(asctime)s|%(levelname)s|%(filename)s:%(lineno)s]  : %(message)s')
    formatter2 = logging.Formatter(u'[%(levelname)s|%(filename)s:%(lineno)s]  : %(message)s'.encode('cp949')) 

    # fileHandler와 StreamHandler를 생성
    file_max_bytes = 10 * 1024 * 1024 
    fileHandler = logging.handlers.RotatingFileHandler(filename=os.path.join(framework.path_data, 'log', '%s.log' % name), maxBytes=file_max_bytes, backupCount=5, encoding='utf8')
    streamHandler = logging.StreamHandler() 

    # handler에 fommater 세팅 
    fileHandler.setFormatter(formatter)
    #streamHandler.setFormatter(formatter) 
    
    # Handler를 logging에 추가
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
"""

#system_loading = False
level_unset_logger_list = []
logger_list = []

def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        #global system_loading
        global level_unset_logger_list
        global logger_list
        level = logging.DEBUG
        from framework import flag_system_loading 
        try:
            """
            if not system_loading:
                if name == 'system':
                    system_loading = True
                level_unset_logger_list.append(logger)
            else:
                try:
                    from system.model import ModelSetting as SystemModelSetting
                    level = SystemModelSetting.get('log_level')
                    level = int(level)
                except:
                    level = logging.DEBUG

                if level_unset_logger_list is not None:
                    for item in level_unset_logger_list:
                        item.setLevel(level)
                    level_unset_logger_list = None
            logger_list.append(logger)
            """
            if flag_system_loading:
                try:
                    from system.model import ModelSetting as SystemModelSetting
                    level = SystemModelSetting.get('log_level')
                    level = int(level)
                except:
                    level = logging.DEBUG
                if level_unset_logger_list is not None:
                    for item in level_unset_logger_list:
                        item.setLevel(level)
                    level_unset_logger_list = None
            else:
                level_unset_logger_list.append(logger)
                 
        except:
            pass
        logger.setLevel(level)
        # formmater 생성
        #formatter = logging.Formatter(u'[%(asctime)s|%(levelname)s|%(pathname)s:%(lineno)s] %(message)s')
        formatter = logging.Formatter(u'[%(asctime)s|%(levelname)s|%(filename)s:%(lineno)s] %(message)s')
        #formatter2 = logging.Formatter(u'[%(levelname)s|%(filename)s:%(lineno)s]  : %(message)s'.encode('cp949')) 
        def customTime(*args):
            utc_dt = utc.localize(datetime.utcnow())
            my_tz = timezone("Asia/Seoul")
            converted = utc_dt.astimezone(my_tz)
            return converted.timetuple()

        formatter.converter = customTime

        # fileHandler와 StreamHandler를 생성
        #file_max_bytes = 10 * 1024 * 1024 
        file_max_bytes = 1 * 1024 * 1024 
        fileHandler = logging.handlers.RotatingFileHandler(filename=os.path.join(path_data, 'log', '%s.log' % name), maxBytes=file_max_bytes, backupCount=5, encoding='utf8', delay=True)
        streamHandler = logging.StreamHandler() 

        

        # handler에 fommater 세팅 
        fileHandler.setFormatter(formatter)
        streamHandler.setFormatter(formatter) 
        
        # Handler를 logging에 추가
        logger.addHandler(fileHandler)
        logger.addHandler(streamHandler)
    return logger

get_logger('apscheduler.scheduler')
get_logger('apscheduler.executors.default')

def set_level(level):
    global logger_list
    try:
        for l in logger_list:
            l.setLevel(level)
    except:
        pass    
