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

        #task = TaskScan()
        #task._start()
        #logger.debug(__class__)
    
    def __init__(self):
        self.section_locations = None
        self.run_queue = None
        self.process_count = 0
        ModelScanItem.not_finished_to_ready()

    def _start(self):
        t = threading.Thread(target=self.wait, args=())
        t.daemon = True
        t.start()

        self.queue = queue.Queue()


        t = threading.Thread(target=self.enqueue, args=())
        t.daemon = True
        t.start()


        t = threading.Thread(target=self.run, args=())
        t.daemon = True
        t.start()


    def wait(self):
        #logger.warning("33333333333333333333")
        
        while True:
            self.section_locations = PlexDBHandle.section_location()
            #logger.debug(section_locations)
            time.sleep(10)
            #logger.warning(f"WAIT  : {datetime.now()}")
            items = ModelScanItem.get_items('wait')

            for item in items:
                try:
                    logger.debug(d(item.as_dict()))
                    if item.status == 'ready':
                        self.process_ready(item)
                    if item.status == 'wait_add_not_find':
                        self.process_add(item)

                                
                except ScanException as e:
                    logger.error(f'Known Exception :{str(e)}')
                except Exception as e: 
                    logger.error(f'Exception:{str(e)}')
                    logger.error(traceback.format_exc())   
                finally:
                    item.save()


    def enqueue(self):
        while True:
            time.sleep(10)
            #logger.warning(f"ENQUEUE  : {datetime.now()}")
            items = ModelScanItem.get_items('run')
            #current_queue = list(self.queue.queue)
            #logger.warning(current_queue)
            for item in items:
                try:
                    logger.warning(d(item.as_dict()))
                    self.queue.put(item)
                    item.set_status(item.status.replace('run_', 'enqueue_'))
                except Exception as e: 
                    #logger.error(f'Exception:{str(e)}')
                    #logger.error(traceback.format_exc()) 
                    pass
                finally:
                    item.save() 

            #logger.error(f"self.queue.empty() : {self.queue.empty()}")
            #logger.error(f"self.queue.empty() : {self.queue.qsize()}")
            #if self.queue.empty():
            #    continue


    def run(self):
        while True:
            try:
                max_process_count = ModelSetting.get_int(f'{name}_max_process_count')
                while True:
                    try:
                        if self.process_count < max_process_count:
                            break
                        time.sleep(5)
                    except Exception as e: 
                        logger.error(f'Exception:{str(e)}')
                        logger.error(traceback.format_exc())  
                        break
                item = self.queue.get()
                item = ModelScanItem.get_by_id(item.id)
                self.scan(item)
                logger.error(item)
                self.queue.task_done()
            except Exception as e: 
                logger.error(f'Exception:{str(e)}')
                logger.error(traceback.format_exc())   
            finally:
                item.save()


    def scan(self, item):
        def func(db_id):
            item = ModelScanItem.get_by_id(db_id)
            self.process_count += 1
            PlexBinaryScanner.scan_refresh2(item.section_id, item.scan_folder, timeout=60*30)
            time.sleep(100)
            self.process_count -= 1
            
            #self.queue.task_done()
            item.finish_time = datetime.now()
            if item.target_mode == 'file':
                data = self.get_meta(item)
                logger.debug(data)
                if item.mode == 'add' and len(data) > 0:
                    item.add_metadata_item_id = data[0]['metadata_item_id']
                #if item.mode == 'remove' and len(data) == 0:
                #    item.set_status('finish_remove_already_not_in_db')
                #    raise ScanException('finish_remove_already_not_in_db')
            item.set_status(f'finish_{item.mode}', save=True)
        t = threading.Thread(target=func, args=(item.id,))
        t.daemon = True
        t.start()
