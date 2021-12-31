# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, threading, platform
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
        from . import SystemModelSetting
        """
        try:
            from . import SystemModelSetting
            plugins = ['command', 'mod']
            for plugin in os.listdir(plugin_path):
                plugins.append(plugin)
        except:
            plugins = os.listdir(plugin_path)
        """
        plugins = os.listdir(plugin_path)
        
        pass_include = []
        except_plugin_list = []

        #2019-07-17
        try:
            plugin_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'custom')
            sys.path.insert(1, plugin_path)
            tmps = os.listdir(plugin_path)
            add_plugin_list = []
            for t in tmps:
                if not t.startswith('_') and os.path.isdir(os.path.join(plugin_path, t)):
                    add_plugin_list.append(t)
            plugins = plugins + add_plugin_list
            pass_include = pass_include + add_plugin_list
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

        # 2018-09-04
        try:
            plugin_path = SystemModelSetting.get('plugin_dev_path')
            if plugin_path != '':
                if os.path.exists(plugin_path):
                    sys.path.insert(0, plugin_path)
                    tmps = os.listdir(plugin_path)
                    add_plugin_list = []
                    for t in tmps:
                        if not t.startswith('_')  and os.path.isdir(os.path.join(plugin_path, t)):
                            add_plugin_list.append(t)
                            if app.config['config']['level'] < 4:
                                break
                    plugins = plugins + add_plugin_list
                    pass_include = pass_include + add_plugin_list
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


        plugins = sorted(plugins)

        logger.debug(plugins)
        for plugin_name in plugins:
            #logger.debug(len(system.LogicPlugin.current_loading_plugin_list))
            if plugin_name.startswith('_'):
                continue
            if plugin_name == 'terminal' and platform.system() == 'Windows':
                continue
            if plugin_name in except_plugin_list:
                logger.debug('Except plugin : %s' % plugin_menu)
                continue
            logger.debug(f'[+] PLUGIN LOADING Start.. [{plugin_name}]') 
            try:
                mod = __import__('%s' % (plugin_name), fromlist=[])
                mod_plugin_info = None
                # 2021-12-31
                if plugin_name not in system.LogicPlugin.current_loading_plugin_list:
                    system.LogicPlugin.current_loading_plugin_list[plugin_name] = {'status':'loading'}
                
                try:
                    mod_plugin_info = getattr(mod, 'plugin_info')
                    if 'category'  not in mod_plugin_info and 'category_name' in mod_plugin_info:
                        mod_plugin_info['category'] = mod_plugin_info['category_name']
                    if 'policy_point' in mod_plugin_info:
                        if mod_plugin_info['policy_point'] > app.config['config']['point']:
                            system.LogicPlugin.current_loading_plugin_list[plugin_name]['status'] = 'violation_policy_point'
                            continue
                    if 'policy_level' in mod_plugin_info:
                        if mod_plugin_info['policy_level'] > app.config['config']['level']:
                            system.LogicPlugin.current_loading_plugin_list[plugin_name]['status'] = 'violation_policy_level'
                            continue
                    if 'category' in mod_plugin_info and mod_plugin_info['category'] == 'beta':
                        if SystemModelSetting.get_bool('use_beta') == False:
                            system.LogicPlugin.current_loading_plugin_list[plugin_name]['status'] = 'violation_beta'
                            continue
                except Exception as exception:
                    #logger.error('Exception:%s', exception)
                    #logger.error(traceback.format_exc())
                    logger.debug(f'[!] PLUGIN_INFO not exist : [{plugin_name}]') 

                try:
                    mod_blue_print = getattr(mod, 'blueprint')
                    if mod_blue_print:
                        if plugin_name in pass_include or is_include_menu(plugin_name):
                            app.register_blueprint(mod_blue_print)
                except Exception as exception:
                    #logger.error('Exception:%s', exception)
                    #logger.error(traceback.format_exc())
                    logger.debug(f'[!] BLUEPRINT not exist : [{plugin_name}]') 
                plugin_instance_list[plugin_name] = mod
                system.LogicPlugin.current_loading_plugin_list[plugin_name]['status'] = 'success'
                system.LogicPlugin.current_loading_plugin_list[plugin_name]['info'] = mod_plugin_info
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
                logger.debug('no blueprint')
        
        #from tool_base import d
        #logger.error(d(system.LogicPlugin.current_loading_plugin_list))
        # 2021-07-01 모듈에 있는 DB 테이블 생성이 안되는 문제
        # 기존 구조 : db.create_all() => 모듈 plugin_load => celery task 등록 후 리턴
        # 변경 구조 : 모듈 plugin_load => db.create_all() => celery인 경우 리턴

        # plugin_load 를 해야 하위 로직에 있는 DB가 로딩된다.
        # plugin_load 에 db는 사용하는 코드가 있으면 안된다. (테이블도 없을 때 에러발생)
        try:
            #logger.warning('module plugin_load in celery ')
            plugin_instance_list['mod'].plugin_load()
        except Exception as exception:
            logger.debug(f'mod plugin_load error!!') 
            #logger.error('Exception:%s', exception)
            #logger.error(traceback.format_exc())

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
            #try:
            #    logger.warning('module plugin_load in celery ')
            #    plugin_instance_list['mod'].plugin_load()
            #except Exception as exception:
            #    logger.error('module plugin_load error')
            #    logger.error('Exception:%s', exception)
            #    logger.error(traceback.format_exc())
            # 2021-07-01
            # db때문에 위에서 로딩함.
            return
        
        for key, mod in plugin_instance_list.items():
            try:
                mod_plugin_load = getattr(mod, 'plugin_load')
                if mod_plugin_load and (key in pass_include or is_include_menu(key)):
                    def func(mod, key):
                        try:
                            logger.debug(f'[!] plugin_load threading start : [{key}]') 
                            mod.plugin_load()
                            logger.debug(f'[!] plugin_load threading end : [{key}]') 
                        except Exception as exception:
                            logger.error('### plugin_load exception : %s', key)
                            logger.error('Exception:%s', exception)
                            logger.error(traceback.format_exc())
                    # mod는 위에서 로딩
                    if key != 'mod':
                        t = threading.Thread(target=func, args=(mod, key))
                        t.setDaemon(True)
                        t.start()
                    #if key == 'mod':
                    #    t.join()
            except Exception as exception:
                logger.debug(f'[!] PLUGIN_LOAD function not exist : [{key}]') 
                #logger.error('Exception:%s', exception)
                #logger.error(traceback.format_exc())
                #logger.debug('no init_scheduler') 
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