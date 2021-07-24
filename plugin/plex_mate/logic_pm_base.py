# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, re, json, threading, time, shutil, platform
from datetime import datetime
# third-party
import requests, xmltodict, yaml
from flask import request, render_template, jsonify, redirect
# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util, path_app_root
from plugin import LogicModuleBase, default_route_socketio
from tool_base import ToolBaseFile, d, ToolSubprocess
# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting
name = 'base'

from .task_pm_base import Task
from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
#########################################################



class LogicPMBase(LogicModuleBase):
    db_default = {
        f'{name}_db_version' : '1',
        f'{name}_path_program' : '',
        f'{name}_path_data' : '',
        f'{name}_bin_scanner' : '',
        f'{name}_bin_sqlite' : '',
        f'{name}_path_db' : '',
        f'{name}_path_metadata' : '',
        f'{name}_path_media' : '',
        f'{name}_path_phototranscoder' : '',
        f'{name}_token' : '',
        f'{name}_url' : 'http://172.17.0.1:32400',
        f'{name}_backup_location_mode' : 'True',
        f'{name}_backup_location_manual' : '',
        f'{name}_path_config' : os.path.join(path_data, 'db', f'{package_name}_config.yaml')
    }



    def __init__(self, P):
        super(LogicPMBase, self).__init__(P, 'setting')
        self.name = name

    def plugin_load(self):
        config_path = ModelSetting.get(f'{name}_path_config')
        if os.path.exists(config_path) == False:
            shutil.copyfile(os.path.join(os.path.dirname(__file__), 'file', os.path.basename(config_path)), config_path)


    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        arg['sub'] = self.name
        arg['path_app_root'] = path_app_root
        try:
            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"{package_name}/{name}/{sub}")



    def process_ajax(self, sub, req):
        try:
            ret = {}
            if sub == 'command':
                command = req.form['command']
                if command == 'size':
                    #if req.form['arg1'] in ['plex_data', 'plex_db']:
                    path = req.form['arg2']
                    self.task_interface('size', (path,))
                    ret = {'ret':'success', 'msg':'명령을 전달하였습니다. 잠시 후 결과 알림을 확인하세요.'}
                elif command == 'execute':
                    if req.form['arg1'] == 'scanner':
                        data = ToolSubprocess.execute_command_return([req.form['arg2']])
                        data = data.replace('\n', '<br>').lstrip('"').rstrip('"')
                        ret['modal'] = data
                    elif req.form['arg1'] == 'sqlite':
                        data = []
                        data.append(f"SQLite 버전")
                        data.append(f" - {ToolSubprocess.execute_command_return([req.form['arg2'], '-version'])}")
                        data.append("")
                        data.append(f"Plex Media Server 버전")
                        data.append(f" - {ToolSubprocess.execute_command_return([req.form['arg2'], '--version'])}")
                        data = '<br>'.join(data)
                        ret['modal'] = data
                elif command == 'backup':
                    if req.form['arg1'] == 'plex_db':
                        self.task_interface('backup', (req.form['arg2'],))
                        ret = {'ret':'success', 'msg':'명령을 전달하였습니다. 잠시 후 결과 알림을 확인하세요.'}
                elif command == 'db':
                    if req.form['arg1'] == 'library_sections':
                        data = PlexDBHandle.library_sections(req.form['arg2'])
                        ret['modal'] = json.dumps(data, indent=4, ensure_ascii=False)
                elif command == 'clear':
                    if req.form['arg1'] == 'plex_phototranscode':
                        path = req.form['arg2']
                        self.task_interface('clear', (path,))
                        ret = {'ret':'success', 'msg':'명령을 전달하였습니다. 잠시 후 결과 알림을 확인하세요.'}
                elif command == 'system_agents':
                    data = PlexWebHandle.system_agents(url=req.form['arg1'], token=req.form['arg2'])
                    data = json.loads(json.dumps(xmltodict.parse(data)))
                    ret['modal'] = json.dumps(data, indent=4, ensure_ascii=False)
                elif command == 'version':
                    url = req.form['arg1']
                    token = req.form['arg2']
                    msg = f"SJVA.bundle : {PlexWebHandle.get_sjva_version(url=url, token=token)}<br>SjvaAgent : {PlexWebHandle.get_sjva_agent_version(url=url, token=token)}<br>"
                    regex = re.compile("VERSION\s=\s'(?P<version>.*?)'")
                    text = requests.get('https://raw.githubusercontent.com/soju6jan/SJVA.bundle/master/SJVA.bundle/Contents/Code/version.py').text
                    match = regex.search(text)
                    if match:
                        msg += u'SJVA.bundle (최신) : ' + match.group('version')
                    text = requests.get('https://raw.githubusercontent.com/soju6jan/SjvaAgent.bundle/main/Contents/Code/version.py').text
                    match = regex.search(text)
                    if match:
                        msg += u'<br>SjvaAgent (최신) : ' + match.group('version')
                    return jsonify({'ret':'success', 'msg':msg})
                    
            elif sub == 'plex_folder_test':
                program_path = req.form['program_path']
                data_path = req.form['data_path']
                if os.path.exists(program_path) == False:
                    ret = {'ret':'fail', 'msg':'데이터 폴더가 없습니다.'}
                elif os.path.exists(data_path) == False:
                    ret = {'ret':'fail', 'msg':'프로그램 폴더가 없습니다.'}
                else:
                    ret['data'] = {}
                    ret['data']['bin_scanner'] = os.path.join(program_path, 'Plex Media Scanner')
                    ret['data']['bin_sqlite'] = os.path.join(program_path, 'Plex SQLite')
                    ret['data']['path_db'] = os.path.join(data_path, 'Plug-in Support', 'Databases', 'com.plexapp.plugins.library.db')
                    ret['data']['path_metadata'] = os.path.join(data_path, 'Metadata')
                    ret['data']['path_media'] = os.path.join(data_path, 'Media')
                    ret['data']['path_phototranscoder'] = os.path.join(data_path, 'Cache', 'PhotoTranscoder')
                    xml_string = ToolBaseFile.read(os.path.join(data_path, 'Preferences.xml'))
                    result = xmltodict.parse(xml_string)
                    prefs = json.loads(json.dumps(result))
                    #logger.warning(d(prefs))
                    ret['data']['token'] = prefs['Preferences']['@PlexOnlineToken']

                    if platform.system() == 'Windows':
                        ret['data']['bin_scanner'] += '.exe'
                        ret['data']['bin_sqlite'] += '.exe'
                    for key, value in ret['data'].items():
                        if key != 'token':
                            if os.path.exists(ret['data'][key]) == False:
                                ret = {'ret':'fail', 'msg':'올바른 경로가 아닙니다.'}
                                return jsonify(ret)
                    ret['ret'] = 'success'
                    ret['msg'] = '설정을 저장하세요.'
            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
    #########################################################

    def task_interface(self, command, *args):
        def func():
            time.sleep(1)
            self.task_interface2(command, *args)
        th = threading.Thread(target=func, args=())
        th.setDaemon(True)
        th.start()


    def task_interface2(self, command, *args):
        if command == 'size':
            func = Task.get_size
        elif command == 'backup':
            func = Task.backup
        elif command == 'clear':
            func = Task.clear
        #ret = func(*args)
        
        if app.config['config']['use_celery']:
            result = func.apply_async(args)
            ret = result.get()
        else:
            ret = func(*args)

        if command == 'size':
            noti_data = {'type':'info', 'msg' : f"경로 : {ret['target']}<br>크기 : {ret['sizeh']}"}
            socketio.emit("notify", noti_data, namespace='/framework', broadcast=True)    
        elif command == 'backup':
            if ret['ret'] == 'success':
                noti_data = {'type':'info', 'msg' : f"경로 : {ret['target']}<br>복사하였습니다."}
            else:
                noti_data = {'type':'danger', 'msg' : f"백업에 실패하였습니다.<br>{ret['log']}"}
            socketio.emit("notify", noti_data, namespace='/framework', broadcast=True)    
        elif command == 'clear':
            noti_data = {'type':'info', 'msg' : f"경로 : {ret['target']}<br>크기 : {ret['sizeh']}"}
            socketio.emit("notify", noti_data, namespace='/framework', broadcast=True)    


    @staticmethod
    def load_config():
        with open(ModelSetting.get(f'{name}_path_config'), encoding='utf8') as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
        return config