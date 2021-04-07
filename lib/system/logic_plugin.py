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
    """
    custom_plugin_list = [
        {
            'name' : 'torrent_info',
            'plugin_name' : 'torrent_info_sjva',
            'json_url' : 'https://raw.githubusercontent.com/wiserain/torrent_info_sjva/master/info.json',
            'git' : 'https://github.com/wiserain/torrent_info_sjva.git',
        },
        {
            'name' : 'hdhomerun',
            'plugin_name' : 'hdhomerun_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/hdhomerun_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/hdhomerun_sjva.git',
        },
        {
            'name' : 'nsearch',
            'plugin_name' : 'nsearch_sjva',
            'json_url' : 'https://raw.githubusercontent.com/starbuck15/nsearch_sjva/master/info.json',
            'git' : 'https://github.com/starbuck15/nsearch_sjva.git',
        },
        {
            'name' : 'tving',
            'plugin_name' : 'tving_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/tving_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/tving_sjva.git',
        },
        {
            'name' : 'wavve',
            'plugin_name' : 'wavve_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/wavve_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/wavve_sjva.git',
        },
        {
            'name' : 'ani24',
            'plugin_name' : 'ani24_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/ani24_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/ani24_sjva.git',
        },
        {
            'name' : 'telegram_receiver',
            'plugin_name' : 'telegram_receiver_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/telegram_receiver_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/telegram_receiver_sjva.git',
        },
        {
            'name' : 'launcher_guacamole',
            'plugin_name' : 'launcher_guacamole_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/launcher_guacamole_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/launcher_guacamole_sjva.git',
            'running_type' : ['docker']
        },
        {
            'name' : 'launcher_greentunnel',
            'plugin_name' : 'launcher_greentunnel_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/launcher_greentunnel_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/launcher_greentunnel_sjva.git',
            'running_type' : ['docker']
        },
        {
            'name' : 'launcher_torrssen2',
            'plugin_name' : 'launcher_torrssen2_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/launcher_torrssen2_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/launcher_torrssen2_sjva.git',
        },
        {
            'name' : 'launcher_gateone',
            'plugin_name' : 'launcher_gateone_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/launcher_gateone_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/launcher_gateone_sjva.git',
            'platform' : ['Linux', 'Darwin']
        },
        {
            'name' : 'launcher_tautulli',
            'plugin_name' : 'launcher_tautulli_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/launcher_tautulli_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/launcher_tautulli_sjva.git'
        },
        {
            'name' : 'launcher_calibre_web',
            'plugin_name' : 'launcher_calibre_web_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/launcher_calibre_web_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/launcher_calibre_web_sjva.git'
        },
        {
            'name' : 'launcher_xteve',
            'plugin_name' : 'launcher_xteve_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/launcher_xteve_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/launcher_xteve_sjva.git'
        },
        {
            'name' : 'manamoa',
            'plugin_name' : 'manamoa_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/manamoa_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/manamoa_sjva.git'
        },
        {
            'name' : 'vnStat',
            'plugin_name' : 'vnStat_sjva',
            'json_url' : 'https://raw.githubusercontent.com/wiserain/vnStat_sjva/master/info.json',
            'git' : 'https://github.com/wiserain/vnStat_sjva.git'
        },
        {
            'name' : 'Synoindex',
            'plugin_name' : 'synoindex_sjva',
            'json_url' : 'https://raw.githubusercontent.com/soju6jan/synoindex_sjva/master/info.json',
            'git' : 'https://github.com/soju6jan/synoindex_sjva.git'
        }
    ]
    """
    custom_plugin_list = [
        
    ]
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
                    #if p['info']['version'] == p['local_info']['version']:
                    #    p['status'] = 'latest'
                    #else:
                    #    p['status'] = 'no_latest'
                    p['status'] = 'latest'
                    LogicPlugin.custom_plugin_list.append(p)
                except Exception as exception: 
                    logger.error('NO Exception:%s', exception)
                    #logger.error(traceback.format_exc())
                    logger.debug('plunin not import : %s', p['plugin_name'])
                    p['local_info'] = None
                    p['status'] = 'no'         

            """
            for p in LogicPlugin.custom_plugin_list:
                try:
                    content = requests.get(p['json_url'])
                    data = content.json()
                    logger.debug(data)
                    p['info'] = data
                    
                    mod = __import__('%s' % (p['plugin_name']), fromlist=[])
                    p['local_info'] = getattr(mod, 'plugin_info')
                    if p['info']['version'] == p['local_info']['version']:
                        p['status'] = 'latest'
                    else:
                        p['status'] = 'no_latest'
                except Exception as exception: 
                    logger.error('NO Exception:%s', exception)
                    #logger.error(traceback.format_exc())
                    logger.debug('plunin not import : %s', p['plugin_name'])
                    p['local_info'] = None
                    p['status'] = 'no'
            #logger.debug(LogicPlugin.custom_plugin_list)
            """

        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def get_plugin_list():
        try:
            if not LogicPlugin.plugin_loading:
                LogicPlugin.loading()
                LogicPlugin.plugin_loading = True
            return LogicPlugin.custom_plugin_list
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def get_plugin_info(plugin_name):
        try:
            lists = LogicPlugin.get_plugin_list()
            for l in lists:
                if l['plugin_name'] == plugin_name:
                    return l
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
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

    
    

    

    """
    @staticmethod
    def auto_update():
        try:
            logger.debug('auto_update')
            flag = False
            for p in LogicPlugin.get_plugin_list():
                if p['local_info'] is not None:
                    logger.debug('%s %s %s', p['plugin_name'],p['info']['version'], p['local_info']['version'])
                    if p['info']['version'] != p['local_info']['version']:
                        logger.debug('auto_update')
                        flag = True
                        LogicPlugin.plungin_install(p['plugin_name'], True)
            return flag
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    """
    @staticmethod
    def custom_plugin_update():
        try:
            custom_path = os.path.join(path_data, 'custom')
            tmps = os.listdir(custom_path)
            for t in tmps:
                plugin_path = os.path.join(custom_path, t)
                try:
                    if t == 'torrent_info':
                        os.remove(os.path.join(plugin_path, 'info.json'))
                except:
                    pass

                command = ['git', '-C', plugin_path, 'reset', '--hard', 'HEAD']
                ret = Util.execute_command(command)
                command = ['git', '-C', plugin_path, 'pull']
                ret = Util.execute_command(command)
                logger.debug("%s\n%s", plugin_path, ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    

    @staticmethod
    def plugin_install_by_api(plugin_git):
        logger.debug('plugin_name : %s', plugin_git)
        ret = {}
        try:
            #https://github.com/soju6jan/synoindex
            #https://github.com/soju6jan/synoindex.git
            #https://raw.githubusercontent.com/soju6jan/synoindex_sjva/master/info.json
            
            name = plugin_git.split('/')[-1]
            
            custom_path = os.path.join(path_data, 'custom')
            plugin_path = os.path.join(custom_path, name)
            logger.debug(plugin_path)
            if os.path.exists(plugin_path):
                ret['ret'] = 'already_exist'
                ret['log'] = '이미 설치되어 있습니다.'
            else:
                for tag in ['master', 'main']:
                    try:
                        info_url = plugin_git.replace('github.com', 'raw.githubusercontent.com') + '/%s/info.json' % tag
                        plugin_info = requests.get(info_url).json()
                        if plugin_info is not None:
                            break
                    except:
                        pass

                logger.debug(plugin_info)

                flag = True
                if 'platform' in plugin_info:
                    if platform.system() not in plugin_info['platform']:
                        ret['ret'] = 'not_support_os'
                        ret['log'] = '설치 가능한 OS가 아닙니다.'
                        flag = False
                elif 'running_type' in  plugin_info:
                    if app.config['config']['running_type'] not in plugin_info['running_type']:
                        ret['ret'] = 'not_support_running_type'
                        ret['log'] = '설치 가능한 실행타입이 아닙니다.'
                        flag = False
                if flag:
                    command = ['git', '-C', custom_path, 'clone', plugin_git + '.git', '--depth', '1']
                    log = Util.execute_command(command)
                    ret['ret'] = 'success'
                    ret['log'] = [u'정상적으로 설치하였습니다. 재시작시 적용됩니다.']
                    ret['log'] += log
                    ret['log'] = '<br>'.join(ret['log'])
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            ret['ret'] = 'exception'
            ret['log'] = str(exception)
        return ret