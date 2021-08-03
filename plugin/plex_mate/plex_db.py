# python
import os, sys, traceback, re, json, threading, time, shutil, fnmatch, glob, platform
from datetime import datetime, timedelta
# third-party
import requests, sqlite3

# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from framework.common.plugin import LogicModuleBase, default_route_socketio
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

class PlexDBHandle(object):
    
    @classmethod
    def library_sections(cls, db_file=None, section_type=None):
        try:
            if db_file is None:
                db_file = ModelSetting.get('base_path_db')
            con = sqlite3.connect(db_file)
            cur = con.cursor()
            if section_type is None:
                ce = con.execute('SELECT * FROM library_sections ORDER BY name, created_at')
            else:
                ce = con.execute('SELECT * FROM library_sections WHERE section_type = ? ORDER BY name, created_at', (section_type,))
            ce.row_factory = dict_factory
            data = ce.fetchall()
            con.close()
            return data
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())

    @classmethod
    def library_section(cls, library_id, db_file=None):
        try:
            library_id = int(library_id)
            if db_file is None:
                db_file = ModelSetting.get('base_path_db')
            con = sqlite3.connect(db_file)
            cur = con.cursor()
            ce = con.execute('SELECT * FROM library_sections WHERE id = ?', (library_id,))
            ce.row_factory = dict_factory
            data = ce.fetchone()
            con.close()
            return data
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())


    @classmethod
    def execute_query(cls, sql, sql_filepath=None):
        try:
            if sql_filepath is None:
                sql_filepath = os.path.join(path_data, 'tmp', f"{str(time.time()).split('.')[0]}.sql")
            ToolBaseFile.write(sql, sql_filepath)
            if platform.system() == 'Windows':
                tmp = sql_filepath.replace('\\', '\\\\')
                cmd = f'"{ModelSetting.get("base_bin_sqlite")}" "{ModelSetting.get("base_path_db")}" ".read {tmp}"'
                ToolSubprocess.execute_command_return(cmd)
            else:
                ToolSubprocess.execute_command_return([ModelSetting.get('base_bin_sqlite'), ModelSetting.get('base_path_db'), f".read {sql_filepath}"])
            return True
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
        return False   


    @classmethod
    def execute_query2(cls, sql, sql_filepath=None):
        try:
            if sql_filepath is None:
                sql_filepath = os.path.join(path_data, 'tmp', f"{str(time.time()).split('.')[0]}.sql")
            ToolBaseFile.write(sql, sql_filepath)
            if platform.system() == 'Windows':
                tmp = sql_filepath.replace('\\', '\\\\')
                cmd = f'"{ModelSetting.get("base_bin_sqlite")}" "{ModelSetting.get("base_path_db")}" ".read {tmp}"'
                ret = ToolSubprocess.execute_command_return(cmd)
            else:
                ret = ToolSubprocess.execute_command_return([ModelSetting.get('base_bin_sqlite'), ModelSetting.get('base_path_db'), f".read {sql_filepath}"])
            return ret
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
        return '' 

    @classmethod
    def select(cls, query, db_file=None):
        try:
            if db_file is None:
                db_file = ModelSetting.get('base_path_db')
            con = sqlite3.connect(db_file)
            cur = con.cursor()
            ce = con.execute(query)
            ce.row_factory = dict_factory
            data = ce.fetchall()
            con.close()
            return data

        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
        return   

    

    @classmethod
    def select2(cls, query, args, db_file=None):
        try:
            if db_file is None:
                db_file = ModelSetting.get('base_path_db')
            con = sqlite3.connect(db_file)
            cur = con.cursor()
            logger.error(args)
            if len(args) == 0:
                ce = con.execute(query)
            else:
                ce = con.execute(query, args)
            ce.row_factory = dict_factory
            data = ce.fetchall()
            con.close()
            return data

        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
        return   
        
    @classmethod
    def tool_select(cls, where, db_file=None):
        con = cur = None
        try:
            if db_file is None:
                db_file = ModelSetting.get('base_path_db')
            con = sqlite3.connect(db_file)
            cur = con.cursor()

            query = """
            SELECT 
                metadata_items.id AS metadata_items_id, 
                metadata_items.library_section_id AS library_section_id, 
                metadata_items.metadata_type AS metadata_type, 
                metadata_items.guid AS guid,
                metadata_items.media_item_count AS media_item_count,
                metadata_items.title AS title,
                metadata_items.year AS year,
                metadata_items.'index' AS metadata_items_index,
                metadata_items.user_thumb_url AS user_thumb_url,
                metadata_items.user_art_url AS user_art_url,
                metadata_items.hash AS metadata_items_hash,
                media_items.id AS media_items_id,
                media_items.section_location_id AS section_location_id,
                media_items.width AS width,
                media_items.height AS height,
                media_items.size AS size,
                media_items.duration AS duration,
                media_items.bitrate AS bitrate,
                media_items.container AS container,
                media_items.video_codec AS video_codec,
                media_items.audio_codec AS audio_codec,
                media_parts.id AS media_parts_id,
                media_parts.directory_id AS media_parts_directory_id,
                media_parts.hash AS media_parts_hash,
                media_parts.file AS file
            FROM metadata_items, media_items, media_parts 
            WHERE metadata_items.id = media_items.metadata_item_id AND media_items.id = media_parts.media_item_id """
            if where is not None and where != '':
                query = query + ' AND (' + where + ') '
            query += ' LIMIT 100'


            #logger.warning(query)

            ce = con.execute(query)
            ce.row_factory = dict_factory
            data = ce.fetchall()
            cur.close
            con.close()
            cur = con = None
            return {'ret':'success', 'data':data}

        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            return {'ret':'exception', 'log':str(e)}
        finally:
            if cur is not None:
                cur.close()
            if con is not None:
                con.close()   
