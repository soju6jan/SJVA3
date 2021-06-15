# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, threading
from framework import app, db, logger, plugin_instance_list, plugin_menu
import system

###############################################################
# 플러그인 
###############################################################
def is_include_menu(plugin_name):
    try:
        if plugin_name not in ['daum_tv', 'ffmpeg', 'fileprocess_movie', 'gdrive_scan', 'ktv', 'plex', 'rclone']:
            return True
        if system.SystemLogic.get_setting_value('use_plugin_%s' % plugin_name) == 'True':
            return True
        elif system.SystemLogic.get_setting_value('use_plugin_%s' % plugin_name) == 'False':
            return False
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())  
    return True


def plugin_init():
    try:
        if not app.config['config']['auth_status']:
            return
        import inspect
        plugin_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'plugin')
        sys.path.insert(0, plugin_path)

        try:
            from . import SystemModelSetting
            plugins = ['command', 'mod']
            for plugin in os.listdir(plugin_path):
                plugins.append(plugin)
            
            
        except:
            plugins = os.listdir(plugin_path)

        
        pass_include = []
        except_plugin_list = []

        #2019-07-17
        try:
            server_plugin_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'custom')
            sys.path.append(server_plugin_path)
            tmps = os.listdir(server_plugin_path)
            add_plugin_list = []
            for t in tmps:
                if not t.startswith('_'):
                    add_plugin_list.append(t)
            plugins = plugins + add_plugin_list
            pass_include = pass_include + add_plugin_list
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

        # 2018-09-04
        try:
            server_plugin_path = SystemModelSetting.get('plugin_dev_path')
            if server_plugin_path != '':
                if os.path.exists(server_plugin_path):
                    sys.path.append(server_plugin_path)
                    tmps = os.listdir(server_plugin_path)
                    add_plugin_list = []
                    for t in tmps:
                        if not t.startswith('_'):
                            add_plugin_list.append(t)
                            if app.config['config']['level'] < 4:
                                break
                    plugins = plugins + add_plugin_list
                    pass_include = pass_include + add_plugin_list
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


        plugins = sorted(plugins)

        
        for plugin_name in plugins:
            if plugin_name.startswith('_'):
                continue
            if plugin_name in except_plugin_list:
                logger.debug('Except plugin : %s' % plugin_menu)
                continue
            logger.debug('plugin_name:%s', plugin_name)
            try:
                mod = __import__('%s' % (plugin_name), fromlist=[])
                try:
                    mod_plugin_info = getattr(mod, 'plugin_info')      
                    if 'policy_point' in mod_plugin_info:
                        if mod_plugin_info['policy_point'] > app.config['config']['point']:
                            continue
                    if 'policy_level' in mod_plugin_info:
                        if mod_plugin_info['policy_level'] > app.config['config']['level']:
                            continue
                    if 'category' in mod_plugin_info and mod_plugin_info['category'] == 'beta':
                        if SystemModelSetting.get_bool('use_beta') == False:
                            continue
                except:
                    logger.debug('no plugin_info : %s', plugin_name)

                mod_blue_print = getattr(mod, 'blueprint')
                if mod_blue_print:
                    if plugin_name in pass_include or is_include_menu(plugin_name):
                        app.register_blueprint(mod_blue_print)
                plugin_instance_list[plugin_name] = mod
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
                logger.debug('no blueprint')
        # import가 끝나면 DB를 만든다.
        # 플러그인 로드시 DB 초기화를 할 수 있다.
        if not app.config['config']['run_by_worker']:
            try:
                db.create_all()
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
                logger.debug('db.create_all error')
        if not app.config['config']['run_by_real']:
            # 2021-06-03 
            # 모듈의 로직에 있는 celery 함수는 등록해주어야한다.
            try:
                logger.warning('module plugin_load in celery ')
                plugin_instance_list['mod'].plugin_load()
            except Exception as exception:
                logger.error('module plugin_load error')
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
            return
        
        for key, mod in plugin_instance_list.items():
            try:
                mod_plugin_load = getattr(mod, 'plugin_load')
                if mod_plugin_load and (key in pass_include or is_include_menu(key)):
                    def func(mod, key):
                        try:
                            logger.debug('### plugin_load threading start : %s', key)
                            mod.plugin_load()
                            logger.debug('### plugin_load threading end : %s', key)
                        except Exception as exception:
                            logger.error('### plugin_load exception : %s', key)
                            logger.error('Exception:%s', exception)
                            logger.error(traceback.format_exc())
                    t = threading.Thread(target=func, args=(mod, key))
                    t.setDaemon(True)
                    t.start()
                    #if key == 'mod':
                    #    t.join()
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
                logger.debug('no init_scheduler') 
            try:
                mod_menu = getattr(mod, 'menu')
                if mod_menu and (key in pass_include or is_include_menu(key)):
                    plugin_menu.append(mod_menu)
            except Exception as exception:
                logger.debug('no menu')
        logger.debug('### plugin_load threading all start.. : %s ', len(plugin_instance_list))
        # 모든 모듈을 로드한 이후에 app 등록, table 생성, start

    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())




def plugin_unload():
    for key, mod in plugin_instance_list.items():
        try:
            #if plugin_name == 'rss':
            #    continue
            mod_plugin_unload = getattr(mod, 'plugin_unload')
            if mod_plugin_unload:
                mod.plugin_unload()
        except Exception as exception:
            logger.error('module:%s', key)
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    system.plugin_unload()