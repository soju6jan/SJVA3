# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, re, json, threading, time, shutil, platform
from datetime import datetime
# third-party
import requests, xmltodict, sqlite3
from flask import request, render_template, jsonify, redirect
# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from plugin import default_route_socketio_sub, LogicSubModuleBase
from tool_base import ToolBaseFile, d, ToolSubprocess, ToolShutil
# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting

from .plex_db import PlexDBHandle, dict_factory
from .plex_web import PlexWebHandle
from .plex_bin_scanner import PlexBinaryScanner
#########################################################


from watchdog.observers.polling import PollingObserver as Observer
#from watchdog.events import FileSystemEventHandler
from watchdog.events import LoggingEventHandler


class LogicPMWatchdogSetting(LogicSubModuleBase):

    def __init__(self, P, parent, name):
        super(LogicPMWatchdogSetting, self).__init__(P, parent, name)
        self.db_default = {
            f'{self.parent.name}_{self.name}_db_version' : '1',
            f'{self.parent.name}_{self.name}_path_list' : '',
            f'{self.parent.name}_{self.name}_auto_start' : 'False',
            f'{self.parent.name}_{self.name}_interval' : '9999',
            f'{self.parent.name}_{self.name}_include_sub' : 'False',
            f'{self.parent.name}_{self.name}_include_json' : 'False',
            f'{self.parent.name}_{self.name}_status' : 'False',
        }
        self.scheduler_desc = 'Plex Watchdog 스케쥴링'


    def scheduler_function(self):
        logger.error('scheduler_function')
        def func():
            time.sleep(1)
            self.task_interface()
            
        th = threading.Thread(target=func, args=())
        th.setDaemon(True)
        th.start()

    def process_ajax(self, sub, req):
        try:
            ret = {}
            if sub == 'command':
                command = req.form['command']
                arg = req.form['arg1']
                logger.warning(command)
                logger.warning(arg)
                if arg == 'true':
                    self.scheduler_function()
                else:
                    ModelSetting.set(f'{self.parent.name}_{self.name}_status', 'False')
            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})

    #########################################################


    def task_interface(self):
        ModelSetting.set(f'{self.parent.name}_{self.name}_status', 'True')
        if app.config['config']['use_celery']:
            result = Task.start.apply_async()
            ret = result.get()
        else:
            ret = Task.start()






class Task(object):
    
    @staticmethod
    @celery.task()
    def start():
        
        control = WatchdogControl()
        control.start()

        """
        #from watchdog.observers import Observer
        path_list = ModelSetting.get_list(f'watchdog_setting_path_list')
        logger.warning(path_list)

        event_handler = LoggingEventHandler()
        observer = Observer()
        observer.schedule(event_handler, path_list[0], recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        finally:
            observer.stop()
            observer.join()

        """


class WatchdogControl:

    job_list = None
    conn = None
    cursor = None
    section_locations = None

    def __init__(self):
        self.job_list = []
        self.db_init()
        

    def start(self):

        from watchdog.observers import Observer
        path_list = ModelSetting.get_list(f'watchdog_setting_path_list')
        logger.warning(path_list)

        for path in path_list:
            job = WatchdogJob(self, path)
            job.start()
            self.job_list.append(job)
        self.db_init()
        self.join()
    
    def db_init(self):
        self.conn = sqlite3.connect(ModelSetting.get('base_path_db'), check_same_thread=False)
        self.cursor = self.conn.cursor()
        ce = self.conn.execute('SELECT * FROM section_locations')
        ce.row_factory = dict_factory
        self.section_locations = ce.fetchall()


    
    def join(self):
        logger.warning("대기 ")
        for job in self.job_list:
            job.thread.join()
        logger.warning("대기 끝")


    def get_status(self):
        return ModelSetting.get_bool(f'watchdog_setting_status')



    def get_section_list_by_filepath(self, filepath):
        ret = []
        for section_location in self.section_locations:
            if filepath.find(section_location['root_path']) != -1:
                if section_location['library_section_id'] not in ret:
                    ret.append(section_location['library_section_id'])
        return ret



    def on_created(self, filepath):
        section_list = self.get_section_list_by_filepath(filepath)

        logger.warning(section_list)

        
        ce = self.conn.execute("SELECT metadata_items.library_section_id FROM media_parts, media_items, metadata_items WHERE media_parts.media_item_id = media_items.id  AND media_items.metadata_item_id = metadata_items.id AND file = ?", (filepath,))
        ce.row_factory = dict_factory
        db_section_list = ce.fetchall()
        logger.debug(db_section_list)

        for section_id in section_list:
            if section_id not in db_section_list:
                logger.warning(f'스캔 : {section_id} {filepath}')
                PlexBinaryScanner.scan_refresh2(section_id, os.path.dirname(filepath))


        





class WatchdogJob(object):

    def __init__(self, control, path):
        self.handler = WatchdogHandler(control)
        self.observer = Observer()
        self.control = control
        self.watchdog_path = path
        self.thread = None

    def start(self):
        def thread_function():
            try:
                self.observer.schedule(
                    self.handler,
                    self.watchdog_path,
                    recursive=True
                )
                logger.warning("시작")
                self.observer.start()
                logger.warning("시작 222")
      
                try:
                    while self.control.get_status():
                        for i in range(60):
                            #logger.debug('1111111111')
                            time.sleep(1)
                except KeyboardInterrupt as e:
                    self.observer.stop()
                finally:
                    self.observer.stop()
                    self.observer.join()
                logger.error('22222222222222222')
            except Exception as e: 
                P.logger.error(f'Exception:{str(e)}')
                P.logger.error(traceback.format_exc())   
        self.thread = threading.Thread(target=thread_function, args=())
        self.thread.daemon = True
        self.thread.start()


class WatchdogHandler(LoggingEventHandler):


    def __init__(self, control):
        super(WatchdogHandler, self).__init__()
        self.control = control

    def on_created(self, event):
        super().on_created(event)
        if event.is_directory:
            return
        self.control.on_created(event.src_path)


    def on_moved(self, event):
        logger.error('on_moved')
        logger.warning(d(event))

    
    def on_deleted(self, event):
        #<DirDeletedEvent: event_type=deleted, src_path='/mnt/gds/VOD/1.방송중/드라마/aaa', is_directory=True>
        logger.error('on_deleted')
        logger.warning(d(event))

    def on_modified(self, event):
        logger.error('on_modified')
        logger.warning(d(event))

    def on_closed(self, event):
        logger.error('on_closed')
        logger.warning(d(event))