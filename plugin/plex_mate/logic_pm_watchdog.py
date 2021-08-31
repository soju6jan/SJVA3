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
from plugin import LogicModuleBase, default_route_socketio
from tool_base import ToolBaseFile, d, ToolSubprocess
# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting
name = 'watchdog'

from .task_pm_base import Task
from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
from .logic_pm_watchdog_setting import LogicPMWatchdogSetting
from .logic_pm_watchdog_list import LogicPMWatchdogList
#########################################################

class LogicPMWatchdog(LogicModuleBase):
    db_default = None

    def __init__(self, P):
        super(LogicPMWatchdog, self).__init__(P, 'setting')
        self.name = name
        self.sub_list = {
            'setting' : LogicPMWatchdogSetting(P, self, 'setting'),
            'list' : LogicPMWatchdogList(P, self, 'list'),
        }

    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        arg['sub'] = self.name
        arg['sub2'] = sub 
        try:
            if sub == 'setting':
                arg['scheduler'] = str(scheduler.is_include(self.sub_list[sub].get_scheduler_name()))
                arg['is_running'] = str(scheduler.is_running(self.sub_list[sub].get_scheduler_name()))
            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"{package_name}/{name}/{sub}")
