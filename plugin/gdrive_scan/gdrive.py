# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import time
from datetime import datetime
import urllib
import json
import threading
import time
import platform

# third-party
import requests
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify, session, send_from_directory 
from flask_socketio import SocketIO, emit, send

from sqlitedict import SqliteDict


# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, path_data, socketio, path_app_root
from framework.util import Util, AlchemyEncoder
from system.logic import SystemLogic
# 패키지
#import plex
from .model import ModelSetting, ModelGDriveScanJob,ModelGDriveScanFile



# third-party
try:
    import oauth2client
except ImportError:
    try:
        os.system("{} install oauth2client".format(app.config['config']['pip']))
        import oauth2client
    except:
        pass
try:
    from apiclient.discovery import build
except ImportError:
    try:
        os.system("{} install google-api-python-client".format(app.config['config']['pip']))
        from apiclient.discovery import build
    except:
        pass

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client import tools
from oauth2client.client import flow_from_clientsecrets, OAuth2WebServerFlow
from httplib2 import Http
#from oauth2client import file, client, tools
from oauth2client import client, tools



# 로그
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
#########################################################


#CLIENT_ID = '199519295861-6e7i6g6b2alnd01sh069qu07bids2m6q.apps.googleusercontent.com'
#CLIENT_SECRET = '1ft_8smtun3yVPaaNigi-13Z'



class Auth(object):
    current_flow = None
    #current_name = None
    #auth_uri = None

    """
    #같은 머신 혹은 고정된 callback 이 있을때만 가능
    @staticmethod
    def make_token(redirect_uri, name, return_url=False):
        try:
            logger.debug('auth')
            GDrive.current_name = name
            json_file = os.path.join(path_app_root, 'static', 'file', 'client_secret.json')
            GDrive.current_flow  = oauth2client.client.flow_from_clientsecrets(
                json_file,  # downloaded file
                SCOPE,  # scope
                redirect_uri=redirect_uri)
            GDrive.auth_uri = GDrive.current_flow.step1_get_authorize_url()
            if return_url:
                return GDrive.auth_uri
            else:
                return webbrowser.open(GDrive.auth_uri)
            return True
        except Exception as exception:
            logger.debug(exception)
            logger.debug(traceback.format_exc())
            return False
    """
    
    @staticmethod
    def save_token(code, name):
        try:
            credentials = GDrive.current_flow.step2_exchange(code)
            filename = os.path.join(path_data, 'db', 'gdrive', '%s.json' % name)
            storage = Storage(filename)
            storage.put(credentials)
            logger.debug('Save token:%s %s',filename, code)
            return True
        except Exception as exception:
            logger.debug(exception)
            logger.debug(traceback.format_exc())
            return False

    @staticmethod
    def make_token_cli(account_type):
        try:
            logger.debug(account_type)
            tmp = 'client_secret.json'
            json_file = None
            if account_type == "0": #기본
                pass
            if account_type == "1":
                tmp = 'client_secret_sjva_me.json'
            if account_type == "2":
                tmp = 'client_secret_knou_ac_kr.json'
            elif account_type == '99': #사용자
                json_file = os.path.join(path_app_root, 'data', 'db', tmp)
                if not os.path.exists(json_file):
                    return '99_not_exist'
            
            if json_file is None:
                json_file = os.path.join(path_app_root, 'static', 'file', tmp)
            GDrive.current_flow  = oauth2client.client.flow_from_clientsecrets(
                json_file,  # downloaded file
                'https://www.googleapis.com/auth/drive',  # scope
                redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            return GDrive.current_flow.step1_get_authorize_url()
        except Exception as exception:
            logger.debug(exception)
            logger.debug(traceback.format_exc())
            return False
    





class GDrive(object):
    
    """
    @classmethod
    def make_token_cli(cls, name):
        def thread_function():
            try:
                logger.debug('auth')
                flow = OAuth2WebServerFlow(client_id=CLIENT_ID,
                                        client_secret=CLIENT_SECRET,
                                        scope=SCOPE,
                                        redirect_uri='',
                                        noauth_local_webserver='')
                storage = Storage(os.path.join(os.path.dirname(__file__), '%s.json' % name))
                logger.debug('auth1')
                tools.run_flow(flow, storage)
                logger.debug('auth2')
                return True
            except Exception as exception:
                logger.debug(exception)
                logger.debug(traceback.format_exc())
                return False
        threading.Timer(1.0, thread_function).start()
        return True
    """

    def __init__(self, match_rule):
        #self.match_rule = [u'내 드라이브', u'M:'] soju6janm:내 드라이브,M:
        self.match_rule = match_rule.split(',')
        self.gdrive_name = self.match_rule[0].split(':')[0]
        self.match_rule = [self.match_rule[0].split(':')[1], self.match_rule[1]]
        
        #self.db = os.path.join(os.path.dirname(__file__), '%s.db' % self.gdrive_name)
        self.db = os.path.join(os.path.join(path_data, 'db', 'gdrive', '%s.db' % self.gdrive_name))
        self.cache = SqliteDict(self.db, tablename='cache', encode=json.dumps, decode=json.loads, autocommit=True)
        self.change_check_interval = 60
        self.api_call_inverval = 1
        self.flag_thread_run = True
        self.thread = None
        self.gdrive_service = None
        #self.match_rule = ['[영화']
        #GdrivePath:내 드라이브/Movie/해외/Blueray/2016/녹투라마 (2016)/nocturama.2016.limited.1080p.bluray.x264-usury.mkv
        

    # 2019-03-10
    # 예) 영화 내부파일을 정리하고 라이브러리 폴더를 옮길 때, 이럴 경우에는 폴더의 이벤트만 오지
    # 파일의 이벤트는 처리하지 않고 있다.
    # 폴더도 처리
    def start_change_watch(self):
        def get_start_page_token(creds):
            try:
                self.gdrive_service = build('drive', 'v3', http=creds.authorize(Http()))
                results = self.gdrive_service.changes().getStartPageToken().execute()
                page_token = results['startPageToken']
                logger.debug('startPageToken:%s', page_token)
                return page_token
            except Exception as exception:
                logger.debug('Exception:%s', exception)
                logger.debug(traceback.format_exc())    

        def thread_function():
            
            store = Storage(os.path.join(path_data, 'db', 'gdrive', '%s.json' % self.gdrive_name))
            creds = store.get()
            if not creds or creds.invalid:
                #flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
                #creds = tools.run_flow(flow, store)
                return -1

            page_token = get_start_page_token(creds)

            while self.flag_thread_run:
                try:
                    #time.sleep(self.change_check_interval)
                    for _ in range(self.change_check_interval):
                        #logger.debug('%s %s', self.gdrive_name, _)
                        if self.flag_thread_run == False:
                            return
                        time.sleep(1)
                    results = self.gdrive_service.changes().list(
                        pageToken=page_token,
                        pageSize=1000,
                        fields= "changes( \
                                    file( \
                                        id, md5Checksum,mimeType,modifiedTime,name,parents,teamDriveId,trashed \
                                    ),  \
                                    fileId,removed \
                                ), \
                                newStartPageToken"
                        ).execute()
            
                    page_token = results.get('newStartPageToken')
                    logger.debug('PAGE_TOKEN:%s' % page_token)

                    items = results.get('changes', [])
                    for _ in items:
                        logger.debug('1.CHANGE : %s', _)
                        
                        # 2019-03-10 변경시에는 2개를 보내야 한다.
                        is_add = True
                        is_file = True
                        if _['removed'] == True:
                            is_add = False
                            fileid = _['fileId']
                            if fileid in self.cache:
                                file_meta = {
                                    'name' : self.cache[fileid]['name'],
                                    'parents' : self.cache[fileid]['parents'],
                                    #'mimeType' : self.cache[fileid]['mimeType'],
                                }
                                file_meta['mimeType'] = self.cache[fileid]['mimeType'] if 'mimeType' in self.cache[fileid] else 'application/vnd.google-apps.folder'
                            else:
                                logger.debug('remove. not cache')
                                continue
                        else:
                            if 'file' in _:
                                if _['file']['mimeType'] == 'application/vnd.google-apps.folder':
                                    logger.debug('FOLDER')
                                elif _['file']['mimeType'].startswith('video'):
                                    logger.debug('FILE')
                                else:
                                    logger.debug('not folder, not video')
                                    continue
                            fileid = _['file']['id']
                            #삭제시에는 inqueue.. 바로 반영이 될까? RemoveWaitFile만들자
                            #일반적일때는 addwait?                    
                            #logger.debug(u'{0} ({1})'.format(_['file']['name'], _['file']['id']).encode('cp949'))

                            file_meta = self.gdrive_service.files().get(
                                fileId=fileid, fields="id,mimeType, modifiedTime,name,parents,trashed"
                            ).execute()

                        if file_meta['mimeType'] == 'application/vnd.google-apps.folder':
                            is_file = False
                        
                        logger.debug('IS_ADD : %s IS_FILE :%s', is_add, is_file)
                        job_list = []

                        if is_add and is_file:
                            job_list = [[file_meta, 'ADD',is_file]]
                        elif is_add and not is_file:
                            job_list = [[file_meta, 'ADD',is_file]]
                            #폴더 변경
                            if fileid in self.cache:
                                remove_file_meta = {
                                    'name' : self.cache[fileid]['name'],
                                    'parents' : self.cache[fileid]['parents'],
                                    #'mimeType' : self.cache[fileid]['mimeType'],
                                }
                                remove_file_meta['mimeType'] = self.cache[fileid]['mimeType'] if 'mimeType' in self.cache else 'application/vnd.google-apps.folder'
                                ttmp = (remove_file_meta['mimeType'] != 'application/vnd.google-apps.folder')
                                job_list.insert(0, [remove_file_meta, 'REMOVE', ttmp])
                        elif not is_add and is_file:
                            job_list = [[file_meta, 'REMOVE',is_file]]
                        elif not is_add and not is_file:
                            job_list = [[file_meta, 'REMOVE',is_file]]                                              

                        for job in job_list:      
                            file_meta = job[0]
                            type_add_remove = job[1]
                            is_file = job[2]
                            logger.debug('2.FILEMETA:%s %s %s' % (file_meta, type_add_remove, is_file))
                            file_paths = self.get_parent(file_meta)
                            if file_paths is None:
                                logger.debug('get_parent is None')
                                continue

                            gdrivepath = '/'.join(file_paths)
                            logger.debug('3.GdrivePath:%s' % gdrivepath)
                            mount_abspath = self.get_mount_abspath(file_paths)
                            if mount_abspath is None:
                                logger.debug('NOT MOUNT INFO')
                                continue
                            logger.debug('4.MountPath:%s' % mount_abspath)
                            
                            #s_id = PLEX_DB.get_section_id(mount_abspath)
                            s_id = self.get_section_id(mount_abspath)
                            if s_id == -1:
                                logger.debug('5-2.IGNORE. %s file section_id is -1.', mount_abspath)
                            else:
                                # 삭제나 변경을 위해서다. 
                                if is_add:
                                    self.cache[fileid] = {
                                        'name': file_meta['name'], 
                                        'parents': file_meta['parents'],
                                        'mimeType' : file_meta['mimeType']
                                    }
                                else:
                                    self.cache[fileid] = None
                                # 2019-05-16 PLEX와 SJVA가 다르다
                                # 파일
                                """
                                if is_add and not is_file:
                                    try:
                                        if not os.listdir(mount_abspath):
                                            logger.debug('5. IS EMPTY!!')
                                            continue
                                    except:
                                        logger.debug('os.listdir exception!')
                                        continue
                                """
                                #if PLEX_DB.is_exist_in_library(mount_abspath) == False:
                                exist_in_library = self.is_exist_in_library(mount_abspath)
                                if (not exist_in_library and type_add_remove == 'ADD') or ( exist_in_library and type_add_remove == 'REMOVE'):
                                    #pms_global.send_command(s_id, mount_abspath, type_add_remove, 'GDRIVE')
                                    self.send_command(s_id, mount_abspath, type_add_remove, is_file)
                                    logger.debug('5-1.Send Command %s %s %s %s', s_id, mount_abspath, type_add_remove,is_file)
                                else:
                                    logger.debug('5-3.IGNORE. EXIST:%s TYPE:%s', exist_in_library, type_add_remove)
                            # 2019-09-02
                            # 비디오스테이션을 위해
                            try:
                                from .logic import Logic
                                Logic.send_to_listener(type_add_remove, is_file, mount_abspath)
                            except Exception as exception:
                                logger.debug('Exception:%s', exception)
                                logger.debug(traceback.format_exc()) 

                            logger.debug('6.File process end.. WAIT :%s', self.api_call_inverval)
                            for _ in range(self.api_call_inverval):
                                #logger.debug('%s %s', self.gdrive_name, _)
                                if self.flag_thread_run == False:
                                    return
                                time.sleep(1)
                            logger.debug('7.AWAKE Continue')
                except TypeError as exception:
                    page_token = get_start_page_token(creds)
                    logger.debug('TYPE ERROR !!!!!!!!!!!!!!!!!!!!')    
                    logger.debug('Exception:%s', exception)
                    logger.debug(traceback.format_exc()) 
                except Exception as exception:
                    logger.debug('Exception:%s', exception)
                    logger.debug(traceback.format_exc())    

                    

        self.thread = threading.Thread(target=thread_function, args=())
        self.thread.daemon = True
        self.thread.start()
        #logger.debug('self.therad %s', self.thread)
        return True

    def get_mount_abspath(self, gdrive_path):
        try:
            # 2019-05-18
            logger.debug(gdrive_path)
            if gdrive_path[0].startswith('My Drive'):
                gdrive_path[0] = gdrive_path[0].replace('My Drive', '내 드라이브')
            replace_gdrive_path = self.match_rule[0].split('/')
            #if platform.system() == 'Windows':
            #Windows
            if self.match_rule[1][0] != '/':
            #if os.sep == '\\':
                (drive, p) = os.path.splitdrive(self.match_rule[1])
                replace_mount_path = os.path.split(p)
            else:
                drive = None
                replace_mount_path = os.path.split(self.match_rule[1])

            flag_find = True
            for idx, val  in enumerate(replace_gdrive_path):
                if gdrive_path[idx] != val:
                    flag_find = False
            
            if flag_find:
                ret = u''
                for _ in replace_mount_path:
                    ret = os.path.join(ret, _)
                for _ in gdrive_path[idx+1:]:
                    ret = os.path.join(ret, _)
                if drive is not None:
                    ret = os.path.join(drive, os.sep, ret)
            else:
                ret = None
                logger.debug('WRONG SETTING PATH!!!!!!!!!!!!!')    
                return ret
            logger.debug('get_mount_abspath1: %s', ret)
            if self.match_rule[1][0] != '/':
                #윈도우
                ret = ret.replace('/', '\\')
                #너무 귀찮다.....
                # \M:\Movie\한국\VOD\악어 (1996)\악어.avi
                if ret[0] == '\\':
                    ret = ret[1:]
            else:
                ret = ret.replace('\\', '/')
            logger.debug('get_mount_abspath2: %s', ret)
            return ret
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())

    def get_parent(self, file_meta):
        try:
            file_paths = [file_meta['name']]
            parents = file_meta['parents']
            while parents is not None:
                parent_id = parents[0]
                logger.debug('parent_id:%s', parent_id)
                if parent_id not in self.cache:
                    parent_result = self.gdrive_service.files().get(
                        fileId=parent_id, fields="id,mimeType, modifiedTime, name, parents, trashed"
                    ).execute()
                    logger.debug('parent_result:%s', parent_result)
                    self.cache[parent_id] = {
                        'name': parent_result['name'], 
                        'parents': parent_result['parents'] if 'parents' in parent_result else None,
                        'mimeType' : parent_result['mimeType']
                    }
                logger.debug( 'parent_id in cache : %s', (parent_id in self.cache) )
                file_paths.insert(0, self.cache[parent_id]['name'])
                logger.debug('    file_paths:%s', file_paths)
                parents = self.cache[parent_id]['parents']
                logger.debug('    parents:%s', parents)

                if len(file_paths) > 30:
                    return None
            return file_paths
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())

    def stop(self):
        logger.debug('Gdrive stop function start..: %s %s ', self.gdrive_name, self.thread.isAlive())
        self.flag_thread_run = False
        self.thread.join()
        logger.debug('Gdrive stop function end..: %s %s', self.gdrive_name, self.thread.isAlive())
    
    def get_section_id(self, path):
        try:
            import plex
            section_id = plex.Logic.get_section_id_by_file(path)
            logger.debug('SectionID:%s %s', section_id, type(section_id))
            return section_id
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return -1

    def is_exist_in_library(self, path):
        try:
            import plex
            ret = plex.Logic.is_exist_in_library(path)
            logger.debug('is_exist_in_library %s %s', path, ret)
            return ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return True

    def send_command(self, s_id, mount_abspath, type_add_remove, is_file):
        callback_id = -1
        try:
            callback_id = ModelGDriveScanFile.add(self.gdrive_name, mount_abspath, int(s_id) if type(s_id) == type('') else s_id, is_file, (type_add_remove == 'ADD'))
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        try:
            import plex
            plex.Logic.send_scan_command2('gdrive_scan', s_id, mount_abspath, callback_id, type_add_remove, "GDRIVE")
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

