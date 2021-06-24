# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, re, json, threading, time, shutil, yaml
from datetime import datetime
# third-party
import requests, yaml
# third-party
from flask import request, render_template, jsonify, redirect
from sqlalchemy import or_, and_, func, not_, desc

# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util, path_app_root
from framework.common.plugin import LogicModuleBase, default_route_socketio
from tool_base import ToolBaseFile, d

# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting
name = 'basic'
from .task_for_download import Task

#########################################################
class LogicKtvBasic(LogicModuleBase):
    db_default = {
        f'{name}_db_version' : '1',
        f'{name}_interval' : '30',
        f'{name}_auto_start' : 'False',
        f'{name}_path_source' : '',
        f'{name}_path_target' : '',
        f'{name}_path_error' : '',
        f'{name}_folder_format' : '{genre}/{title}',
        f'{name}_path_config' : os.path.join(path_data, 'db', f"{package_name}_{name}.yaml"),
        f'{name}_task_stop_flag' : 'False',
        f'{name}_dry_task_stop_flag' : 'False',
    }

    def __init__(self, P):
        super(LogicKtvBasic, self).__init__(P, 'setting', scheduler_desc='국내TV 파일처리 - 기본')
        self.name = name
        self.data = {
            'data' : [],
            'is_working' : 'wait'
        }
        default_route_socketio(P, self)

    def process_menu(self, sub, req):
        try:
            arg = P.ModelSetting.to_dict()
            arg['sub'] = self.name
            if sub == 'setting':
                arg['scheduler'] = str(scheduler.is_include(self.get_scheduler_name()))
                arg['is_running'] = str(scheduler.is_running(self.get_scheduler_name()))
                arg['path_app_root'] = path_app_root
            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"{package_name}/{name}/{sub}")

    def process_ajax(self, sub, req):
        try:
            if sub == 'command':
                command = req.form['command']
                ret = {}
                if command == 'refresh':
                    self.refresh_data()
                elif command == 'dry_run_start':
                    def func():
                        self.call_task(is_dry=True)
                    th = threading.Thread(target=func, args=())
                    th.setDaemon(True)
                    th.start()
                    ret = {'ret':'success', 'msg':'곧 실행됩니다.'}
                elif command == 'dry_run_stop':
                    if self.data['is_working'] == 'run':
                        ModelSetting.set(f'{name}_dry_task_stop_flag', 'True')
                        ModelSetting.set(f'{name}_task_stop_flag', 'True')
                        ret = {'ret':'success', 'msg':'잠시 후 중지됩니다.'}
                    else:
                        ret = {'ret':'warning', 'msg':'대기중입니다.'}
                return jsonify(ret)
        except Exception as e: 
            P.logger.error('Exception:%s', e)
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})

    def scheduler_function(self):
        self.call_task()
    
    def call_task(self, is_dry=False):
        config = self.load_basic_config()
        self.data['data'] = []
        self.data['is_working'] = 'run'
        self.refresh_data()
        config[0]['소스 폴더'] = ModelSetting.get(f"{name}_path_source")
        config[0]['타겟 폴더'] = ModelSetting.get(f"{name}_path_target")
        config[0]['에러 폴더'] = ModelSetting.get(f"{name}_path_error")
        config[0]['타겟 폴더 구조'] = ModelSetting.get(f"{name}_folder_format")
        call_module = name
        if is_dry:
            call_module += '_dry'
        ModelSetting.set(f'{call_module}_task_stop_flag', 'False')
        if app.config['config']['use_celery']:
            result = Task.start.apply_async((config, call_module))
            try:
                ret = result.get(on_message=self.receive_from_task, propagate=True)
            except:
                logger.debug('CELERY on_message not process.. only get() start')
                ret = result.get()
        else:
            Task.start(config, call_module)
        self.data['is_working'] = ret
        self.refresh_data()   

    def plugin_load(self):
        if os.path.exists(ModelSetting.get(f'{name}_path_config')) == False:
            shutil.copyfile(os.path.join(os.path.dirname(__file__), 'file', f'config_{name}.yaml'), ModelSetting.get(f'{name}_path_config'))

    #########################################################
    def load_basic_config(self):
        with open(ModelSetting.get(f'{name}_path_config')) as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
        return config


    def refresh_data(self, index=-1):
        if index == -1:
            self.socketio_callback('refresh_all', self.data)
        else:
            self.socketio_callback('refresh_one', self.data['data'][index])
    
    def receive_from_task(self, arg, celery=True):
        try:
            result = None
            if celery:
                if arg['status'] == 'PROGRESS':
                    result = arg['result']
            else:
                result = arg
            if result is not None:
                result['index'] = len(self.data['data'])
                self.data['data'].append(result)
                self.refresh_data(index=result['index'])
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())