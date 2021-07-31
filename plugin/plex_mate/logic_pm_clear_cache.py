# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, re, json, threading, time, shutil, platform
from datetime import datetime
# third-party
import requests, xmltodict
from flask import request, render_template, jsonify, redirect
# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from plugin import default_route_socketio_sub, LogicSubModuleBase
from tool_base import ToolBaseFile, d, ToolSubprocess
# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting


from .task_pm_clear_movie import Task as TaskMovie
from .task_pm_clear_show import Task as TaskShow
from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
from .logic_pm_base import LogicPMBase
#########################################################

class LogicPMClearCache(LogicSubModuleBase):
    def __init__(self, P, parent, name):
        super(LogicPMClearCache, self).__init__(P, parent, name)
        self.db_default = {
            f'{self.parent.name}_{self.name}_db_version' : '1',
            f'{self.parent.name}_{self.name}_auto_start' : 'False',
            f'{self.parent.name}_{self.name}_interval' : '0 5 * * *',
            f'{self.parent.name}_{self.name}_max_size' : '20',
        }
        self.scheduler_desc = 'Plex PhotoTranscoder 삭제 스케쥴링'


    def process_ajax(self, sub, req):
        try:
            ret = {}
            if sub == 'command':
                command = req.form['command']
                if command == 'cache_size':
                    self.P.logic.get_module('base').task_interface('size', (ModelSetting.get('base_path_phototranscoder'),))
                    ret = {'ret':'success', 'msg':'명령을 전달하였습니다. 잠시 후 결과 알림을 확인하세요.'}
                elif command == 'cache_clear':
                    self.P.logic.get_module('base').task_interface('clear', (ModelSetting.get('base_path_phototranscoder'),))
                    ret = {'ret':'success', 'msg':'명령을 전달하였습니다. 잠시 후 결과 알림을 확인하세요.'}
            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})

    def scheduler_function(self):
        logger.error('scheduler_function')
    
    def plugin_load(self):
        logger.error('plugin_load')
    
    def plugin_unload(self):
        logger.error('plugin_unload')
    #########################################################

    