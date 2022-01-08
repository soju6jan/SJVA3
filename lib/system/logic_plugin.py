# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import logging
import json
import zipfile
import time
import platform
# third-party
import requests
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify
from flask_login import login_user, logout_user, current_user, login_required

# sjva 공용
from framework.logger import get_logger, set_level
from framework import app, db, scheduler, version, path_app_root, path_data, USERS
from framework.util import Util

# 패키지
from .model import ModelSetting
import system
# 로그
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
#########################################################



class LogicPlugin(object):
    plugin_loading = False
    
    

    current_loading_plugin_list = {}
    
    """
    custom_plugin_list = []
    @staticmethod
    def loading():
        try:
            custom_path = os.path.join(path_data, 'custom')
            plugin_list = os.listdir(custom_path)
            logger.debug(plugin_list)
            for name in plugin_list:
                try:
                    p = {}
                    p['name'] = name
                    p['plugin_name'] = name
                    mod = __import__('%s' % (p['plugin_name']), fromlist=[])
                    p['local_info'] = getattr(mod, 'plugin_info')
                    p['status'] = 'latest'
                    LogicPlugin.custom_plugin_list.append(p)
                except Exception as exception: 
                    logger.error('NO Exception:%s', exception)
                    logger.debug('plunin not import : %s', p['plugin_name'])
                    p['local_info'] = None
                    p['status'] = 'no'         
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    """

    @staticmethod
    def get_plugin_list():
        return LogicPlugin.current_loading_plugin_list
        """
        try:
            if not LogicPlugin.plugin_loading:
                LogicPlugin.loading()
                LogicPlugin.plugin_loading = True
            return LogicPlugin.custom_plugin_list
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        """

    
    @staticmethod
    def get_plugin_info(plugin_name):
        try:
            lists = LogicPlugin.get_plugin_list()
            for key, value in lists.items():
                if key == plugin_name:
                    return value['info']
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    

    """
    @staticmethod
    def plugin_install(plugin_name):
        logger.debug('plugin_name : %s', plugin_name)
        try:
            plugin_info = LogicPlugin.get_plugin_info(plugin_name)
            
            custom_path = os.path.join(path_data, 'custom')

            if 'platform' in plugin_info:
                if platform.system() not in plugin_info['platform']:
                    return 'not_support_os'
            if 'running_type' in  plugin_info:
                if app.config['config']['running_type'] not in plugin_info['running_type']:
                    return 'not_support_running_type'
            git_clone_flag = True
            if git_clone_flag:
                # git clone
                command = ['git', '-C', custom_path, 'clone', plugin_info['git'], '--depth', '1']
                ret = Util.execute_command(command)
            return 'success'
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    """

    @staticmethod
    def plugin_uninstall(plugin_name):
        logger.debug('plugin_name : %s', plugin_name)
        try:
            mod = __import__('%s' % (plugin_name), fromlist=[])
            mod_plugin_unload = getattr(mod, 'plugin_unload')
            mod_plugin_unload()
            time.sleep(1)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        try:
            custom_path = os.path.join(path_data, 'custom')
            plugin_path = os.path.join(custom_path, plugin_name)
            if os.path.exists(plugin_path):
                try:
                    import framework.common.celery as celery_task
                    celery_task.rmtree(plugin_path)
                except Exception as exception: 
                    try:
                        logger.debug('plugin_uninstall')
                        os.system('rmdir /S /Q "%s"' % plugin_path)
                    except:
                        logger.error('Exception:%s', exception)
                        logger.error(traceback.format_exc())
            if os.path.exists(plugin_path):
                return 'fail'
            else:
                return 'success'
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @staticmethod
    def custom_plugin_update():
        try:
            if os.environ.get('UPDATE_STOP') == 'true':
                return
            if os.environ.get('PLUGIN_UPDATE_FROM_PYTHON') == 'false':
                return
            custom_path = os.path.join(path_data, 'custom')
            tmps = os.listdir(custom_path)
            for t in tmps:
                plugin_path = os.path.join(custom_path, t)
                try:
                    if t == 'torrent_info':
                        os.remove(os.path.join(plugin_path, 'info.json'))
                except:
                    pass
                if t.startswith('_'):
                    continue
                if os.path.exists(os.path.join(plugin_path, '.git')):
                    command = ['git', '-C', plugin_path, 'reset', '--hard', 'HEAD']
                    ret = Util.execute_command(command)
                    command = ['git', '-C', plugin_path, 'pull']
                    ret = Util.execute_command(command)
                    logger.debug("%s\n%s", plugin_path, ret)
                else:
                    logger.debug(f"plugin_path is not git repo")
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    

    @staticmethod
    def plugin_install_by_api(plugin_git, zip_url, zip_filename):
        logger.debug('plugin_git : %s', plugin_git)
        logger.debug('zip_url : %s', zip_url)
        logger.debug('zip_filename : %s', zip_filename)
        
        is_git = True if plugin_git != None and plugin_git != '' else False
        ret = {}
        try:
            if is_git:
                name = plugin_git.split('/')[-1]
            else:
                name = zip_filename.split('.')[0]
            
            custom_path = os.path.join(path_data, 'custom')
            plugin_path = os.path.join(custom_path, name)
            logger.debug(plugin_path)
            plugin_info = {}
            if os.path.exists(plugin_path):
                ret['ret'] = 'already_exist'
                ret['log'] = '이미 설치되어 있습니다.'
            else:
                if plugin_git and plugin_git.startswith('http'):
                    for tag in ['master', 'main']:
                        try:
                            info_url = plugin_git.replace('github.com', 'raw.githubusercontent.com') + '/%s/info.json' % tag
                            plugin_info = requests.get(info_url).json()
                            if plugin_info is not None:
                                break
                        except:
                            pass
                if zip_filename and zip_filename != '':
                    import zipfile
                    from tool_base import ToolBaseFile
                    zip_filepath = os.path.join(path_data, 'tmp', zip_filename)
                    extract_filepath = os.path.join(path_data, 'tmp', name)
                    logger.error(zip_url)
                    logger.warning(zip_filepath)
                    if ToolBaseFile.download(zip_url, zip_filepath):
                        #logger.warning(os.path.exists(zip_filepath))
                        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                            zip_ref.extractall(extract_filepath)
                        plugin_info_filepath = os.path.join(extract_filepath, 'info.json')
                        if os.path.exists(plugin_info_filepath):
                            plugin_info = ToolBaseFile.read_json(plugin_info_filepath)
                        else:
                            plugin_info = {}

                flag = True
                if 'platform' in plugin_info:
                    if platform.system() not in plugin_info['platform']:
                        ret['ret'] = 'not_support_os'
                        ret['log'] = '설치 가능한 OS가 아닙니다.'
                        flag = False
                if flag and 'running_type' in  plugin_info:
                    if app.config['config']['running_type'] not in plugin_info['running_type']:
                        ret['ret'] = 'not_support_running_type'
                        ret['log'] = '설치 가능한 실행타입이 아닙니다.'
                        flag = False
                if flag and 'policy_level' in plugin_info:
                    if plugin_info['policy_level'] > app.config['config']['level']:
                        ret['ret'] = 'policy_level'
                        ret['log'] = '설치 가능 회원등급보다 낮습니다.'
                        flag = False
                if flag and 'policy_point' in plugin_info:
                    if plugin_info['policy_level'] > app.config['config']['point']:
                        ret['ret'] = 'policy_level'
                        ret['log'] = '설치 가능 포인트보다 낮습니다.'
                        flag = False

                if flag:
                    if plugin_git and plugin_git.startswith('http'):
                        command = ['git', '-C', custom_path, 'clone', plugin_git + '.git', '--depth', '1']
                        log = Util.execute_command(command)
                    if zip_filename and zip_filename != '':
                        import shutil
                        if os.path.exists(plugin_path) == False:
                            shutil.move(extract_filepath, plugin_path)
                        else:
                            for tmp in os.listdir(extract_filepath):
                                shutil.move(os.path.join(extract_filepath, tmp), plugin_path)
                        log = ''
                    logger.debug(plugin_info)
                    # 2021-12-31
                    if 'dependency' in plugin_info:
                        for dep in plugin_info['dependency']:
                            for key, value in LogicPlugin.get_plugin_list().items():
                                if key == dep['name']:
                                    logger.debug(f"Dependency 설치 - 이미 설치됨 : {dep['name']}")
                                    break
                            else:
                                logger.debug(f"Dependency 설치 : {dep['home']}")
                                LogicPlugin.plugin_install_by_api(dep['home'], dep.get('zip_url'), dep.get('zip_filename'))
                                #command = ['git', '-C', custom_path, 'clone', dep['home'], '--depth', '1']
                                #ret = Util.execute_command(command)
                    ret['ret'] = 'success'
                    ret['log'] = [u'정상적으로 설치하였습니다. 재시작시 적용됩니다.', log]
                    ret['log'] = '<br>'.join(ret['log'])
                
                    
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            ret['ret'] = 'exception'
            ret['log'] = str(exception)
        
            
        return ret
        