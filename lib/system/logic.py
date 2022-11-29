# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import logging
from datetime import datetime
import string
import random
import json

# third-party
import requests
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify
from flask_login import login_user, logout_user, current_user, login_required

# sjva 공용
from framework.logger import get_logger, set_level
from framework import app, db, scheduler, version, path_app_root, path_data, USERS
from framework.util import Util
from framework import USERS
from framework.user import User
from framework import db, scheduler
from framework.job import Job

# 패키지
from .model import ModelSetting 
import system
# 로그
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
#########################################################

class SystemLogic(object):
    point = 0
    db_default = { 
        'db_version' : '1',
        'port' : '9999',
        'ddns' : 'http://localhost:9999',
        #'url_filebrowser' : 'http://localhost:9998',
        #'url_celery_monitoring' : 'http://localhost:9997',
        'id' : 'sjva', 
        'pw' : 'sjva',
        'system_start_time' : '',
        'repeat' : '',
        'auto_restart_hour' : '12',
        #'unique' : '',
        'theme' : 'Default',
        'log_level' : '10',
        'use_login' : 'False',
        'link_json' : '[{"type":"link","title":"위키","url":"https://sjva.me/wiki/public/start"}]', 
        'plugin_dev_path': '',
        'plugin_tving_level2' : 'False', 
        'web_title' : 'SJ Video Assistant',
        'my_ip' : '',
        'wavve_guid' : '', 

        #번역
        'trans_type' : '0',
        'trans_google_api_key' : '',
        'trans_papago_key' : '',

        #인증
        'auth_use_apikey' : 'False',
        'auth_apikey' : '',
        'hide_menu' : 'True',

        #Selenium
        'selenium_remote_url' : '',        
        'selenium_remote_default_option' : '--no-sandbox\n--disable-gpu',
        'selenium_binary_default_option' : '',

        # notify
        'notify_telegram_use' : 'False',
        'notify_telegram_token' : '',
        'notify_telegram_chat_id' : '',
        'notify_telegram_disable_notification' : 'False',
        'notify_discord_use' : 'False',
        'notify_discord_webhook' : '',
        
        'notify_advaned_use' : 'False',
        'notify_advaned_policy' : u"# 각 플러그인 설정 설명에 명시되어 있는 ID = 형식\n# DEFAULT 부터 주석(#) 제거 후 작성\n\n# DEFAULT = ",

        # telegram
        'telegram_bot_token' : '',
        'telegram_bot_auto_start' : 'False',
        'telegram_resend' : 'False', 
        'telegram_resend_chat_id' : '', 

        # 홈페이지 연동 2020-06-07
        'sjva_me_user_id' : '',
        'auth_status' : '',
        'sjva_id' : '',

        # site
        'site_daum_interval' : '0 4 */3 * *',
        'site_daum_auto_start' : 'False',
        'site_daum_cookie' : 'TIARA=gaXEIPluo-wWAFlwZN6l8gN3yzhkoo_piP.Kymhuy.6QBt4Q6.cRtxbKDaWpWajcyteRHzrlTVpJRxLjwLoMvyYLVi_7xJ1L',
        'site_daum_test' : u'나쁜 녀석들',
        'site_daum_proxy' : '',

        'site_wavve_id' : '',
        'site_wavve_pw' : '',
        'site_wavve_credential' : '',
        'site_wavve_use_proxy' : 'False',
        'site_wavve_proxy_url' : '',

        'site_tving_id' : '',
        'site_tving_pw' : '',
        'site_tving_login_type' : '0',
        'site_tving_token' : '',
        'site_tving_deviceid' : '',
        'site_tving_use_proxy' : 'False',
        'site_tving_proxy_url' : '',
        'site_tving_uuid' : '',
        
        # memo
        'memo' : '',

        # tool - decrypt
        'tool_crypt_use_user_key' : 'False',
        'tool_crypt_user_key' : '',
        'tool_crypt_encrypt_word' : '',
        'tool_crypt_decrypt_word' : '',
        
        'use_beta' : 'False',
    }



    db_default2 = {'use_category_vod':'True', 'use_category_file_process':'True', 'use_category_plex':'True', 'use_category_tool':'True'}

    db_default3 = {'use_plugin_ffmpeg':'False', 'use_plugin_ktv':'False', 'use_plugin_fileprocess_movie':'False',  'use_plugin_plex':'False', 'use_plugin_gdrive_scan':'False', 'use_plugin_rclone':'False', 'use_plugin_daum_tv':'False'}

    recent_version = None


    @staticmethod
    def plugin_load():
        try:
            SystemLogic.db_init()
            SystemLogic.init()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def db_init():
        try:
            
            logger.debug('setting count : %s', db.session.query(ModelSetting).filter_by().count())
            is_first = False
            for key, value in SystemLogic.db_default.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    if key == 'port':
                        is_first = True
                    if key == 'sjva_id' or key == 'auth_apikey':
                        value = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
                    db.session.add(ModelSetting(key, value))
                    db.session.commit()
            logger.warning("db_init1")
            # 기존...사람들을 위해 토큰이 있는 사용자면 추가할때 True로 해준다
            for key, value in SystemLogic.db_default2.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    tmp = value
                    if is_first == False:
                        tmp = 'True'
                    db.session.add(ModelSetting(key, tmp))
                    db.session.commit()
            #db.session.commit()
            logger.warning("db_init2")

            for key, value in SystemLogic.db_default3.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    tmp = value
                    if is_first == False:
                        tmp = 'True'
                    db.session.add(ModelSetting(key, tmp))
                    db.session.commit()
            logger.warning("db_init3")
            #for key, value in SystemLogic.db_default_etc.items():
            #    if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
            #        db.session.add(ModelSetting(key, value))
            #db.session.commit()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @staticmethod
    def init():
        try:
            if app.config['config']['repeat'] == 0 or SystemLogic.get_setting_value('system_start_time') == '':
                item = db.session.query(ModelSetting).filter_by(key='system_start_time').with_for_update().first()
                item.value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                db.session.commit()
                
            item = db.session.query(ModelSetting).filter_by(key='repeat').with_for_update().first()
            item.value = str(app.config['config']['repeat'])
            db.session.commit()
            username = db.session.query(ModelSetting).filter_by(key='id').first().value
            passwd = db.session.query(ModelSetting).filter_by(key='pw').first().value
            USERS[username] = User(username, passwd_hash=passwd)
            
            SystemLogic.set_restart_scheduler()
            #SystemLogic.set_statistics_scheduler()
            SystemLogic.set_scheduler_check_scheduler()
            #SystemLogic.get_recent_version()
           
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_recent_version():
        try:
            import requests
            url = f"{app.config['DEFINE']['MAIN_SERVER_URL']}/version"
            if ModelSetting.get('ddns') == app.config['DEFINE']['MAIN_SERVER_URL']:
                url = 'https://dev.soju6jan.com/version'
            SystemLogic.recent_version = requests.get(url).text
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        return False
    
    @staticmethod
    def restart():
        import system
        system.restart()

    @staticmethod
    def get_info():
        info = {}
        import platform
        info['platform'] = platform.platform()
        info['processor'] = platform.processor()

        import sys
        info['python_version'] = sys.version
        info['version'] = version
        info['recent_version'] = SystemLogic.recent_version
        info['path_app_root'] = path_app_root
        info['running_type'] = u'%s.  비동기 작업 : %s' % (app.config['config']['running_type'], u"사용" if app.config['config']['use_celery'] else "미사용")
        import system
        
        info['auth'] = app.config['config']['auth_desc']
        info['cpu_percent'] = 'not supported'
        info['memory'] = 'not supported'
        info['disk'] = 'not supported'
        if app.config['config']['running_type'] != 'termux':
            try:
                import psutil
                from framework.util import Util
                info['cpu_percent'] = '%s %%' % psutil.cpu_percent() 
                tmp = psutil.virtual_memory()
                #info['memory'] = [Util.sizeof_fmt(tmp[0], suffix='B'), Util.sizeof_fmt(tmp[3]), Util.sizeof_fmt(tmp[1]), tmp[2]]
                info['memory'] = u'전체 : %s   사용량 : %s   남은량 : %s  (%s%%)' % (Util.sizeof_fmt(tmp[0], suffix='B'), Util.sizeof_fmt(tmp[3], suffix='B'), Util.sizeof_fmt(tmp[1], suffix='B'), tmp[2])
            except:
                pass

            try:
                import platform
                if platform.system() == 'Windows':
                    s = os.path.splitdrive(path_app_root)
                    root = s[0]
                else:
                    root = '/'
                tmp = psutil.disk_usage(root)
                info['disk'] = u'전체 : %s   사용량 : %s   남은량 : %s  (%s%%) - 드라이브 (%s)' % (Util.sizeof_fmt(tmp[0], suffix='B'), Util.sizeof_fmt(tmp[1], suffix='B'), Util.sizeof_fmt(tmp[2], suffix='B'), tmp[3], root)
            except Exception as exception: 
                pass
        try:
            tmp = SystemLogic.get_setting_value('system_start_time')
            #logger.debug('SYSTEM_START_TIME:%s', tmp)
            tmp_datetime = datetime.strptime(tmp, '%Y-%m-%d %H:%M:%S')
            timedelta = datetime.now() - tmp_datetime
            info['time'] = u'시작 : %s   경과 : %s   재시작 : %s' % (tmp, str(timedelta).split('.')[0], app.config['config']['repeat'])
        except Exception as exception: 
            info['time'] = str(exception)
        return info


    @staticmethod
    def setting_save_system(req):
        try:
            for key, value in req.form.items():
                logger.debug('Key:%s Value:%s', key, value)
                entity = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
                entity.value = value
                #if key == 'theme':
                #    SystemLogic.change_theme(value)
            db.session.commit()
            lists = ModelSetting.query.all()
            SystemLogic.setting_list = Util.db_list_to_dict(lists)
            USERS[db.session.query(ModelSetting).filter_by(key='id').first().value] = User(db.session.query(ModelSetting).filter_by(key='id').first().value, passwd_hash=db.session.query(ModelSetting).filter_by(key='pw').first().value)
            SystemLogic.set_restart_scheduler()
            set_level(int(db.session.query(ModelSetting).filter_by(key='log_level').first().value))
            
            return True                  
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def setting_save_after():
        try:
            USERS[ModelSetting.get('id')] = User(ModelSetting.get('id'), passwd_hash=ModelSetting.get('pw'))
            SystemLogic.set_restart_scheduler()
            set_level(int(db.session.query(ModelSetting).filter_by(key='log_level').first().value))
            from .logic_site import SystemLogicSite
            SystemLogicSite.get_daum_cookies(force=True)
            SystemLogicSite.create_tving_instance()
            return True                  
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def change_theme(theme):
        try:
            source = os.path.join(path_app_root, 'static', 'css', 'theme', '%s_bootstrap.min.css' % theme)
            target = os.path.join(path_app_root, 'static', 'css', 'bootstrap.min.css')
            os.remove(target)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def get_setting_value(key):
        try:
            #logger.debug('get_setting_value:%s', key)
            entity = db.session.query(ModelSetting).filter_by(key=key).first()
            if entity is None:
                return None
            else:
                return entity.value
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            logger.error('error key : %s', key)
            return False
    
    @staticmethod
    def set_restart_scheduler():
        name = '%s_restart' % (package_name)
        if scheduler.is_include(name):
            scheduler.remove_job(name)
        interval = ModelSetting.get('auto_restart_hour')
        if interval != '0':
            if len(interval.split(' ')) == 1:
                interval = '%s' % (int(interval) * 60)
            job_instance = Job(package_name, name, interval, SystemLogic.restart, u"자동 재시작", True)
            scheduler.add_job_instance(job_instance, run=False)
    """    
    @staticmethod
    def set_statistics_scheduler():
        try:
            name = '%s_statistics' % (package_name)
            if scheduler.is_include(name):
                scheduler.remove_job(name)

            job_instance = Job(package_name, name, 59, SystemLogic.statistics_scheduler_function, u"Update Check", True)
            scheduler.add_job_instance(job_instance, run=True)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False
    """

    @staticmethod
    def set_scheduler_check_scheduler():
        try:
            name = 'scheduler_check'
            if scheduler.is_include(name):
                scheduler.remove_job(name)

            job_instance = Job(package_name, name, 2, scheduler.first_run_check_thread_function, u"Scheduler Check", True)
            scheduler.add_job_instance(job_instance, run=False)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False
    
    

    @staticmethod
    def command_run(command_text):
        try:
            ret = {}
            tmp = command_text.strip().split(' ')
            if not tmp:
                ret['ret'] = 'success'
                ret['log'] = 'Empty..'
                return ret
            if tmp[0] == 'set':
                if len(tmp) == 3:
                    if tmp[1] == 'token':
                        tmp[1] = 'unique'
                    entity = db.session.query(ModelSetting).filter_by(key=tmp[1]).with_for_update().first()
                    if entity is None:
                        ret['ret'] = 'fail'
                        ret['log'] = '%s not exist' % tmp[1]
                        return ret
                    entity.value = tmp[2] if tmp[2] != 'EMPTY' else ""
                    db.session.commit()
                    ret['ret'] = 'success'
                    ret['log'] = '%s - %s' % (tmp[1], tmp[2])
                    return ret
            
            if tmp[0] == 'set2':
                if tmp[1] == 'klive':
                    from klive import ModelSetting as KLiveModelSetting
                    if KLiveModelSetting.get(tmp[2]) is not None:
                        KLiveModelSetting.set(tmp[2], tmp[3])
                        ret['ret'] = 'success'
                        ret['log'] = f'KLive 설정 값 변경 : {tmp[2]} - {tmp[3]}'
                        return ret
                   
            
            ret['ret'] = 'fail'
            ret['log'] = 'wrong command'
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            ret['ret'] = 'fail'
            ret['log'] = str(exception)
            return ret

    @staticmethod
    def link_save(link_data_str):
        try:
            data = json.loads(link_data_str)
            entity = db.session.query(ModelSetting).filter_by(key='link_json').with_for_update().first()
            entity.value = link_data_str
            db.session.commit()
            SystemLogic.apply_menu_link()
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False


    @staticmethod
    def apply_menu_link():
        try:
            link_data_str = SystemLogic.get_setting_value('link_json')  
            data = json.loads(link_data_str)
            from framework.menu import get_menu_map
            menu_map = get_menu_map()
            for link_category in menu_map:
                if link_category['type'] == 'link':
                    break
            link_category['list'] = []
            for item in data:
                entity = {}
                entity['type'] = item['type']
                if item['type'] == 'link':
                    entity['name'] = item['title']
                    entity['link'] = item['url']
                link_category['list'].append(entity)
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False
