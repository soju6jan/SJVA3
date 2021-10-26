# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, re, json, threading, time, shutil, platform
from datetime import datetime
# third-party
import requests, xmltodict
from flask import request, render_template, jsonify, redirect
# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util, path_app_root
from plugin import LogicModuleBase, default_route_socketio
from tool_base import ToolBaseFile, d, ToolSubprocess
from framework.job import Job

# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting
name = 'periodic'
from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
from .logic_pm_base import LogicPMBase
from .task_pm_periodic import Task
from .model_periodic import ModelPeriodicItem

#########################################################

class LogicPMPeriodic(LogicModuleBase):
    db_default = {
        f'{name}_db_version' : '1',
        f'{name}_last_list_option' : '',
    }

    def __init__(self, P):
        super(LogicPMPeriodic, self).__init__(P, 'list')
        self.name = name

    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        arg['sub'] = self.name
        arg['sub2'] = sub 
        try:
            arg['path_app_root'] = path_app_root
            arg['library_list'] = PlexDBHandle.library_sections()
            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"{package_name}/{name}/{sub}")

    def process_ajax(self, sub, req):
        try:
            if sub == 'web_list':
                return jsonify(ModelPeriodicItem.web_list(request))
            elif sub == 'command':
                ret = {}
                command = req.form['command']
                if command == 'kill':
                    ret = self.kill(req.form['arg1'])
                elif command == 'remove_no_append_data':
                    ret = ModelPeriodicItem.remove_no_append_data()
                elif command == 'get_tasks':
                    section_list = PlexDBHandle.library_sections()
                    #logger.debug(d(section_list))
                    tasks = self.get_jobs()
                    for idx, task in enumerate(tasks):
                        for section in section_list:
                            if str(task['섹션ID']) ==  str(section['id']):
                                task['section_title'] = section['name']
                                break
                    ret = {'data' : tasks}
                elif command == 'task_sched':
                    idx = int(req.form['arg1'])
                    flag = (req.form['arg2'] == 'true')
                    job_id = f'{self.P.package_name}_periodic_{idx}'
                    ret = {'ret':'success'}
                    if flag and scheduler.is_include(job_id):
                        ret['msg'] = '이미 스케쥴러에 등록되어 있습니다.'
                    elif flag and scheduler.is_include(job_id) == False:
                        result = self.sched_add(idx)
                    elif flag == False and scheduler.is_include(job_id):
                        result = scheduler.remove_job(job_id)
                        ret['msg'] = '스케쥴링 취소'
                    elif flag == False and scheduler.is_include(job_id) == False:
                        ret['msg'] = '등록되어 있지 않습니다.'

                elif command == 'all_sched_add':
                    tasks = self.get_jobs()
                    for idx, item in enumerate(tasks):
                        if item.get('스케쥴링', '등록') == '등록':
                            self.sched_add(idx, item=item)
                    ret = {'ret' : 'success', 'msg' : 'Success'}
                elif command == 'all_sched_remove':
                    tasks = self.get_jobs()
                    for idx, item in enumerate(tasks):
                        if scheduler.is_include(item['job_id']):
                            scheduler.remove_job(item['job_id'])
                    ret = {'ret' : 'success', 'msg' : 'Success'}
                elif command == 'task_execute':
                    result = self.one_execute(int(req.form['arg1']))
                    ret = {'ret' : 'success', 'data':result}
                return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})



    def plugin_load(self):
        ModelPeriodicItem.set_terminated()
        self.start()


    def reset_db(self):
        return ModelPeriodicItem.delete_all()



    #########################################################

    def sched_add(self, idx, item=None):
        try:
            if item is None:
                item = self.get_jobs()[idx]
            if scheduler.is_include(item['job_id']):
                logger.debug(f"{item['섹션ID']} include scheduler!")
                return
            job = Job(self.P.package_name, item['job_id'], item['주기'], self.job_function, item['설명'], False, args=idx)
            scheduler.add_job_instance(job)
            return True
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())   
        return False


    def kill(self, db_item_id):
        import psutil
        try:
            db_item = ModelPeriodicItem.get_by_id(db_item_id)
            logger.debug(d(db_item.as_dict()))
            if db_item is not None:
                
                process = psutil.Process(int(db_item.process_pid))
                logger.debug(process)
                logger.debug(process.name())
                if process.name().find('Plex Media Scanner') != -1:
                    for proc in process.children(recursive=True):
                        proc.kill()
                    process.kill()
                    db_item.status = 'user_stop'
                    db_item.save()
                    ret = {'ret':'success', 'msg':'정상적으로 중지하였습니다.'}
                else:
                    ret = {'ret':'success', 'msg':'Plex Media Scanner 파일이 아닙니다.'}
        except psutil.NoSuchProcess:
            ret = {'ret':'danger', 'msg':'실행중인 프로세스가 아닙니다.'}
            if db_item is not None:
                db_item.status = 'terminated'
                db_item.save()
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            ret = {'ret':'danger', 'msg':str(e)} 
        return ret




    def start(self):
        #logger.error("START")
        data = self.get_jobs()

        for idx, item in enumerate(data):
            if item.get('스케쥴링', '등록') == '등록':
                self.sched_add(idx, item=item)
                 

    @classmethod
    def get_jobs(cls):
        config = LogicPMBase.load_config()
        data = config.get('라이브러리 주기적 스캔 목록', None)
        if data is None or type(data) != type([]):
            return []
        for idx, item in enumerate(data):
            item['job_id'] = f'{package_name}_periodic_{idx}'
            item['설명'] = item.get('설명', f"섹션: {item['섹션ID']}")
            item['is_include_scheduler'] = str(scheduler.is_include(item['job_id']))
        return data


    def job_function(self, idx):
        logger.warning(f"job_function IDX : {idx}")
        data = self.get_jobs()[idx]
        if data.get('스캔모드', None) == '웹':
            PlexWebHandle.section_scan(data['섹션ID'])
            logger.debug(f"스캔모드 : 웹 실행")
            logger.debug(data)
            return

        #Task.start(idx)
        if app.config['config']['use_celery']:
            result = Task.start.apply_async((idx,'scheduler'))
            ret = result.get()
        else:
            ret = Task.start(idx, 'scheduler')
            #ret = func(self, *args)

    def one_execute(self, idx):
        try:
            job_id = f'{package_name}_periodic_{idx}'
            if scheduler.is_include(job_id):
                if scheduler.is_running(job_id):
                    ret = 'is_running'
                else:
                    scheduler.execute_job(job_id)
                    ret = 'scheduler'
            else:
                def func():
                    time.sleep(2)
                    self.job_function(idx)
                t = threading.Thread(target=func, args=())
                t.daemon = True
                t.start()
                ret = 'thread'
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            ret = 'fail'
        return ret