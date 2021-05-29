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
        #return True
        #####################################################
        # 2019-08-30 : 메뉴 
        # 로딩 False 인 것은 아예 로딩하지 않는다. 그러나 타 모듈에서 로딩하는 것은 어쩔수 없다
        # 그런 것은 메뉴 구성할때 한번 더 거른다.
        #####################################################
        #menu_json = {'plugin_use_pooq':'True'}
        #if 'plugin_use_%s' % plugin_name in menu_json and menu_json['plugin_use_%s' % plugin_name] == 'True':
        #    return True
        #return False
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

        # 2020-10-23
        #plugins = os.listdir(plugin_path)
        try:
            from . import SystemModelSetting
            plugins = ['command', 'mod']
            for plugin in os.listdir(plugin_path):
                plugins.append(plugin)
        except:
            plugins = os.listdir(plugin_path)

        
        pass_include = []
        #except_plugin_list = ['rss2']
        except_plugin_list = []

        #logger.debug('CONFIG_SERVER : %s', app.config['config'])
        #2019-05-24
        
        if app.config['config']['is_server'] or app.config['config']['is_debug']:
            server_plugin_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'server')
            if os.path.exists(server_plugin_path):
                sys.path.insert(0, server_plugin_path)
                plugins = plugins + os.listdir(server_plugin_path)
                pass_include = pass_include + os.listdir(server_plugin_path)

        #2019-07-17
        try:
            server_plugin_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'custom')
            sys.path.append(server_plugin_path)
            tmps = os.listdir(server_plugin_path)
            add_plugin_list = []
            for t in tmps:
                if not t.startswith('_'):
                    add_plugin_list.append(t)
            #logger.debug(add_plugin_list)
            #plugins = plugins + os.listdir(server_plugin_path)
            #pass_include = pass_include + os.listdir(server_plugin_path)
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
                    #logger.debug(add_plugin_list)
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