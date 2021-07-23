# python
import os, sys, traceback, re, json, threading, time, shutil, fnmatch, glob
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

    @classmethod
    def library_section(cls, library_id, db_file=None):
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


    @classmethod
    def execute_query(cls, sql, sql_filepath=None):
        try:
            if sql_filepath is None:
                sql_filepath = os.path.join(path_data, 'tmp', f"{str(time.time()).split('.')[0]}.sql")
            ToolBaseFile.write(sql, sql_filepath)
            ToolSubprocess.execute_command_return([ModelSetting.get('base_bin_sqlite'), ModelSetting.get('base_path_db'), f".read {sql_filepath}"])
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        return False   


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

        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        return   

       