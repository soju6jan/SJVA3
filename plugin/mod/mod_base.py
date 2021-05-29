# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, re, json, threading, time, shutil, datetime, platform
# third-party
import requests
from flask import request, render_template, jsonify, redirect
# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from framework.common.plugin import LogicModuleBase, default_route_socketio
from tool_base import ToolBaseFile
#########################################################
from .plugin import P
name = 'base'
logger = P.logger
ModelSetting = P.ModelSetting
package_name = P.package_name

class ModuleBase(LogicModuleBase):
    db_default = {
        f'{name}_db_version' : '1',
        f'{name}_mod_order' : '',
        f'{name}_mod_root_path' : os.path.join(path_data, 'module'),
    }
    
    def __init__(self, P):
        super(ModuleBase, self).__init__(P, 'total')
        self.name = name
        self.module_list_install = None
        self.module_list_total = None
    

    def process_menu(self, sub, req):
        arg = ModelSetting.to_dict()
        arg['sub'] = self.name
        arg['sub2'] = sub
        try:
            return render_template(f"{package_name}_{self.name}_{sub}.html", arg=arg)
        except:
            return render_template('sample.html', title=f'{package_name} - {sub}')

    def process_ajax(self, sub, req):
        try:
            ret = {'ret':'success'}
            if sub == 'send_command':
                sub2 = req.form['sub2']
                command = req.form['command']
                arg1 = req.form['arg1'] 
                arg2 = req.form['arg2'] 

                if command == 'module_list':
                    if sub2 == 'total':
                        if arg1 == 'refresh' or self.module_list_total is None:
                            self.make_module_list()
                            ret = {'ret':'success', 'msg':'새로고침 하였습니다.'}
                        ret['module_list'] = self.module_list_total
                elif command == 'module_install':
                    self.module_install(arg1)
                    ret['msg'] = "설치중입니다."
                elif command == 'module_remove':
                    self.module_remove(arg1)
                    ret['msg'] = "삭제중입니다."
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
                    
                    

    ############################################### 

    def module_install(self, module_name):
        try:
            def func():
                from system.logic_command2 import SystemLogicCommand2
                return_log = SystemLogicCommand2(f"{module_name} 모듈 설치", [
                    ['msg', u'잠시만 기다려주세요.'],
                ], wait=True, show_modal=True, clear=True).start()

                mod_data = self.find_module_from_total(module_name)
                if mod_data is None:
                    socketio.emit("command_modal_add_text", f"{module_name} 정보 없음\n\n", namespace='/framework', broadcast=True)
                else:
                    mod_root_path = ModelSetting.get(f'{name}_mod_root_path')
                    if not os.path.exists(mod_root_path):
                        os.makedirs(mod_root_path)
                    
                    mod_path = os.path.join(mod_root_path, module_name)
                    if os.path.exists(mod_path):
                        socketio.emit("command_modal_add_text", f"{mod_path} 폴더 삭제\n\n", namespace='/framework', broadcast=True)
                        shutil.rmtree(mod_path)

                    socketio.emit("command_modal_add_text", f"{mod_path} 폴더 생성\n\n", namespace='/framework', broadcast=True)
                    os.makedirs(mod_path)

                    commands = []
                    for idx, _file in enumerate(mod_data['files']):
                        commands.append(['msg', f"{idx+1}/{len(mod_data['files'])} 파일 다운로드 : {_file[0]}"])

                        commands.append(['curl', '-Lo', os.path.join(mod_path, _file[0]), _file[1]])

                    if platform.system() != 'Windows':
                        commands.append(['chmod', '777', '-R', mod_root_path])
                    commands.append(['msg', '재시작 후 적용됩니다.'])
                    return_log = SystemLogicCommand2(f"{module_name} 모듈 설치", commands, wait=True, show_modal=True, clear=False).start()
                    mod_order = ModelSetting.get_list(f"{name}_mod_order", ',')
                    if module_name not in mod_order:
                        mod_order.append(module_name)
                        ModelSetting.set(f"{name}_mod_order", ','.join(mod_order))

                return_log = SystemLogicCommand2(f"{module_name} 모듈 설치", [
                    ['msg', u'\n설치 완료..'],
                ], wait=True, show_modal=True, clear=False).start()

            th = threading.Thread(target=func)
            th.setDaemon(True)
            th.start() 


        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    def module_remove(self, module_name):
        try:
            def func():
                from system.logic_command2 import SystemLogicCommand2
                return_log = SystemLogicCommand2(f"{module_name} 모듈 삭제", [
                    ['msg', u'잠시만 기다려주세요.'],
                ], wait=True, show_modal=True, clear=True).start()

                mod_data = self.find_module_from_total(module_name)
                if mod_data is None:
                    socketio.emit("command_modal_add_text", f"{module_name} 정보 없음\n\n", namespace='/framework', broadcast=True)
                else:
                    mod_root_path = ModelSetting.get(f'{name}_mod_root_path')
                    mod_path = os.path.join(mod_root_path, module_name)
                    if os.path.exists(mod_path):
                        socketio.emit("command_modal_add_text", f"{mod_path} 폴더 삭제\n\n", namespace='/framework', broadcast=True)
                        shutil.rmtree(mod_path)
                    mod_order = ModelSetting.get_list(f"{name}_mod_order", ',')
                    new = []
                    for tmp in mod_order:
                        if module_name != tmp:
                            new.append(tmp)
                    ModelSetting.set(f"{name}_mod_order", ','.join(new))
                return_log = SystemLogicCommand2(f"{module_name} 모듈 삭제", [
                    ['msg', '재시작 후 적용됩니다.'],
                    ['msg', u'\n삭제 완료..'],
                ], wait=True, show_modal=True, clear=False).start()

            th = threading.Thread(target=func)
            th.setDaemon(True)
            th.start() 


        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())



    def find_module_from_total(self, module_name):
        for mod in self.module_list_total:
            if mod['name'] == module_name:
                return mod


    def make_module_list(self):
        url = 'https://sjva.me/p/module/home/0'
        data = requests.get(url).json()
        #logger.warning(self.dump(data))
        for mod in data:
            for install_mod in self.module_list_install:
                if mod['name'] == install_mod['name']:
                    mod['install'] = install_mod
                    break
        self.module_list_total = data
        

    def init_mod_list(self):
        self.module_list_install = []
        mod_dir_list = []
        ret = []
        try:
            mod_root_path = ModelSetting.get(f'{name}_mod_root_path')
            if not os.path.exists(mod_root_path):
                return
            mod_list = os.listdir(mod_root_path)
            sys.path.insert(0, mod_root_path)
            logger.warning(mod_list)
            tmp_module_list = []
            for mod_name in mod_list:
                try:
                    if mod_name.startswith('_'):
                        continue
                    mod = __import__(mod_name, fromlist=[])
                    try:
                        mod_dir_list.append(os.path.join(mod_root_path, mod_name))
                        mod_info = getattr(mod, 'mod_info')
                        mod_info['name'] = mod_info['sub'][0]
                        tmp_module_list.append(mod_info)
                    except Exception as exception:
                        logger.error('Exception:%s', exception)
                        logger.error(traceback.format_exc())
                        logger.debug('no mod_name : %s', mod_name)
                except Exception as exception:
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())
                    continue
            
            try:
                for order in ModelSetting.get_list(f"{name}_mod_order", ','):
                    for idx, mod in enumerate(tmp_module_list):
                        if order == mod['name']:
                            self.module_list_install.append(mod)
                            del tmp_module_list[idx]
                            break
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
                

            self.module_list_install += tmp_module_list
            for mod_info in self.module_list_install:
                try:
                    P.menu['sub'].insert(-1, mod_info['sub'])
                    if 'sub2' in mod_info:
                        P.menu['sub2'][mod_info['sub'][0]] = mod_info['sub2']
                    mod_instance = mod_info['mod_class'](P)
                    P.module_list.append(mod_instance)
                    del mod_info['mod_class']
                    #logger.info(f"module loading : {mod_info['sub'][0]}")
                except Exception as exception:
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())
            
            import jinja2 
            my_loader = jinja2.ChoiceLoader([
                app.jinja_loader,
                jinja2.FileSystemLoader(mod_dir_list),
            ])
            app.jinja_loader = my_loader

            from framework import get_menu_map
            menu_map = get_menu_map()
            for tmp in menu_map[-1]['list']:
                if tmp['type'] == 'plugin' and tmp['plugin'] == 'mod':
                    tmp['sub'] = P.menu['sub']
                    tmp['sub2'] = P.menu['sub2']
                    break
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
       