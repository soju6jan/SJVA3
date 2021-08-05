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
from tool_expand import EntityKtv

from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting
from .logic_pm_base import LogicPMBase
from .plex_db import PlexDBHandle, dict_factory


class Task(object):

    source_con = source_cur = None
    target_con = target_cur = None
    change_rule = None

    @staticmethod
    @celery.task(bind=True)
    def start(self):
        SECTION_ID = ModelSetting.get('dbcopy_copy_target_section_id')
        SECTION_LOCATION_ID = ModelSetting.get('dbcopy_copy_target_section_location_id')
        Task.change_rule = [ModelSetting.get('dbcopy_copy_path_source_root_path'), ModelSetting.get('dbcopy_copy_path_target_root_path')]
        Task.file_change_rule = [ModelSetting.get('dbcopy_copy_path_source_root_path'), ModelSetting.get('dbcopy_copy_path_target_root_path').replace(' ', '%20')]

        Task.source_con = sqlite3.connect(ModelSetting.get('dbcopy_copy_path_source_db'))
        Task.source_cur = Task.source_con.cursor()
        
        Task.target_con = sqlite3.connect(ModelSetting.get('base_path_db'))
        Task.target_cur = Task.target_con.cursor()

        ce = Task.source_con.execute('SELECT * FROM metadata_items WHERE library_section_id = ? ORDER BY title DESC', (ModelSetting.get('dbcopy_copy_source_section_id'),))
        ce.row_factory = dict_factory
        meta_list = ce.fetchall()
        status = {'is_working':'run', 'count':len(meta_list), 'current':0}
        for idx, metadata_item in enumerate(meta_list):
            if ModelSetting.get_bool('dbcopy_status_task_stop_flag'):
                return 'stop'
            #if idx > 30:
            #    return 'wait'
            try:
                status['current'] += 1
                data = {'status':status, 'ret':'append', 'title':metadata_item['title'], 'year':metadata_item['year'], 'files':[]}
                #logger.warning(f"{idx} / {len(meta_list)} {metadata_item['title']}")
                metadata_item_id, is_exist = Task.insert_metadata_items(metadata_item, SECTION_ID)
                if is_exist:
                    data['ret'] = 'exist'
                    continue
                #logger.warning(f"metadata_item_id : {metadata_item_id}")
                new_filename = None
                media_ce = Task.source_con.execute('SELECT * FROM media_items WHERE metadata_item_id = ? ORDER BY id', (metadata_item['id'],))
                media_ce.row_factory = dict_factory
                for media_item in media_ce.fetchall():
                    #logger.debug(d(media_item))
                    media_item_id = Task.insert_media_items(media_item, SECTION_ID, SECTION_LOCATION_ID, metadata_item_id)
                    #logger.warning(f"media_item_id : {media_item_id}")

                    part_ce = Task.source_con.execute('SELECT * FROM media_parts WHERE media_item_id = ? ORDER BY id', (media_item['id'],))
                    part_ce.row_factory = dict_factory
                    for media_part in part_ce.fetchall():
                        #logger.debug(d(media_part))
                        media_part_id, new_filename = Task.insert_media_parts(media_part, media_item_id, SECTION_ID)
                        #logger.warning(f"media_part_id : {media_part_id}")
                        data['files'].append(new_filename)
                        stream_ce = Task.source_con.execute('SELECT * FROM media_streams WHERE media_item_id = ? AND media_part_id = ? ORDER BY id', (media_item['id'],media_part['id']))
                        stream_ce.row_factory = dict_factory
                        for media_stream in stream_ce.fetchall():
                            #logger.debug(d(media_stream))
                            media_stream_id = Task.insert_media_streams(media_stream, media_item_id, media_part_id, SECTION_ID)
                            #logger.warning(f"media_stream_id : {media_stream_id}")
            except Exception as e: 
                logger.error(f'Exception:{str(e)}')
                logger.error(traceback.format_exc())
            finally:
                if app.config['config']['use_celery']:
                    self.update_state(state='PROGRESS', meta=data)
                else:
                    self.receive_from_task(data, celery=False)


            # bin scan
            """
            if new_filename is not None:
                meta_root = os.path.dirname(os.path.dirname(new_filename))
                PlexBinaryScanner.scan_refresh(section_id, meta_root)
            """
            #PlexDBHandle.execute_query
    
    @staticmethod
    def insert_media_streams(media_stream, media_item_id, media_part_id, library_section_id):
        data = PlexDBHandle.select2(f"SELECT id FROM media_streams WHERE media_item_id = ? AND media_part_id = ? AND stream_type_id = ? AND codec = ? AND language = ? AND `index` = ? AND extra_data = ?", (media_item_id, media_part_id, media_stream['stream_type_id'], media_stream['codec'], media_stream['language'], media_stream['index'], media_stream['extra_data']))
        #logger.error(data)
        if len(data) == 1:
            return data[0]['id']
        elif len(data) == 0:
            insert_col = ''
            insert_value = ''
            for key, value in media_stream.items():
                if key in ['id']:
                    continue
                if key == 'media_item_id':
                    value = media_item_id
                if key == 'media_part_id':
                    value = media_part_id
                if key == 'url':
                    if value != '' and value.startswith('file'):
                        value = value.replace(Task.file_change_rule[0], Task.file_change_rule[1])
                if value is None:
                    continue
                insert_col += f"'{key}',"
                if type(value) == type(''):
                    insert_value += f'"{value}",'
                else:
                    insert_value += f"{value},"

            insert_col = insert_col.rstrip(',')
            insert_value = insert_value.rstrip(',')

            query = f"INSERT INTO media_streams ({insert_col}) VALUES ({insert_value});SELECT max(id) FROM media_streams;" 
            #logger.error(query)
            ret = PlexDBHandle.execute_query2(query)
            if ret != '':
                return int(ret)
        else:
            logger.error("동일 정보가 여러가 있음")



    @staticmethod
    def process_localfile(filepath, library_section_id):
        #logger.error(filepath)
        new_filepath = filepath.replace(Task.change_rule[0], Task.change_rule[1])
        if Task.change_rule[1][0] != '/': #windows
            new_filepath = new_filepath.replace('/', '\\')
        #logger.warning(f"새로운 경로 : {new_filepath}")
        #라이브러리 폴더 root_path
        
        text = filepath.replace(Task.change_rule[0] + '/', '')
        #logger.debug(text)
        folderpath = '/'.join(text.split('/')[:-1])
        ret = {}
        ret['new_filepath'] = new_filepath
        ret['dir_id'] = Task.make_directories(library_section_id, folderpath)
        #logger.debug(ret)
        return ret
     
    @staticmethod
    def make_directories(library_section_id, path):
        data = PlexDBHandle.select2(f"SELECT id FROM directories WHERE library_section_id = ? AND path = ?", (library_section_id, path))
        if len(data) == 1:
            return data[0]['id']
        elif len(data) == 0:
            tmps = path.split('/')
            if len(tmps) == 1:
                parent_path = ''
            else:
                parent_path = '/'.join(tmps[:-1])

            parent_directory_id = Task.make_directories(library_section_id, parent_path)

            time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            updated_str = time_str
            try:
                updated_at_ce = Task.source_con.execute('SELECT updated_at FROM directories WHERE path = ?', (path,))
                updated_at_ce.row_factory = dict_factory
                tmp = updated_at_ce.fetchall()
                if len(tmp) == 1:
                    updated_str = tmp[0]['updated_at']
            except Exception as e: 
                logger.error(f'Exception:{str(e)}')
                logger.error(traceback.format_exc())
                

            path = path.replace("'", "''")
            query = f"INSERT INTO directories ('library_section_id','parent_directory_id','path','created_at','updated_at') VALUES ('{library_section_id}',{parent_directory_id},'{path}','{time_str}','{updated_str}');SELECT max(id) FROM directories;" 
            #logger.error(query)
            ret = PlexDBHandle.execute_query2(query)
            if ret != '':
                #logger.warning(f"path:{path} id:{ret}")
                return int(ret)
    
    @staticmethod
    def insert_media_parts(media_part, media_item_id, library_section_id):
        data = PlexDBHandle.select2(f"SELECT id FROM media_parts WHERE hash = ? AND media_item_id = ?", (media_part['hash'], media_item_id))
        #logger.error(data)
        if len(data) >= 1:
            return data[0]['id'], None
        elif len(data) == 0:
            file_ret = Task.process_localfile(media_part['file'], library_section_id)

            insert_col = ''
            insert_value = ''
            for key, value in media_part.items():
                if key in ['id']:
                    continue
                if key == 'media_item_id':
                    value = media_item_id
                if key == 'directory_id':
                    value = file_ret['dir_id']
                if key == 'file':
                    value = file_ret['new_filepath']
                if value is None:
                    continue
                insert_col += f"'{key}',"
                if type(value) == type(''):
                    insert_value += f'"{value}",'
                else:
                    insert_value += f"{value},"

            insert_col = insert_col.rstrip(',')
            insert_value = insert_value.rstrip(',')

            query = f"INSERT INTO media_parts ({insert_col}) VALUES ({insert_value});SELECT max(id) FROM media_parts;" 
            #logger.error(query)
            ret = PlexDBHandle.execute_query2(query)
            if ret != '':
                return int(ret), file_ret['new_filepath']
        else:
            logger.error("동일 정보가 여러가 있음")







    @staticmethod
    def insert_media_items(media_item, library_section_id, section_location_id, metadata_item_id, insert=True):
        data = PlexDBHandle.select2(f"SELECT id FROM media_items WHERE library_section_id = ? AND metadata_item_id = ? AND size = ? AND bitrate = ? AND hints = ?", (library_section_id, metadata_item_id, media_item['size'], media_item['bitrate'], media_item['hints']))
        #logger.error(data)
        
        if len(data) >= 1:
            return data[0]['id']
        elif len(data) == 0:
            if insert:
                insert_col = ''
                insert_value = ''
                for key, value in media_item.items():
                    if key in ['id']:
                        continue
                    if key == 'library_section_id':
                        value = library_section_id
                    if key == 'section_location_id':
                        value = section_location_id
                    if key == 'metadata_item_id':
                        value = metadata_item_id

                    if value is None:
                        #logger.error(f"null {key}")
                        continue
                    insert_col += f"'{key}',"
                    if type(value) == type(''):
                        insert_value += f'"{value}",'
                    else:
                        insert_value += f"{value},"

                insert_col = insert_col.rstrip(',')
                insert_value = insert_value.rstrip(',')

                query = f"INSERT INTO media_items ({insert_col}) VALUES ({insert_value});SELECT max(id) FROM media_items;" 
                #logger.error(query)
                ret = PlexDBHandle.execute_query2(query)
                if ret != '':
                    return int(ret)
            else:
                logger.error("insert 했으나 정보 없음")    
        else:
            logger.error("동일 정보가 여러가 있음")




    @staticmethod
    def insert_metadata_items(metadata_item, section_id, insert=True):
        data = PlexDBHandle.select2(f"SELECT id FROM metadata_items WHERE library_section_id = ? AND guid = ? AND hash = ?", (section_id, metadata_item['guid'], metadata_item['hash']))
        #logger.error(data)
        
        if len(data) >= 1:
            return data[0]['id'], True
        elif len(data) == 0:
            if insert:
                insert_col = ''
                insert_value = ''
                for key, value in metadata_item.items():
                    if key in ['id']:
                        continue
                    if key == 'library_section_id':
                        value = section_id

                    if value is None:
                        #logger.error(f"null {key}")
                        continue
                    insert_col += f"'{key}',"
                    if type(value) == type(''):
                        value = value.replace('"', '""')
                        insert_value += f'"{value}",'
                    else:
                        insert_value += f"{value},"

                insert_col = insert_col.rstrip(',')
                insert_value = insert_value.rstrip(',')

                query = f"INSERT INTO metadata_items({insert_col}) VALUES({insert_value});SELECT max(id) FROM metadata_items;" 
                #logger.error(query)
                ret = PlexDBHandle.execute_query2(query)
                if ret != '':
                    return int(ret), False
                #logger.warning(f"ret : {ret}")
                #self.insert_metadata_items(metadata_item, section_id, insert=False)
                #data = PlexDBHandle.select2(f"SELECT id FROM metadata_items WHERE library_section_id = ? AND guid = ? AND hash = ?", (section_id, metadata_item['guid'], metadata_item['hash']))
                #logger.error(data)
                
                #if len(data) == 1:
                #    return data[0]['id']

            else:
                logger.error("insert 했으나 정보 없음")    
        else:
            logger.error("동일 정보가 여러가 있음")
