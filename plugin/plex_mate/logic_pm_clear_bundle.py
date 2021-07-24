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


from .task_pm_clear_bundle import Task
from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
#########################################################



class LogicPMClearBundle(LogicSubModuleBase):
    
    def __init__(self, P, parent, name):
        super(LogicPMClearBundle, self).__init__(P, parent, name)
        self.db_default = {
            f'{self.parent.name}_{self.name}_db_version' : '1',
            f'{self.parent.name}_{self.name}_task_stop_flag' : 'False',
        }
        self.data = {
            'list' : [],
            'status' : {'is_working':'wait'}
        }
        self.list_max = 300
        default_route_socketio_sub(P, parent, self)


    def process_ajax(self, sub, req):
        try:
            ret = {}
            if sub == 'command':
                command = req.form['command']
                logger.error(f"sub : {sub}  /  command : {command}")
                if command == 'start':
                    if self.data['status']['is_working'] == 'run':
                        ret = {'ret':'warning', 'msg':'실행중입니다.'}
                    else:
                        tmp = req.form['arg1'].split('_')
                        self.task_interface(tmp[0], tmp[1], tmp[2], req.form['arg2'])
                        ret = {'ret':'success', 'msg':'작업을 시작합니다.'}
                elif command == 'stop':
                    if self.data['status']['is_working'] == 'run':
                        ModelSetting.set(f'{self.parent.name}_{self.name}_task_stop_flag', 'True')
                        ret = {'ret':'success', 'msg':'잠시 후 중지됩니다.'}
                    else:
                        ret = {'ret':'warning', 'msg':'대기중입니다.'}
                elif command == 'refresh':
                    self.refresh_data()
            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
    

    #########################################################

    def task_interface(self, *args):
        logger.warning(args)
        def func():
            time.sleep(1)
            self.task_interface2(*args)
        th = threading.Thread(target=func, args=())
        th.setDaemon(True)
        th.start()


    def task_interface2(self, *args):
        logger.warning(args)
        
        self.data['list'] = []
        self.data['status']['is_working'] = 'run'
        self.refresh_data()
        ModelSetting.set(f'{self.parent.name}_{self.name}_task_stop_flag', 'False')

        #func(*args)
        #return
        try:
            if app.config['config']['use_celery']:
                result = Task.start.apply_async(args)
                ret = result.get(on_message=self.receive_from_task, propagate=True)
            else:
                ret = Task.start(self, *args)
            self.data['status']['is_working'] = ret
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            self.data['status']['is_working'] = 'exception'

        
        self.refresh_data()


    def refresh_data(self, index=-1):
        if index == -1:
            self.socketio_callback('refresh_all', self.data)
        else:
            self.socketio_callback('refresh_one', {'one' : self.data['list'][index], 'status' : self.data['status']})
        

    def receive_from_task(self, arg, celery=True):
        try:
            result = None
            if celery:
                if arg['status'] == 'PROGRESS':
                    result = arg['result']
            else:
                result = arg
            if result is not None:
                self.data['status'] = result['status']
                #logger.warning(result)
                del result['status']
                #logger.warning(result)
                if self.list_max != 0:
                    if len(self.data['list']) == self.list_max:
                        self.data['list'] = []
                result['index'] = len(self.data['list'])
                self.data['list'].append(result)
                self.refresh_data(index=result['index'])
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())