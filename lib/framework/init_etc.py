# -*- coding: utf-8 -*-
import os, traceback, sys

from datetime  import datetime, timedelta
from flask import request, abort
from functools import wraps

def check_api(original_function):
    @wraps(original_function)
    def wrapper_function(*args, **kwargs):  #1
        from framework import logger
        logger.debug('CHECK API... {} '.format(original_function.__module__))
        try:
            from system import ModelSetting as SystemModelSetting
            if SystemModelSetting.get_bool('auth_use_apikey'):
                if request.method == 'POST':
                    apikey = request.form['apikey']
                else:
                    apikey = request.args.get('apikey')
                #apikey = request.args.get('apikey')
                if apikey is None or apikey != SystemModelSetting.get('auth_apikey'):
                    logger.debug('CHECK API : ABORT no match ({})'.format(apikey))
                    logger.debug(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
                    abort(403)
                    return 
        except Exception as exception: 
            print('Exception:%s', exception)
            print(traceback.format_exc())
            logger.debug('CHECK API : ABORT exception')
            abort(403)
            return 
        return original_function(*args, **kwargs)  #2
    return wrapper_function


def make_default_dir(path_data):
    try:
        if not os.path.exists(path_data):
            os.mkdir(path_data)
        tmp = os.path.join(path_data, 'tmp')
        try:
            import shutil
            if os.path.exists(tmp):
                shutil.rmtree(tmp)
        except:
            pass
        sub = ['db', 'log', 'download', 'bin', 'download_tmp', 'command', 'custom', 'output', 'upload', 'tmp']
        for item in sub:
            tmp = os.path.join(path_data, item)
            if not os.path.exists(tmp):
                os.mkdir(tmp)
    except Exception as exception: 
        print('Exception:%s', exception)
        print(traceback.format_exc())
        


def pip_install():
    from framework import app
    try:
        import discord_webhook
    except:
        try: os.system("{} install discord-webhook".format(app.config['config']['pip']))
        except: pass

    try:
        from flask_cors import CORS
    except:
        try: os.system("{} install flask-cors".format(app.config['config']['pip']))
        except: pass

        
                    

def get_ip():
    headers_list = request.headers.getlist("X-Forwarded-For")
    return headers_list[0] if headers_list else request.remote_addr


def config_initialize(action):
    from . import logger, app

    if action == 'start':
        app.config['config']['server_url'] = 'https://server.sjva.me'
        app.config['config']['rss_subtitle_webhook'] = 'https://discordapp.com/api/webhooks/689800985887113329/GBTUBpP9L0dOegqL4sH-u1fwpssPKq0gBOGPb50JQjim22gUqskYCtj-wnup6BsY3vvc'

        app.config['config']['run_by_real'] = True if sys.argv[0] == 'sjva.py' or sys.argv[0] == 'sjva3.py' else False
        #app.config['config']['run_by_migration'] = True if sys.argv[-2] == 'db' else False
        app.config['config']['run_by_worker'] = True if sys.argv[0].find('celery') != -1 else False
        app.config['config']['run_by_init_db'] = True if sys.argv[-1] == 'init_db' else False
        if sys.version_info[0] == 2: 
            app.config['config']['pip'] = 'pip'
            app.config['config']['is_py2'] = True
            app.config['config']['is_py3'] = False
        else: 
            app.config['config']['is_py2'] = False
            app.config['config']['is_py3'] = True
            app.config['config']['pip'] = 'pip3'
        
        app.config['config']['is_debug'] = False
        app.config['config']['repeat'] = -1

        if app.config['config']['run_by_real']:
            try:
                if len(sys.argv) > 2:
                    app.config['config']['repeat'] = int(sys.argv[2])
            except:
                app.config['config']['repeat'] = 0
        if len(sys.argv) > 3:
            try:
                app.config['config']['is_debug'] = (sys.argv[-1] == 'debug')
            except:
                app.config['config']['is_debug'] = False
        app.config['config']['use_celery'] = True
        for tmp in sys.argv:
            if tmp == 'no_celery':
                app.config['config']['use_celery'] = False
                break
        #logger.debug('use_celery : %s', app.config['config']['use_celery'])
        logger.debug('======================================')
    elif action == 'auth':
        from system.logic_auth import SystemLogicAuth
        #SystemLogicAuth.do_auth()
        tmp = SystemLogicAuth.get_auth_status()
        app.config['config']['auth_status'] = tmp['ret']
        app.config['config']['auth_desc'] = tmp['desc']
        app.config['config']['level'] = tmp['level']
        app.config['config']['point'] = tmp['point']
        #app.config['config']['auth_status'] = True
    
    elif action == 'system_loading_after':
        from . import SystemModelSetting
        try: app.config['config']['is_server'] = (SystemModelSetting.get('ddns') == app.config['config']['server_url'])
        except: app.config['config']['is_server'] = False
        
        if app.config['config']['is_server'] or app.config['config']['is_debug']:
            app.config['config']['server'] = True
            app.config['config']['is_admin'] = True
        else:
            app.config['config']['server'] = False
            app.config['config']['is_admin'] = False
        app.config['config']['running_type'] = 'native'
        if 'SJVA_RUNNING_TYPE' in os.environ:
            app.config['config']['running_type'] = os.environ['SJVA_RUNNING_TYPE']
        else:
            import platform
            if platform.system() == 'Windows':
                app.config['config']['running_type'] = 'windows'



