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


from .task_pm_dbcopy_copy import Task
from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
from .logic_pm_base import LogicPMBase
#########################################################


class LogicPMDbCopyCopy(LogicSubModuleBase):
    
    def __init__(self, P, parent, name):
        super(LogicPMDbCopyCopy, self).__init__(P, parent, name)
        self.db_default = {
            f'{self.parent.name}_{self.name}_db_version' : '1',
            f'{self.parent.name}_{self.name}_path_source_db' : '',
            f'{self.parent.name}_{self.name}_source_section_id' : '',
            f'{self.parent.name}_{self.name}_path_source_root_path' : '',
            f'{self.parent.name}_{self.name}_path_target_root_path' : '',
            f'{self.parent.name}_{self.name}_target_section_id' : '',
            f'{self.parent.name}_{self.name}_target_section_location_id' : '',
            f'{self.parent.name}_{self.name}_dir_updated_mode' : '0',
            f'{self.parent.name}_{self.name}_task_stop_flag' : 'False',
        }
        self.data = {
            'list' : [],
            'status' : {'is_working':'wait'}
        }
        default_route_socketio_sub(P, parent, self)


    def process_ajax(self, sub, req):
        try:
            ret = {}
            if sub == 'command':
                command = req.form['command']
                if command == 'source_section':
                    data = PlexDBHandle.library_sections(db_file=req.form['arg1'])
                    ret['modal'] = d(data)
                elif command == 'target_section_id':
                    data = PlexDBHandle.library_sections()
                    ret['modal'] = d(data)
                elif command == 'target_section_location_id':
                    logger.warning(req.form['arg1'])
                    data = PlexDBHandle.select2('SELECT * FROM section_locations WHERE library_section_id = ?', (req.form['arg1'],))
                    ret['modal'] = d(data)
                elif command == 'select_source_locations':
                    data = PlexDBHandle.select('SELECT * FROM section_locations', db_file=req.form['arg1'])
                    ret['modal'] = d(data)
                elif command == 'select_target_locations':
                    data = PlexDBHandle.select('SELECT * FROM section_locations')
                    ret['modal'] = d(data)
            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
