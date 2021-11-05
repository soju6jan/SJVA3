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

                    query += f'UPDATE media_streams SET url = REPLACE(url, "{req.form["arg1"]}", "{req.form["arg2"]}");'

                    result = PlexDBHandle.execute_query(query)
                    if result:
                        ret = {'ret':'success', 'msg':'정상적으로 처리되었습니다.'}
                    else:
                        ret = {'ret':'warning', 'msg':'실패'}
                elif command == 'duplicate_list':
                    query = f"select metadata_items.id as meta_id, metadata_items.media_item_count,  media_items.id as media_id, media_parts.id as media_parts_id, media_parts.file from media_items, metadata_items, media_parts, (select media_parts.file as file, min(media_items.id) as media_id,  count(*) as cnt from media_items, metadata_items, media_parts where media_items.metadata_item_id = metadata_items.id and media_parts.media_item_id = media_items.id and metadata_items.media_item_count > 1 and media_parts.file != '' group by media_parts.file having cnt > 1) as ttt where media_items.metadata_item_id = metadata_items.id and media_parts.media_item_id = media_items.id and metadata_items.media_item_count > 1 and media_parts.file != '' and media_parts.file = ttt.file order by meta_id, media_id, media_parts_id;"
                    data = PlexDBHandle.select(query)
                    ret['modal'] = json.dumps(data, indent=4, ensure_ascii=False)
                elif command == 'duplicate_remove':
                    query = f"select metadata_items.id as meta_id, metadata_items.media_item_count,  media_items.id as media_id, media_parts.id as media_parts_id, media_parts.file from media_items, metadata_items, media_parts, (select media_parts.file as file, min(media_items.id) as media_id,  count(*) as cnt from media_items, metadata_items, media_parts where media_items.metadata_item_id = metadata_items.id and media_parts.media_item_id = media_items.id and metadata_items.media_item_count > 1 and media_parts.file != '' group by media_parts.file having cnt > 1) as ttt where media_items.metadata_item_id = metadata_items.id and media_parts.media_item_id = media_items.id and metadata_items.media_item_count > 1 and media_parts.file != '' and media_parts.file = ttt.file order by meta_id, media_id, media_parts_id;"
                    data = PlexDBHandle.select(query)
                    prev = None
                    filelist = []
                    query = ''
                    def delete_medie(meta_id, media_id):
                        tmp = f"DELETE FROM media_streams WHERE media_item_id = {media_id};\n"
                        tmp += f"DELETE FROM media_parts WHERE media_item_id = {media_id};\n"
                        tmp += f"DELETE FROM media_items WHERE id = {media_id};\n"
                        tmp += f"UPDATE metadata_items SET media_item_count = (SELECT COUNT(*) FROM media_items WHERE metadata_item_id = {meta_id}) WHERE id = {meta_id};\n"
                        return tmp
                    def delete_part(part_id):
                        tmp = f"DELETE FROM media_streams WHERE media_part_id = {part_id};\n"
                        tmp += f"DELETE FROM media_parts WHERE id = {part_id};\n"
                        return tmp
                    for idx, current in enumerate(data):
                        try:
                            if prev is None:
                                continue
                            if current['meta_id'] != prev['meta_id'] and current['file'] in filelist:
                                logger.warning(d(current))
                                pass
                            if current['meta_id'] == prev['meta_id'] and current['file'] == prev['file']:
                                if current['media_id'] != prev['media_id']:
                                    query += delete_medie(current['meta_id'], current['media_id'])
                                elif current['media_parts_id'] != prev['media_parts_id']:
                                    query += delete_part(current['media_parts_id'])

                        finally:     
                            if current['file'] not in filelist:
                                filelist.append(current['file'])
                            prev = current
                    if query != '':
                        logger.warning(query)
                        result = PlexDBHandle.execute_query(query)
                        if result:
                            ret = {'ret':'success', 'msg':'정상적으로 처리되었습니다.'}
                        else:
                            ret = {'ret':'warning', 'msg':'실패'}
                    else:
                        ret = {'ret':'success', 'msg':'처리할 내용이 없습니다.'}
                elif command == 'equal_file_equal_meta':
                    query = f"""select media_parts.file, replace(media_parts.file, rtrim(media_parts.file, replace(media_parts.file, '/', '')), '') AS filename from media_parts, metadata_items, media_items, (SELECT metadata_items.id as id, replace(media_parts.file, rtrim(media_parts.file, replace(media_parts.file, '/', '')), '') AS filename, count(*) AS cnt FROM metadata_items, media_items, media_parts WHERE metadata_items.id = media_items.metadata_item_id AND media_items.id = media_parts.media_item_id AND metadata_items.library_section_id = 18 GROUP BY filename HAVING cnt > 1 ORDER BY file) AS tmp where metadata_items.id = media_items.metadata_item_id AND media_items.id = media_parts.media_item_id AND metadata_items.library_section_id = {req.form['arg1']} and media_parts.file != '' and filename = tmp.filename and metadata_items.id = tmp.id order by file"""

                    #logger.error(query)
                    data = PlexDBHandle.select(query)
                    ret['modal'] = json.dumps(data, indent=4, ensure_ascii=False)
                elif command == 'empty_episode_process':
                    section_id = req.form['arg1']
                    #P.logic.get_module('base').task_interface('empty_episode_process', (section_id,))
                    #ret = {'ret':'success', 'msg':'시작합니다.'}
                    #query = f"""UPDATE metadata_items as A SET user_thumb_url = (SELECT user_art_url FROM metadata_items as B WHERE id in (SELECT parent_id FROM metadata_items WHERE A.id = b.parent_id AND library_section_id = {section_id} AND (user_thumb_url = '' or user_thumb_url LIKE 'media%'))) WHERE library_section_id = {section_id} AND (user_thumb_url = '' or user_thumb_url LIKE 'media%');"""
                    # null로 세팅하면 부모것을 사용함
                    query = f"""UPDATE metadata_items as A SET user_thumb_url = (SELECT user_art_url FROM metadata_items WHERE id in (SELECT parent_id FROM metadata_items as B WHERE id in (SELECT parent_id FROM metadata_items WHERE A.id = b.parent_id AND library_section_id = {section_id} AND (user_thumb_url = '' or user_thumb_url LIKE 'media%')))) WHERE library_section_id = {section_id} AND (user_thumb_url = '' or user_thumb_url LIKE 'media%')"""


                    result = PlexDBHandle.execute_query(query)
                    if result:
                        ret = {'ret':'success', 'msg':'정상적으로 처리되었습니다.'}
                    else:
                        ret = {'ret':'warning', 'msg':'실패'}
                elif command == 'remove_trash':
                    section_id = req.form['arg1']
                    query = f"""UPDATE metadata_items SET deleted_at = null WHERE deleted_at is not null AND library_section_id = {section_id};
                    UPDATE media_items SET deleted_at = null WHERE deleted_at is not null AND library_section_id = {section_id};
                    UPDATE media_parts SET deleted_at = null WHERE deleted_at is not null AND media_item_id in (SELECT id FROM media_itmes WHERE library_section_id = {section_id});"""
                    result = PlexDBHandle.execute_query(query)
                    logger.error(result)
                    if result:
                        ret = {'ret':'success', 'msg':'정상적으로 처리되었습니다.'}
                    else:
                        ret = {'ret':'warning', 'msg':'실패'}

            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
  


    #########################################################
