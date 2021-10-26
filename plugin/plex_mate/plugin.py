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
from plugin import get_model_setting, Logic, default_route, PluginUtil

# 패키지
#########################################################


class P(object):
    package_name = __name__.split('.')[0]
    logger = get_logger(package_name)
    blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    menu = {
        'main' : [package_name, u'Plex Mate'],
        'sub' : [
            ['base', u'설정'], ['clear', u'파일 정리'], ['tool', 'DB 툴'],  ['periodic', '라이브러리 주기적 스캔'], ['scan', '스캔(개발중)'], ['watchdog', '파일시스템 감시(개발중)'], ['dbcopy', '라이브러리 복사'],['manual', '매뉴얼'], ['log', u'로그']
        ], 
        'category' : 'beta',
        'sub2' : {
            'base' : [
                ['setting', '설정']
            ],
            'clear' : [
                ['movie', '영화 정리'], ['show', 'TV 정리'], ['music', '음악 정리'], ['bundle', '번들 삭제'], ['cache', '캐시(PhotoTranscoder) 삭제'], 
            ],
            'tool' : [
                ['simple', '간단 명령'], ['select', 'DB Select'], ['query', 'SQL Query'],
            ],
            'periodic' : [
                ['task', '작업 관리'], ['list', '스캔 결과']
            ],
            'scan' : [
                ['manual', '수동'], ['auto', '자동'], ['list', '목록'],
            ],
            'watchdog' : [
                ['setting', '설정'], ['list', '목록'],
            ],
            'dbcopy' : [
                ['make', '소스 DB 생성'], ['copy', '복사 설정'], ['status', '복사 상태'],
            ],
            'manual' : [
                ['README.md', 'README'], ['file/파일정리.md', '파일정리'], 
                ['file/라이브러리 복사.md', '라이브러리 복사'],
                ['file/스캔.md', 'PLEX 스캔'], ['file/라이브러리 주기적 스캔.md', '라이브러리 주기적 스캔']
            ],
        }
    }  

    plugin_info = {
        'version' : '0.2.0.0',
        'name' : package_name,
        'category' : menu['category'],
        'icon' : '',
        'developer' : u'soju6jan',
        'description' : u'Plex Mate',
        'home' : 'https://github.com/soju6jan/%s' % package_name,
        'more' : '',
        #'policy_level' : 10,
    }
    ModelSetting = get_model_setting(package_name, logger)
    logic = None
    module_list = None
    home_module = 'server'


def initialize():
    try:
        app.config['SQLALCHEMY_BINDS'][P.package_name] = 'sqlite:///%s' % (os.path.join(path_data, 'db', '{package_name}.db'.format(package_name=P.package_name)))
        PluginUtil.make_info_json(P.plugin_info, __file__)

        from .logic_pm_base import LogicPMBase
        from .logic_pm_clear import LogicPMClear
        from .logic_pm_tool import LogicPMTool
        from .logic_pm_periodic import LogicPMPeriodic
        from .logic_pm_dbcopy import LogicPMDbCopy
        from .logic_pm_scan import LogicPMScan
        from .logic_pm_watchdog import LogicPMWatchdog
        P.module_list = [LogicPMBase(P), LogicPMClear(P), LogicPMPeriodic(P), LogicPMTool(P), LogicPMDbCopy(P), LogicPMScan(P), LogicPMWatchdog(P)]
        P.logic = Logic(P)
        default_route(P)
    except Exception as e: 
        P.logger.error('Exception:%s', e)
        P.logger.error(traceback.format_exc())


initialize()

