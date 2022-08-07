# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, re, json, threading, time, shutil, platform, queue
from datetime import datetime
# third-party
import requests, xmltodict
from flask import request, render_template, jsonify, redirect
from sqlalchemy import or_, and_, func, not_, desc
# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from plugin import LogicModuleBase, default_route_socketio
from tool_base import ToolBaseFile, d, ToolSubprocess
# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting
name = 'webhook'

#########################################################

class LogicPMWebhook(LogicModuleBase):
    db_default = {
        f'{name}_db_version' : '1',
    }

    def __init__(self, P):
        super(LogicPMWebhook, self).__init__(P, 'setting')
        self.name = name

    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        arg['sub'] = self.name
        arg['sub2'] = sub 
        try:
            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"{package_name}/{name}/{sub}")


    def process_normal(self, sub, req):
        logger.error(sub)
        logger.error(req)
        #data = json.loads(req.form['payload'])
        #data = req.form
        #logger.error(d(data))

        # "\"start\":\"{file}\""
        # "mode=start|server_name={server_name}|server_machine_id={server_machine_id}|user={user}|media_type={media_type}|title={title}|file={file}|section_id={section_id}|rating_key={rating_key}|progress_percent={progress_percent}"
        if sub == 'tautulli':
            text = req.get_json()
            logger.warning(d(text))
            
            data = {}
            for tmp in text.split('|'):
                tmp2 = tmp.split('=', 1)
                logger.info(tmp2)
                data[tmp2[0]] = tmp2[1]
            

            #data = json.loads("{" + params + "}")
            logger.error(d(data))

            #if data['mode'] == 'start':
            self.start(data)
        elif sub == 'plex':
            data = json.loads(req.form['payload'])
            data = req.form
            logger.error(d(data))



        return "OK"


    

    #########################################################

    def start(self, data):
        def func():
            #TaskMakeCache.start()
            #return
            if app.config['config']['use_celery']:
                logger.debug(TaskMakeCache.start)
                result = TaskMakeCache.start.apply_async(tuple(), data)
                ret = result.get()
            else:
                ret = TaskMakeCache.start()
            logger.error("Start thread end")
        t = threading.Thread(target=func, args=())
        t.daemon = True
        t.start()

class TaskMakeCache:
    
    @staticmethod
    @celery.task()
    def start(*args, **kwargs):
        logger.debug(args)
        logger.debug(kwargs)

        TaskMakeCache(kwargs).process()


    def __init__(self, data):
        self.data = data


    def process(self):
        if self.data['mode'] == 'start':
            self.fileread_start()
    
    def fileread_start(self):

        t = threading.Thread(target=self.fileread, args=())
        t.daemon = True
        t.start()


    def fileread(self):

        logger.error(d(self.data))
        
        original_size = os.stat(self.data['file']).st_size
        logger.warning(f"오리지널 크기: {original_size}")
        logger.warning(f"오리지널 크기: {original_size}")
        action_flag = True
        if platform.system() != 'Windows':
            cache_filepath = self.data['file'].replace("/mnt/gds", "/mnt/cache/vfs/gds{2O0mA}")
            logger.debug(cache_filepath)
            cache_size = os.stat(cache_filepath).st_size
            logger.warning(f"캐시 크기: {cache_size}")

            #tmp = os.system(f'du {cache_filepath}')
            from support.base import SupportProcess
            tmp = SupportProcess.execute(['du', '-B', '1', cache_filepath])
            logger.error (tmp)
            cache_size = tmp.split(' ')[0]
            match = re.match(r'^\d+', tmp)
            cache_size = match.group(0)
            logger.info(cache_size)

            cache_size = int(cache_size)
            
            diff = abs(original_size-cache_size)
            if diff < 1024 * 1024 * 10: # 10메가
                logger.warning("캐시 완료")
                action_flag = False
            
        if action_flag:
            f = open(self.data['file'], 'rb')
            count = 0
            while True:
                buf = f.read(1024*1024)
                count += 1
                current = f.tell()
                logger.debug(f"count : {count} {current} {int(current/original_size*100)}")
                if len(buf) == 0:
                    break
