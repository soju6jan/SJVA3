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


from .task_pm_thumb_movie import Task as TaskThumbMovie
from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
#########################################################



class LogicPMClearLibrary(LogicSubModuleBase):
    
    def __init__(self, P, parent, name):
        super(LogicPMClearLibrary, self).__init__(P, parent, name)
        self.db_default = {
            f'{self.parent.name}_{self.name}_db_version' : '1',
            f'{self.parent.name}_{self.name}_task_stop_flag' : 'False',
            f'{self.parent.name}_{self.name}_path_config_yaml' : os.path.join(path_data, 'db', f'{package_name}_{self.parent.name}_{self.name}.yaml')
        }
        self.data = {
            'list' : [],
            'status' : {'is_working':'wait'}
        }
        default_route_socketio_sub(P, parent, self)


    def process_ajax(self, sub, req):
        try:
            ret = {}
            if sub == 'command':
                command = req.form['command']
                logger.error(f"sub : {sub}  /  command : {command}")
                if command.startswith('start'):
                    if self.data['status']['is_working'] == 'run':
                        ret = {'ret':'warning', 'msg':'실행중입니다.'}
                    else:
                        self.task_interface(command, req.form['arg1'], req.form['arg2'])
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
    
    def plugin_load(self):
        config_path = ModelSetting.get(f'{self.parent.name}_{self.name}_path_config_yaml')
        logger.error(config_path)
        if os.path.exists(config_path) == False:
            shutil.copyfile(os.path.join(os.path.dirname(__file__), 'file', os.path.basename(config_path)), config_path)

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
        #if sub == 'movie':
        library_section = PlexDBHandle.library_section(args[1])
        #logger.warning(d(library_section))
        self.data['list'] = []
        self.data['status']['is_working'] = 'run'
        self.refresh_data()
        ModelSetting.set(f'{self.parent.name}_{self.name}_task_stop_flag', 'False')
        try:
            if library_section['section_type'] == 1:
                func = TaskThumbMovie.start
                config = TaskThumbMovie.load_config()
            elif library_section['section_type'] == 2:
                func = TaskThumbShow.start
            try:
                self.list_max = config['웹페이지에 표시할 세부 정보 갯수']
            except:
                self.list_max = 200
            #func(*args)
            #return
            if app.config['config']['use_celery']:
                result = func.apply_async(args)
                ret = result.get(on_message=self.receive_from_task, propagate=True)
            else:
                ret = func(self, *args)
            self.data['status']['is_working'] = ret
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            self.data['status']['is_working'] = 'wait'
        self.refresh_data()


    def refresh_data(self, index=-1):
        #logger.error(f"refresh_data : {index}")
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
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())