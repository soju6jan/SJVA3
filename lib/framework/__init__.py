# -*- coding: utf-8 -*-
version = '0.2.22.1'
#########################################################
# python
import os
import sys
import platform
path_app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
path_data = os.path.join(path_app_root, 'data')
flag_system_loading = False

from datetime  import datetime, timedelta
import json
import traceback
# third-party

from flask import Flask, redirect, render_template, Response, request, jsonify, send_file, send_from_directory, abort, Markup
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit 
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

#from celery import Celery

# sjva 공용
from .init_args import args
from .py_version_func import *
from framework.class_scheduler import Scheduler
from framework.logger import get_logger
from .menu import init_menu, get_menu_map
from .user import User
from .init_web import jinja_initialize
from .init_etc import check_api, make_default_dir, pip_install, config_initialize

#########################################################
# App 시작
#########################################################

## 기본디렉토리 생성
make_default_dir(path_data)

package_name = __name__.split('.')[0]

logger = get_logger(package_name)

try:
    # Global
    logger.debug('Path app root : %s', path_app_root)     
    logger.debug('Path app data : %s', path_data) 
    logger.debug('Platform : %s', platform.system())

    app = Flask('sjva')

    #try:
    #    from flask_restful import Api
    #    api = Api(app)
    #except:
    #    logger.debug('NOT INSTALLED FLASK_RESTFUL')

    app.secret_key = os.urandom(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/db/sjva.db?check_same_thread=False'
    app.config['SQLALCHEMY_BINDS'] = {'sjva':'sqlite:///data/db/sjva.db'}
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['config'] = {}
    
    config_initialize('start')

    pip_install()

    db = SQLAlchemy(app, session_options={"autoflush": False})

    scheduler = Scheduler(args)

    #socketio = SocketIO(app, cors_allowed_origins="*") #, async_mode='gevent')
    if args is not None and args.use_gevent == False:
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    else:
        socketio = SocketIO(app, cors_allowed_origins="*") #, async_mode='gevent')

    from flask_cors import CORS
    CORS(app)

    from flaskext.markdown import Markdown
    Markdown(app)


    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    exit_code = -1
   
    # app route가 되어 있는데 import 해야지만 routing이 됨
    from .log_viewer import *
    from .manual import *
    
    # 추후 삭제
    USERS = {"sjva"+version : User("sjva"+version, passwd_hash="sjva"+version),}
    
    
    
    ##########################################
    from .init_celery import celery
    import framework.common.celery

    ##########################################
    # 시스템 플러그인
    # 시스템 DB부터 만들자.
    import system
    from system.model import ModelSetting as SystemModelSetting
    # epg 없이 klive 만 있고 db 파일이 없을 때 아예 다른 모듈이 로딩안되는 문제 발생
    # klive에서 epg 칼럼을 참조해서 그러는것 같음. 방어코드이나 확인못함
    try:
        db.create_all()
    except Exception as exception:
        logger.error('CRITICAL db.create_all()!!!')
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
    
    config_initialize('auth')

    system.plugin_load()
    flag_system_loading = True # 로그레벨에서 사용. 필요한가??

    
    app.register_blueprint(system.blueprint)

    config_initialize('system_loading_after')

    ################################################################
    # 아래는 코드 동작.. 위는 import만
    plugin_menu = []
    plugin_menu.append(system.menu)
    plugin_instance_list = {}

    jinja_initialize(app)
    

    ######################################################
    # 플러그인
    system.LogicPlugin.custom_plugin_update()
    from .init_plugin import plugin_init
    plugin_init()
    
    logger.debug('### plugin loading completed')            
    #####################################################
    # 메뉴
    init_menu(plugin_menu)
    system.SystemLogic.apply_menu_link()
    logger.debug('### menu loading completed')

    logger.debug("### init app.config['config]")
    app.config['config']['port'] = 0
    if sys.argv[0] == 'sjva.py' or sys.argv[0] == 'sjva3.py':
        try:
            app.config['config']['port'] = SystemModelSetting.get_int('port')
            if app.config['config']['port'] == 19999 and app.config['config']['running_type'] == 'docker' and not os.path.exists('/usr/sbin/nginx'):
                SystemModelSetting.set('port', '9999')
                app.config['config']['port'] = 9999
        except:
            app.config['config']['port'] = 9999
    
    if args is not None:
        if args.port is not None:
            app.config['config']['port'] = args.port
        app.config['config']['repeat'] = args.repeat        
        app.config['config']['use_celery'] = args.use_celery
        if platform.system() == 'Windows':
            app.config['config']['use_celery'] = False
        app.config['config']['use_gevent'] = args.use_gevent
    logger.debug('### config ###')
    logger.debug(json.dumps(app.config['config'], indent=4))

    logger.debug('### LAST')
    logger.debug('### PORT:%s', app.config['config']['port'])
    logger.debug('### Now you can access SJVA by webbrowser!!')
    
    

except Exception as exception:
    logger.error('Exception:%s', exception)
    logger.error(traceback.format_exc())


# 반드시 마지막에 
#import init_route
from .init_route import *

