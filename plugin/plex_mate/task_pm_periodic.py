# python
import os, sys, traceback, re, json, threading, time, shutil, fnmatch, glob, subprocess
from datetime import datetime, timedelta
# third-party
import requests

# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from plugin import LogicModuleBase, default_route_socketio
from tool_expand import ToolExpandFileProcess
from tool_base import ToolShutil, d, ToolUtil, ToolBaseFile, ToolOSCommand


from .plugin import P
from .model_periodic import ModelPeriodicItem
from .plex_db import PlexDBHandle
from .plex_bin_scanner import PlexBinaryScanner

logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting


class Task(object):
    
    @staticmethod
    @celery.task()
    def start(idx, mode):
        try:
            from .logic_pm_periodic import LogicPMPeriodic
            yaml = LogicPMPeriodic.get_jobs()[idx]

            db_item = ModelPeriodicItem()
            db_item.mode = mode
            db_item.section_id = yaml['섹션ID']
            section_data = PlexDBHandle.library_section(db_item.section_id)
            db_item.section_title = section_data['name']
            db_item.section_type = section_data['section_type']
            db_item.folder = yaml.get('폴더', None)

            query = f"""
            SELECT COUNT(media_parts.id) as cnt, MAX(media_parts.id) as max_part_id
            FROM metadata_items, media_items, media_parts 
            WHERE metadata_items.id = media_items.metadata_item_id AND media_items.id = media_parts.media_item_id AND media_parts.file != '' AND metadata_items.library_section_id = ?"""


            tmp = PlexDBHandle.select2(query, (db_item.section_id,))[0]
            #logger.error(f"시작 : {tmp}")
            db_item.part_before_max = tmp['max_part_id']
            db_item.part_before_count = tmp['cnt']

            timeout = yaml.get("최대실행시간", None)
            if timeout is not None:
                timeout = int(timeout)*60 
            
            PlexBinaryScanner.scan_refresh2(db_item.section_id, db_item.folder, timeout=timeout, db_item=db_item)
            db_item.finish_time = datetime.now()
            delta = db_item.finish_time - db_item.start_time
            db_item.duration = delta.seconds
            
            tmp = PlexDBHandle.select2(query, (db_item.section_id,))[0]
            #logger.error(f"종료 : {tmp}")
            db_item.part_after_max = tmp['max_part_id']
            db_item.part_after_count = tmp['cnt']
            db_item.part_append_count = db_item.part_after_count - db_item.part_before_count

            query = f"""
            SELECT media_parts.file as filepath, metadata_items.id as metadata_items_id
            FROM metadata_items, media_items, media_parts 
            WHERE metadata_items.id = media_items.metadata_item_id AND media_items.id = media_parts.media_item_id AND media_parts.file != '' AND metadata_items.library_section_id = ? AND media_parts.id > ? ORDER BY media_parts.id ASC"""
            tmp = PlexDBHandle.select2(query, (db_item.section_id, db_item.part_before_max))
            append_files = []
            for t in tmp:
                append_files.append(f"{t['metadata_items_id']}|{t['filepath']}")

            db_item.append_files = '\n'.join(append_files)
            db_item.save()

            if section_data['section_type'] == 2 and db_item.part_append_count > 0:
                query = 'UPDATE metadata_items SET added_at = (SELECT max(added_at) FROM metadata_items mi WHERE mi.parent_id = metadata_items.id OR mi.parent_id IN(SELECT id FROM metadata_items mi2 WHERE mi2.parent_id = metadata_items.id)) WHERE metadata_type = 2;'
                result = PlexDBHandle.execute_query(query)

        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())

