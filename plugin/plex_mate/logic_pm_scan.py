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
name = 'scan'

from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
from .model_scan import ModelScanItem
from .plex_bin_scanner import PlexBinaryScanner
#########################################################

class LogicPMScan(LogicModuleBase):
    db_default = {
        f'{name}_db_version' : '2',
        f'{name}_last_list_option' : '',
        f'{name}_start_auto' : 'False',
        f'{name}_max_process_count' : '3',
        f'{name}_manual_target' : '',
        f'{name}_max_wait_time' : '10',
    }

    def __init__(self, P):
        super(LogicPMScan, self).__init__(P, 'list')
        self.name = name

    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        arg['sub'] = self.name
        arg['sub2'] = sub 
        try:
            arg['library_list'] = PlexDBHandle.library_sections()
            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"{package_name}/{name}/{sub}")

    def process_ajax(self, sub, req):
        try:
            if sub == 'web_list':
                return jsonify(ModelScanItem.web_list(request))
            elif sub == 'command':
                ret = {}
                command = req.form['command']
                if command == 'manual':
                    target = req.form['arg2']
                    ModelSetting.set(f'{name}_manual_target', target)
                    target_mode = 'file'
                    if os.path.exists(target) and os.path.isdir(target):
                        target_mode = 'folder'
                    ret = self.make_item(call_from='web', mode=req.form['arg1'], target=target, target_mode=target_mode)
                    if ret['ret'] == 'success':
                        ret['msg'] = 'Success..'
                return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
    
    def plugin_load(self):
        self.start()
    
    
    def migration(self):
        try:
            import sqlite3
            db_file = app.config['SQLALCHEMY_BINDS'][package_name].replace('sqlite:///', '')
            logger.error(db_file)
            if ModelSetting.get(f'{name}_db_version') == '1':
                connection = sqlite3.connect(db_file)
                cursor = connection.cursor()
                query = f'ALTER TABLE {name}_item ADD add_metadata_item_id VARCHAR'
                cursor.execute(query)
                query = f'ALTER TABLE {name}_item ADD remove_metadata_item_id VARCHAR'
                cursor.execute(query)
                connection.close()
                ModelSetting.set(f'{name}_db_version', '2')
                db.session.flush()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    
    
    def reset_db(self):
        return ModelScanItem.delete_all() 

    #########################################################

       

    def start(self):
        def func():
            TaskScan.start()
            return
            if app.config['config']['use_celery']:
                logger.debug(TaskScan.start)
                result = TaskScan.start.apply_async()
                ret = result.get()
            else:
                ret = TaskScan.start()
            logger.error("Start thread end")
        t = threading.Thread(target=func, args=())
        t.daemon = True
        t.start()


    def make_item(self, call_from=None, callback_id=None, callback_url=None, mode='add', target=None, target_mode='file', section_id=None):
        db_item = ModelScanItem()
        db_item.call_from = call_from
        db_item.callback_id = callback_id
        db_item.callback_url = callback_url
        db_item.mode = mode
        db_item.target = target
        db_item.target_mode = target_mode
        if section_id != -1:
            db_item.section_id = section_id
        if isinstance(db_item.section_id, str):
            db_item.section_id = int(db_item.section_id)
        db_item.save()
        ret = {'ret':'success', 'id':db_item.id}
        return ret


class ScanException(Exception):
        pass

class TaskScan:
    

    @staticmethod
    @celery.task()
    def start():
        task = TaskScan()
        task._start()
        logger.debug('aaaaaaaaaaaaaaaaa')
        logger.debug(__class__)
    
    def __init__(self):
        logger.debug('111111111111111111111')
        self.section_locations = None
        self.run_queue = None
        self.process_count = 0
        
        ModelScanItem.not_finished_to_ready()

    def _start(self):
        logger.warning("vvvvvvvvvvvvvvvvvvvvvvvvvvv")
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
        logger.warning("33333333333333333333")
        
        while True:
            self.section_locations = PlexDBHandle.section_location()
            #logger.debug(section_locations)
            time.sleep(10)
            logger.warning(f"WAIT  : {datetime.now()}")
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
            logger.warning(f"ENQUEUE  : {datetime.now()}")
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






    def process_add(self, item):
        item.check_count += 1
        if os.path.exists(item.target):
            if os.path.isfile(item.target) and item.target_mode == 'folder':
                item.target_mode = 'file'
                item.scan_folder = os.path.dirname(item.target)
            elif os.path.isdir(item.target) and item.target_mode == 'file':
                item.target_mode = 'folder'
                item.scan_folder = item.target

            item.check_finished_time = datetime.now()

            if ModelScanItem.is_already_scan_folder_exist(item.scan_folder):
                item.set_status('finish_already_scan_folder_exist')
            else:
                item.set_status('run_add_find')
        else:
            delta = item.created_time - datetime.now()
            if delta.seconds > ModelSetting.get_int(f'{name}_max_wait_time') * 60:
                item.set_status('finish_time_over')
   




    def process_ready(self, item):
        if item.section_id is None:
            for location in self.section_locations:
                if item.target.find(location['root_path']) != -1:
                    item.section_id = location['section_id']
                    item.section_title = location['name']
                    item.section_type = location['section_type']
                    break
            if item.section_id is None:
                item.set_status('finish_not_find_library')
                raise ScanException('finish_not_find_library')
        else:
            find_flag = False
            for location in self.section_locations:
                if item.section_id == location['section_id'] and item.target.find(location['root_path']) != -1:
                    item.section_title = location['name']
                    item.section_type = location['section_type']
                    find_flag = True
                    break
            if find_flag == False:
                item.set_status('finish_wrong_section_id')
                raise ScanException('finish_wrong_section_id')

        if item.target_mode is None:
            item.traget_mode = 'file'
        if item.target_mode == 'file':
            item.scan_folder = os.path.dirname(item.target)
        else:
            item.scan_folder = item.target
        item.check_count = 0
        if item.target_mode == 'file':
            data = self.get_meta(item)
            logger.debug(data)
            if item.mode == 'add' and len(data) > 0:
                item.add_metadata_item_id = data[0]['metadata_item_id']
                item.set_status('finish_add_already_in_db')
                raise ScanException('finish_add_already_in_db')
            if item.mode == 'remove' and len(data) == 0:
                item.set_status('finish_remove_already_not_in_db')
                raise ScanException('finish_remove_already_not_in_db')

        if item.mode == 'add':
            item.set_status('wait_add_not_find')
        elif item.mode == 'remove':
            item.set_status('wait_remove_still_exist')


    def get_meta(self, item):
        query = """SELECT metadata_items.id as metadata_item_id, media_parts.file as file FROM metadata_items, media_items, media_parts WHERE metadata_items.id = media_items.metadata_item_id AND media_items.id = media_parts.media_item_id AND metadata_items.library_section_id = ? AND media_parts.file = ?"""
        data = PlexDBHandle.select2(query, (item.section_id, item.target))
        return data
        