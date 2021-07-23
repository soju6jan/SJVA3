# python
import os, sys, traceback, re, json, threading, time, shutil, fnmatch, glob, platform
from datetime import datetime, timedelta
# third-party
import requests, sqlite3, yaml

# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from plugin import LogicModuleBase, default_route_socketio
from tool_expand import ToolExpandFileProcess
from tool_base import ToolShutil, d, ToolUtil, ToolBaseFile, ToolOSCommand, ToolSubprocess


from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# tag : db에서는 구분 값 / xml info - 폴더명
TAG = {
    'poster' : ['thumb', 'posters'],
    'art' : ['art', 'art'],
    'banner' : ['banner', 'banners']
}




class Task(object):


    @staticmethod
    @celery.task(bind=True)
    def start(self, location, meta_type, folder, dryrun):
        dryrun = True if dryrun == 'true'  else False

        if location == 'Metadata':
            root_path = os.path.join(ModelSetting.get('base_path_metadata'), meta_type)
        elif location == 'Media':
            root_path = os.path.join(ModelSetting.get('base_path_media'), 'localhost')
       
        if folder == 'all':
            folders = os.listdir(root_path)
        else:
            folders = [folder]
        
        db_file = ModelSetting.get('base_path_db')
        con = sqlite3.connect(db_file)
        cur = con.cursor()

        status = {'is_working':'run', 'remove_count' : 0, 'remove_size':0, 'count':0, 'current':0}


        for folder in folders:
            folder_path = os.path.join(root_path, folder)
            if os.path.exists(folder_path) == False:
                continue

            bundle_list = os.listdir(folder_path)
            status['count'] += len(bundle_list)
            for bundle in bundle_list:
                try:
                    if ModelSetting.get_bool('clear_bundle_task_stop_flag'):
                        return 'stop'
                    time.sleep(0.05)
                    status['current'] += 1
                    data = {'folder':folder, 'bundle':bundle, 'status':status}
                    bundle_path = os.path.join(folder_path, bundle)
                    hash_value = folder + bundle.split('.')[0]
                    if location == 'Metadata':
                        ce = con.execute('SELECT * FROM metadata_items WHERE hash = ?', (hash_value,))
                    else:
                        ce = con.execute('SELECT * FROM media_parts WHERE hash = ?', (hash_value,))
                    ce.row_factory = dict_factory
                    fetch = ce.fetchall()
                    if len(fetch) == 1:
                        if location == 'Metadata':
                            data['title'] = fetch[0]['title']
                        else:
                            data['file'] = fetch[0]['file']
                    elif len(fetch) == 0:
                        tmp = ToolBaseFile.size(start_path=bundle_path)
                        data['remove'] = tmp
                        status['remove_size'] += tmp
                        status['remove_count'] += 1
                        if dryrun == False:
                            ToolBaseFile.rmtree(_path)
                    if app.config['config']['use_celery']:
                        self.update_state(state='PROGRESS', meta=data)
                    else:
                        P.logic.get_module('clear').sub_list['bundle'].receive_from_task(data, celery=False)
                except Exception as e: 
                    logger.error(f'Exception:{str(e)}')
                    logger.error(traceback.format_exc())
        return 'wait'