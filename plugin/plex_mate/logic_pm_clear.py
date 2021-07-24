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
from plugin import LogicModuleBase
from tool_base import ToolBaseFile, d, ToolSubprocess
# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting
name = 'clear'

from .task_pm_clear_movie import Task as TaskThumbMovie
from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
from .logic_pm_clear_library import LogicPMClearLibrary
from .logic_pm_clear_bundle import LogicPMClearBundle
#########################################################


class LogicPMClear(LogicModuleBase):
    def __init__(self, P):
        super(LogicPMClear, self).__init__(P, 'movie')
        self.name = name
        self.sub_list = {
            'movie' : LogicPMClearLibrary(P, self, 'movie'),
            'show' : LogicPMClearLibrary(P, self, 'show'),
            'bundle' : LogicPMClearBundle(P, self, 'bundle')
        }

    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        arg['sub'] = self.name
        arg['sub2'] = sub
        try:
            if sub == 'movie':
                arg['library_list'] = PlexDBHandle.library_sections(section_type=1)
            elif sub == 'show':
                arg['library_list'] = PlexDBHandle.library_sections(section_type=2)
            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"{package_name}/{name}/{sub}")


    def process_ajax(self, sub, req):
        try:
            ret = {}
            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
    
    def plugin_load(self):
        for key, value in self.sub_list.items():
            value.plugin_load()


    #########################################################
