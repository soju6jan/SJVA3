# -*- coding: utf-8 -*-
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
from tool_base import ToolUtil
# 패키지
#########################################################


class P(object):
    package_name = __name__.split('.')[0]
    logger = get_logger(package_name)
    blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    plugin_info = {
        'version' : '0.2.0.0',
        'name' : package_name,
        'category' : 'beta',
        'icon' : '',
        'developer' : u'soju6jan',
        'description' : u'국내TV 파일처리 v2',
        'home' : 'https://github.com/soju6jan/%s' % package_name,
        'more' : '',
    }

    menu = {
        'main' : [package_name, u'국내TV v2'],
        'sub' : [
            ['basic', u'기본 처리'], ['finish', u'종영 처리'], ['log', u'로그']
        ], 
        'category' : plugin_info['category'],
        'sub2' : {
            'basic' : [
                ['setting', u'설정'], ['list', u'처리목록']
            ],
            'finish' : [
                ['setting', u'설정'], ['list', u'처리목록']
            ],
        }
    }  

    
    ModelSetting = get_model_setting(package_name, logger)
    logic = None
    module_list = None
    home_module = 'basic'


def initialize():
    try:
        app.config['SQLALCHEMY_BINDS'][P.package_name] = 'sqlite:///%s' % (os.path.join(path_data, 'db', '{package_name}.db'.format(package_name=P.package_name)))
        from framework.util import Util
        ToolUtil.save_dict(P.plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))

        from .ktv_basic import LogicKtvBasic
        #from .ktv_finish import LogicKtvFinish
        P.module_list = [LogicKtvBasic(P)]
        P.logic = Logic(P)
        default_route(P)
    except Exception as e: 
        P.logger.error('Exception:%s', e)
        P.logger.error(traceback.format_exc())


initialize()

