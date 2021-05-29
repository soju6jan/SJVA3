#########################################################
# python
import os, traceback

# third-party
import requests
from flask import Blueprint, request, send_file, redirect

# sjva 공용
from framework import app, path_data, check_api, py_urllib, SystemModelSetting
from framework.logger import get_logger
from framework.util import Util
from framework.common.plugin import get_model_setting, Logic, default_route

# 패키지
#########################################################

class P(object):
    package_name = __name__.split('.')[0]
    logger = get_logger(package_name)
    blueprint = Blueprint(package_name, package_name, url_prefix=f"/{package_name}", template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    menu = {
        'category' : 'system',
        'main' : [package_name, '모듈'],
        'sub' : [
            ['base', u'모듈 설정'], ['log', '로그']
        ], 
        'sub2' : {
            'base' : [
                ['setting', '설정'], ['total', '모듈 목록'],
            ],
        }
    }  

    ModelSetting = get_model_setting(package_name, logger)
    logic = None
    module_list = None
    home_module = 'base'

class ModLogic(Logic):
    def plugin_load(self):
        P.module_list[0].init_mod_list()
        super().plugin_load()

def initialize():
    try:
        app.config['SQLALCHEMY_BINDS'][P.package_name] = f"sqlite:///{os.path.join(path_data, 'db', f'{P.package_name}.db')}"
        
        from .mod_base import ModuleBase
        P.module_list = [ModuleBase(P)]
        P.logic = ModLogic(P)
        default_route(P)
    except Exception as e: 
        P.logger.error('Exception:%s', e)
        P.logger.error(traceback.format_exc())

initialize()

