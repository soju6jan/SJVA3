# -*- coding: utf-8 -*-
import io
import traceback
import platform

from framework import app, logger

def is_arm():
    try:
        ret = False
        import platform
        if platform.system() == 'Linux':
            if platform.platform().find('86') == -1 and platform.platform().find('64') == -1:
                ret = True
            if platform.platform().find('arch') != -1:
                ret = True
            if platform.platform().find('arm') != -1:
                ret = True
        return ret
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def is_native():
    try:
        return (app.config['config']['running_type'] == 'native')
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def is_termux():
    try:
        return (app.config['config']['running_type'] == 'termux')
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def is_windows():
    try:
        return (app.config['config']['running_type'] == 'native' and platform.system() == 'Windows')
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def is_mac():
    try:
        return (app.config['config']['running_type'] == 'native' and platform.system() == 'Darwin')
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def is_docker():
    try:
        return (app.config['config']['running_type'] == 'docker')
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def is_linux():
    try:
        #return (app.config['config']['running_type'] == 'native' and platform.system() == 'Linux')
        return (platform.system() == 'Linux')
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
        