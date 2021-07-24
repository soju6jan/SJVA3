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

# 패키지
#########################################################


class P(object):
    package_name = __name__.split('.')[0]
    logger = get_logger(package_name)
    blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    menu = {
        'main' : [package_name, u'PLEX Mate'],
        'sub' : [
            ['base', u'설정'], ['clear', u'파일 정리'], ['tool', 'DB 툴'], ['manual', '매뉴얼'], ['log', u'로그']
        ], 
        'category' : 'beta',
        'sub2' : {
            'base' : [
                ['setting', '설정']
            ],
            'clear' : [
                ['movie', '영화 정리'], ['show', '쇼 정리'], ['bundle', '번들 삭제'], ['cache', '캐시(PhotoTranscoder) 삭제'], 
            ],
            'tool' : [
                ['simple', '간단 명령'], ['show', '컬렉션 삭제'], ['cache', 'PhotoTranscoder'], ['bundle', '번들제거']
            ]
        }
    }  

    plugin_info = {
        'version' : '0.2.0.0',
        'name' : package_name,
        'category_name' : 'beta',
        'icon' : '',
        'developer' : u'soju6jan',
        'description' : u'PLEX Mate',
        'home' : 'https://github.com/soju6jan/%s' % package_name,
        'more' : '',
        'policy_level' : 10,
    }
    ModelSetting = get_model_setting(package_name, logger)
    logic = None
    module_list = None
    home_module = 'server'


def initialize():
    try:
        app.config['SQLALCHEMY_BINDS'][P.package_name] = 'sqlite:///%s' % (os.path.join(path_data, 'db', '{package_name}.db'.format(package_name=P.package_name)))
        from framework.util import Util
        Util.save_from_dict_to_json(P.plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))

        from .logic_pm_base import LogicPMBase
        from .logic_pm_clear import LogicPMClear
        from .logic_pm_tool import LogicPMTool
        P.module_list = [LogicPMBase(P), LogicPMClear(P), LogicPMTool(P)]
        P.logic = Logic(P)
        default_route(P)
    except Exception as e: 
        P.logger.error('Exception:%s', e)
        P.logger.error(traceback.format_exc())


initialize()

