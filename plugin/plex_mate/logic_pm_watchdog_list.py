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
from tool_base import ToolBaseFile, d, ToolSubprocess, ToolShutil
# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting

from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
from .plex_bin_scanner import PlexBinaryScanner
#########################################################



class LogicPMWatchdogList(LogicSubModuleBase):

    def __init__(self, P, parent, name):
        super(LogicPMWatchdogList, self).__init__(P, parent, name)
        self.db_default = {
            f'{self.parent.name}_{self.name}_db_version' : '1',
        }


    def process_ajax(self, sub, req):
        try:
            ret = {'ret':'success'}
            if sub == 'command':
                command = req.form['command']
                logger.error(f"sub : {sub}  /  command : {command}")
            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
  


    #########################################################
