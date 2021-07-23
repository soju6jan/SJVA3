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



class LogicPMDBToolSimple(LogicSubModuleBase):
    def __init__(self, P, parent, name):
        super(LogicPMDBToolSimple, self).__init__(P, parent, name)
        self.db_default = {
            f'{self.parent.name}_{self.name}_db_version' : '1',
            f'{self.parent.name}_{self.name}_library_location_source' : '',
            f'{self.parent.name}_{self.name}_library_location_target' : '',
            
        }
        


    def process_ajax(self, sub, req):
        try:
            ret = {}
            if sub == 'command':
                command = req.form['command']
                logger.error(f"sub : {sub}  /  command : {command}")
                if command == 'update_show_add':
                    query = 'UPDATE metadata_items SET added_at = (SELECT max(added_at) FROM metadata_items mi WHERE mi.parent_id = metadata_items.id OR mi.parent_id IN(SELECT id FROM metadata_items mi2 WHERE mi2.parent_id = metadata_items.id)) WHERE metadata_type = 2;'
                    result = PlexDBHandle.execute_query(query)
                    if result:
                        ret = {'ret':'success', 'msg':'정상적으로 처리되었습니다.'}
                    else:
                        ret = {'ret':'warning', 'msg':'실패'}
                elif command == 'remove_collection_count':
                    query = f"SELECT count(*) AS cnt FROM metadata_items WHERE metadata_type = 18 AND library_section_id = {req.form['arg1']};"
                    result = PlexDBHandle.select(query)
                    if result is not None and len(result)>0:
                        ret = {'ret':'success', 'msg':f"{result[0]['cnt']}개의 컬렉션이 있습니다."}
                    else:
                        ret = {'ret':'warning', 'msg':'실패'}
                elif command == 'remove_collection':
                    query = f"DELETE FROM metadata_items WHERE metadata_type = 18 AND library_section_id = {req.form['arg1']};"
                    result = PlexDBHandle.execute_query(query)
                    if result:
                        ret = {'ret':'success', 'msg':'정상적으로 처리되었습니다.'}
                    else:
                        ret = {'ret':'warning', 'msg':'실패'}
                elif command == 'remove_sjva_extra_count':
                    query = f"SELECT count(*) AS cnt FROM metadata_items WHERE metadata_type = 12 AND guid LIKE 'sjva://sjva.me%';"
                    result = PlexDBHandle.select(query)
                    if result is not None and len(result)>0:
                        ret = {'ret':'success', 'msg':f"{result[0]['cnt']}개의 부가영상이 있습니다."}
                    else:
                        ret = {'ret':'warning', 'msg':'실패'}
                elif command == 'remove_sjva_extra':
                    query = f"DELETE FROM metadata_items WHERE metadata_type = 12 AND guid LIKE 'sjva://sjva.me%';"
                    result = PlexDBHandle.execute_query(query)
                    if result:
                        ret = {'ret':'success', 'msg':'정상적으로 처리되었습니다.'}
                    else:
                        ret = {'ret':'warning', 'msg':'실패'}
                elif command == 'update_sjva_extra':
                    query = f"DELETE FROM metadata_items WHERE metadata_type = 12 AND (guid LIKE 'sjva://sjva.me/wavve_movie%' OR guid LIKE 'sjva://sjva.me/redirect.m3u8/tving%' OR guid LIKE '%=ooo5298ooo%');\n"

                    query += f'UPDATE metadata_items SET guid = REPLACE(REPLACE(guid, "http://localhost:9999", "{SystemModelSetting.get("ddns")}"), "apikey=0123456789", "apikey={SystemModelSetting.get("auth_apikey")}") WHERE metadata_type = 12 AND guid LIKE "sjva://sjva.me%" AND guid LIKE "%http://localhost:9999%";'

                    result = PlexDBHandle.execute_query(query)
                    if result:
                        ret = {'ret':'success', 'msg':'정상적으로 처리되었습니다.'}
                    else:
                        ret = {'ret':'warning', 'msg':'실패'}
                elif command == 'library_location_source':
                    ModelSetting.set(f'{self.parent.name}_{self.name}_library_location_source', req.form['arg1'])

                    query = f'SELECT count(*) AS cnt FROM section_locations WHERE root_path LIKE "{req.form["arg1"]}%";'
                    result = PlexDBHandle.select(query)
                    msg = f"섹션폴더 (section_locations) : {result[0]['cnt']}<br>"

                    query = f'SELECT count(*) AS cnt FROM media_parts WHERE file LIKE "{req.form["arg1"]}%";'
                    result = PlexDBHandle.select(query)
                    msg += f"영상파일 (media_parts) : {result[0]['cnt']}<br>"

                    query = f'SELECT count(*) AS cnt FROM media_streams WHERE url LIKE "file://{req.form["arg1"]}%";'
                    result = PlexDBHandle.select(query)
                    msg += f"자막 (media_streams) : {result[0]['cnt']}"

                    ret = {'ret':'success', 'msg':msg}
                elif command == 'library_location_target':
                    ModelSetting.set(f'{self.parent.name}_{self.name}_library_location_source', req.form['arg1'])
                    ModelSetting.set(f'{self.parent.name}_{self.name}_library_location_target', req.form['arg2'])

                    query = f'UPDATE section_locations SET root_path = REPLACE(root_path, "{req.form["arg1"]}", "{req.form["arg2"]}");'

                    query += f'UPDATE media_parts SET file = REPLACE(file, "{req.form["arg1"]}", "{req.form["arg2"]}");'

                    query += f'UPDATE media_streams SET url = REPLACE(file, "{req.form["arg1"]}", "{req.form["arg2"]}");'

                    result = PlexDBHandle.execute_query(query)
                    if result:
                        ret = {'ret':'success', 'msg':'정상적으로 처리되었습니다.'}
                    else:
                        ret = {'ret':'warning', 'msg':'실패'}
                elif command == 'duplicate_list':
                    query = f"select metadata_items.id as meta_id, metadata_items.media_item_count,  media_items.id as media_id, media_parts.id as media_parts_id, media_parts.file from media_items, metadata_items, media_parts, (select media_parts.file as file, min(media_items.id) as media_id,  count(*) as cnt from media_items, metadata_items, media_parts where media_items.metadata_item_id = metadata_items.id and media_parts.media_item_id = media_items.id and metadata_items.media_item_count > 1 and media_parts.file != '' group by media_parts.file having cnt > 1) as ttt where media_items.metadata_item_id = metadata_items.id and media_parts.media_item_id = media_items.id and metadata_items.media_item_count > 1 and media_parts.file != '' and media_parts.file = ttt.file order by meta_id, media_id, media_parts_id;"
                    data = PlexDBHandle.select(query)
                    ret['modal'] = json.dumps(data, indent=4, ensure_ascii=False)
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
        #if sub == 'movie':
        library_section = PlexDBHandle.library_section(args[1])
        #logger.warning(d(library_section))
        self.data['list'] = []
        self.data['status']['is_working'] = 'run'
        self.refresh_data()
        ModelSetting.set(f'{self.parent.name}_{self.name}_task_stop_flag', 'False')

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
            ret = func(*args)
        self.data['status']['is_working'] = ret
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