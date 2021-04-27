# -*- coding: utf-8 -*-
import os
import logging
import logging.handlers
from datetime import datetime
from framework import path_data
from pytz import timezone, utc

#from colorlog import ColoredFormatter

class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    #format = "[%(asctime)s|%(name)s|%(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    format = u'[%(asctime)s|%(levelname)s|%(name)s:%(filename)s:%(lineno)s] %(message)s'

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)





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
        formatter = logging.Formatter(u'[%(asctime)s|%(levelname)s|%(filename)s:%(lineno)s] %(message)s')
        def customTime(*args):
            utc_dt = utc.localize(datetime.utcnow())
            my_tz = timezone("Asia/Seoul")
            converted = utc_dt.astimezone(my_tz)
            return converted.timetuple()

        formatter.converter = customTime
        file_max_bytes = 1 * 1024 * 1024 
        fileHandler = logging.handlers.RotatingFileHandler(filename=os.path.join(path_data, 'log', '%s.log' % name), maxBytes=file_max_bytes, backupCount=5, encoding='utf8', delay=True)
        streamHandler = logging.StreamHandler() 


        # handler에 fommater 세팅 
        fileHandler.setFormatter(formatter)
        streamHandler.setFormatter(CustomFormatter()) 
        
        # Handler를 logging에 추가
        logger.addHandler(fileHandler)
        logger.addHandler(streamHandler)
    return logger

get_logger('apscheduler.scheduler')
get_logger('apscheduler.executors.default')

try: logging.getLogger('socketio').setLevel(logging.ERROR)
except: pass

try: logging.getLogger('engineio').setLevel(logging.ERROR)
except: pass

try: logging.getLogger('apscheduler.scheduler').setLevel(logging.ERROR)
except: pass
try: logging.getLogger('apscheduler.scheduler.default').setLevel(logging.ERROR)
except: pass
try: logging.getLogger('werkzeug').setLevel(logging.ERROR)
except: pass

def set_level(level):
    global logger_list
    try:
        for l in logger_list:
            l.setLevel(level)
    except:
        pass    
