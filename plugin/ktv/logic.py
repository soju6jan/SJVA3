# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import time
from datetime import datetime, timedelta
import logging
import urllib
import shutil
import re

# third-party
import requests
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify
from sqlalchemy import desc

# sjva 공용
from framework import app, db, scheduler, celery
from framework.job import Job
from framework.util import Util
from framework.event import MyEvent
from tool_base import ToolBaseNotify

# 패키지
from .model import ModelSetting, ModelKtvFile, ModelKtvLibrary
from .entity_show import EntityLibraryPathRoot, EntityLibraryPath, EntityShow

#########################################################

package_name = __name__.split('.')[0]
logger = logging.getLogger(package_name)




class Logic(object): 
    db_default = { 
        'auto_start' : 'False',
        'interval' : '2',
        'not_ktv_move_folder_name' : 'no_ktv',
        'manual_folder_name' : 'manual',
        'no_daum_folder_name' : u'기타',
        'web_page_size' : 20,
        'download_path' : '',
        'telegram' : '',
        'except_partial' : '.part',
        'except_genre_remove_epi_number' : u'애니메이션',
    }
    #from file_setting import FileManagerSetting
    #_DOWNLOAD_PATH = FileManagerSetting.DOWNLOAD_PATH
    #_LIBRARY_ROOT_LIST = FileManagerSetting.LIBRARY_ROOT_LIST
    _DOWNLOAD_PATH = None
    _LIBRARY_ROOT_LIST = None

    @staticmethod
    def db_init():
        try:
            for key, value in Logic.db_default.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    db.session.add(ModelSetting(key, value))
            db.session.commit()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def plugin_load():
        try:
            Logic.db_init()
            logger.debug('plugin_load:%s', scheduler.sched)
            if ModelSetting.query.filter_by(key='auto_start').first().value == 'True':
                Logic.scheduler_start()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def plugin_unload():
        pass

    @staticmethod
    def scheduler_start():
        try:
            interval = ModelSetting.query.filter_by(key='interval').first().value
            job = Job(package_name, 'ktv_process', interval, Logic.process_download_file0, [u'국내영상 파일 처리'], False)
            scheduler.add_job_instance(job)

            #interval = ModelSetting.query.filter_by(key='interval_upload').first().value
            #job = Job(package_name, 'ktv_file_check', interval, Logic.check_library_completed0, [u'국내영상 Moved 파일 처리'], False)
            #scheduler.add_job_instance(job)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def scheduler_stop():
        try:
            scheduler.remove_job('ktv_process')
            #scheduler.remove_job('ktv_file_check')
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def setting_save(req):
        try:
            for key, value in req.form.items():
                logger.debug('Key:%s Value:%s', key, value)
                entity = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
                entity.value = value
            db.session.commit()
            return True                  
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False

    @staticmethod 
    def check_except_partial(filename, except_partial):
        try:
            #logger.debug(filename)
            #logger.debug(except_partial)
            for tmp in except_partial:
                if tmp == '':
                    continue
                elif filename.find(tmp.strip()) != -1:
                    return True
            
            return False
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False


    @staticmethod
    def for_synoindex(arg):
        try:
            logger.debug('FOR SYNOINDEX : %s' % arg)
            if arg['status'] == 'PROGRESS':
                result = arg['result']
                if 'filename' in result:
                    Logic.send_to_listener(result['filename'])
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def process_download_file0():
        try:
            if app.config['config']['use_celery']:
                result = Logic.process_download_file.apply_async()
                try:
                    flag_rclone_start = result.get(on_message=Logic.for_synoindex, propagate=True)
                    if flag_rclone_start:
                        scheduler.execute_job('rclone')
                except:
                    logger.debug('CELERY on_message not process.. only get() start')
                    try:
                        flag_rclone_start = result.get()
                        if flag_rclone_start:
                            scheduler.execute_job('rclone')
                    except:
                        pass
                #logger.debug('CELERY ktv end.. rclone_start : %s', flag_rclone_start)
            else:
                Logic.process_download_file()
            # 2020-08-08
            if Logic.plex_update_list:
                logger.debug('>> len plex_update_list : %s', len(Logic.plex_update_list))
                for item in Logic.plex_update_list:
                    try:
                        db.session.add(item)
                    except Exception as exception: 
                        logger.error('Exception:%s', exception)
                        logger.error(traceback.format_exc())
                db.session.commit()
                Logic.plex_update_list = []
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    @celery.task(bind=True)
    def process_download_file(self):
        setting_list = Util.db_list_to_dict(db.session.query(ModelSetting).all())

        Logic._DOWNLOAD_PATH = setting_list['download_path']
        except_partial = setting_list['except_partial'].split(',')
        except_genre_remove_epi_number = [x.strip() for x in setting_list['except_genre_remove_epi_number'].split(',')]
        if '' in except_genre_remove_epi_number:
            except_genre_remove_epi_number.remove('')

        library_list = db.session.query(ModelKtvLibrary).all()
        Logic._LIBRARY_ROOT_LIST = []
        for item in library_list:
            if item.library_type == 0:
                drive_type = EntityLibraryPathRoot.DriveType.LOCAL
            else:
                drive_type = EntityLibraryPathRoot.DriveType.RCLONE
            lib = EntityLibraryPathRoot(drive_type=drive_type, mount_path=item.library_path, rclone_path=item.rclone_path, depth=2, replace_for_plex=[item.replace_for_plex_source, item.replace_for_plex_target])
            Logic._LIBRARY_ROOT_LIST.append(lib)

        dir_list = None
        path = Logic._DOWNLOAD_PATH
        list_ = os.listdir(Logic._DOWNLOAD_PATH)
        logger.debug('process_download_file 2')
        logger.debug('list : %s', len(list_))
        # rclone 시작이 필요한가..
        flag_rclone_start = False
        for var in list_:
            try:
                #with db.session.no_autoflush:
                if True:
                    abspath = os.path.join(path, var)
                    telegram_log = None
                    entity = None
                    
                    if os.path.isfile(abspath):
                        if Logic.check_except_partial(var, except_partial):
                            continue
                        telegram_log = package_name + '\n%s\n' % abspath
                        if dir_list is None:
                            logger.debug('process_download_file')
                            # 방송이름 목록
                            dir_list = Logic._make_dir_list()
                            logger.debug('process_download_file 1')
                        logger.debug('===================================')
                        logger.debug('File Process: %s', var)
                        # 방송용 파일이 아니면 
                        entity = EntityShow(var, nd_download_path=path, except_genre_remove_epi_number=except_genre_remove_epi_number)
                        if entity.video_type == EntityShow.VideoType.KOREA_TV:
                            logger.debug('<Move>')       
                            _find_dir = Logic._get_find_dir(dir_list, entity)                        
                            if len(_find_dir) == 1:
                                entity.set_find_library_path(_find_dir[0]) 
                                logger.debug(' - 하나의 폴더 선택됨 : %s', _find_dir[0].abspath)
                                entity.move_file()
                                # 2019-09-01
                                if entity.scan_status == EntityShow.ScanStatus.MOVED and entity.nd_find_library_path.entity_library_root.drive_type == EntityLibraryPathRoot.DriveType.LOCAL:
                                    if app.config['config']['use_celery']:
                                        self.update_state(state='PROGRESS', meta={'filename':entity.move_abspath_local})
                                    else:
                                        Logic.send_to_listener(entity.move_abspath_local)
                                elif entity.scan_status == EntityShow.ScanStatus.MOVED and entity.nd_find_library_path.entity_library_root.drive_type == EntityLibraryPathRoot.DriveType.RCLONE:
                                    if app.config['config']['use_celery']:
                                        self.update_state(state='PROGRESS', meta={'filename':entity.move_abspath_cloud})
                                    else:
                                        Logic.send_to_listener(entity.move_abspath_cloud)

                                entity.modelfile = ModelKtvFile.create(entity)
                                logger.debug(entity.log)
                                # ID를 보내야하기 때문에 commit
                                db.session.add(entity.modelfile)
                                db.session.commit()
                                if entity.scan_status == EntityShow.ScanStatus.MOVED:
                                    try:
                                        import plex
                                        plex.Logic.send_scan_command(entity.modelfile, package_name)
                                    except Exception as exception:
                                        logger.debug('NOT IMPORT PLEX!!')
                                    db.session.add(entity.modelfile)
                                    db.session.commit()
                                if entity.move_type == EntityLibraryPathRoot.DriveType.RCLONE:
                                    flag_rclone_start = True
                            elif len(_find_dir) > 1:
                                logger.debug(' - 선택된 폴더가 2개 이상')
                                logger.debug('  %s', _find_dir[0].abspath)
                                logger.debug('  %s', _find_dir[1].abspath)
                                entity.log += '<파일이동>\n'
                                entity.log += '선택된 폴더 %s개\n' % (len(_find_dir))
                                entity.log += '  %s\n' % _find_dir[0].abspath
                                entity.log += '  %s\n' % _find_dir[1].abspath
                                tmp = os.path.join(Logic._DOWNLOAD_PATH, setting_list['manual_folder_name'] )
                                if not os.path.isdir(tmp):
                                    os.mkdir(tmp)
                                if os.path.exists(os.path.join(tmp, var)):
                                    os.remove(os.path.join(tmp, var))
                                shutil.move(abspath, tmp)
                                if app.config['config']['use_celery']:
                                    self.update_state(state='PROGRESS', meta={'filename':os.path.join(tmp, var)})
                                else:
                                    Logic.send_to_listener(os.path.join(tmp, var))
                                entity.log += '  %s 이동\n' % tmp
                            elif not _find_dir:
                                #continue
                                logger.debug(' - 선택된 폴더 없음')
                                entity.log += '<파일이동>\n'
                                entity.log += '선택된 폴더 없음\n'
                                flag_move = False
                                if entity.daum_info is None:
                                    
                                    #if FileManagerSetting.HOW_TO_PROCESS_NO_DAUM_FILE == 'MOVE_ON_NOMETA_DIR_IN_DOWNLOAD_DIR':
                                    #    tmp = os.path.join(Logic._DOWNLOAD_PATH, self._NO_DAUM_INFO_MOVE_DIRECTORY_NAME )
                                    #    if not os.path.isdir(tmp):
                                    #        os.mkdir(tmp)
                                    #    shutil.move(abspath, tmp)
                                    #    flag_move = True
                                    #elif FileManagerSetting.HOW_TO_PROCESS_NO_DAUM_FILE == 'PROCESS_LIKE_AS_GENRE':

                                    #daum = EntityDaumTV(-1)
                                    try:
                                        import daum_tv
                                        daum = daum_tv.ModelDaumTVShow(-1)
                                        daum.genre = setting_list['no_daum_folder_name']
                                        daum.title = entity.filename_name
                                    except Exception as exception:
                                        logger.error('Exception:%s', exception)
                                        logger.error(traceback.format_exc())
                                        daum = None
                                    entity.daum_info = daum
                                    
                                    

                                if flag_move == False and entity.daum_info:
                                    flag_search = False
                                    for library_root in Logic._LIBRARY_ROOT_LIST:
                                        for _ in library_root.get_genre_list():
                                            if _ == entity.daum_info.genre:
                                                #폴더만 만들어주고 다음번에 이동. 첫번째 선택된곳만
                                                tmp = os.path.join(library_root.mount_path, _, Util.change_text_for_use_filename(entity.daum_info.title) )
                                                
                                                if not os.path.isdir(tmp):
                                                    logger.debug('mkdir:%s', tmp)
                                                    os.mkdir(tmp)
                                                    entity.log += '폴더생성 : %s\n' % tmp
                                                logger.debug('  * 장르:%s [%s] 폴더 생성. 다음 탐색시 이동', _, tmp)
                                                flag_search = True
                                                break
                                        if flag_search: 
                                            break
                                    if not flag_search:
                                        logger.debug('  * 장르:%s 없음.', entity.daum_info.genre)
                                        # TODO 옵션
                                        # 로컬에 장르 만든다
                                        """
                                        _ = os.path.join(self._DOWNLOAD_PATH, 'tmp')
                                        if not os.path.isdir(_):
                                            os.mkdir(_)
                                        """
                                        # 다음번에 방송명 폴더를 만든다???
                                        _ = os.path.join(Logic._LIBRARY_ROOT_LIST[0].mount_path, entity.daum_info.genre)
                                        if not os.path.isdir(_):
                                            os.mkdir(_)
                                            entity.log += '장르 폴더생성 : %s\n' % _
                            telegram_log += entity.log        
                            logger.debug('===================================')
                        # 처리하지 못하는 포멧의 파일
                        else:
                            
                            tmp = os.path.join(Logic._DOWNLOAD_PATH, setting_list['not_ktv_move_folder_name'] )
                            if not os.path.isdir(tmp):
                                os.mkdir(tmp)
                            if os.path.exists(os.path.join(tmp, var)):
                                os.remove(os.path.join(tmp, var))
                            shutil.move(abspath, tmp)
                            if app.config['config']['use_celery']:
                                self.update_state(state='PROGRESS', meta={'filename':os.path.join(tmp, var)})
                            else:
                                Logic.send_to_listener(os.path.join(tmp, var))
                            telegram_log += '처리하지 못하는 파일 형식\n이동:%s\n' % tmp
                    else:
                        #폴더
                        tmp = var + '.mp4'
                        match_flag = False
                        for regex in EntityShow._REGEX_FILENAME:
                            match = re.compile(regex).match(tmp)
                            if match:
                                match_flag = True
                                break
                        if match_flag:
                            try:
                                childs = os.listdir(abspath)
                                # 모두 파일인 경우에만 처리
                                # 2019-07-13
                                for c in childs:
                                    if os.path.isdir(os.path.join(abspath, c)):
                                        continue
                                for c in childs:
                                    tmp = os.path.join(abspath,c)
                                    if os.stat(tmp).st_size < 1000000:
                                        os.remove(tmp)
                                    else:
                                        if os.path.exists(os.path.join(path,c)):
                                            if os.stat(os.path.join(path,c)).st_size >= os.stat(tmp).st_size:
                                                os.remove(tmp)
                                            else:
                                                os.remove(os.path.join(path,c))
                                                shutil.move(tmp, path)
                                        else:
                                            shutil.move(tmp, path)
                                shutil.rmtree(abspath)
                            except Exception as exception: 
                                logger.error('Exception:%s', exception)
                                logger.error(traceback.format_exc())
            except Exception as exception:
                try:
                    db.session.rollback()
                    logger.debug('ROLLBACK!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                except:
                    logger.debug('>>>>>>>>>>>>>>>>>>>>>>>>>>')
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())

            finally:
                try:
                    if ModelSetting.query.filter_by(key='telegram').first().value == 'True' and telegram_log is not None:
                        img = None
                        if entity is not None and entity.daum_info is not None and entity.daum_info.poster_url is not None:
                            img = entity.daum_info.poster_url
                        ToolBaseNotify.send_message(telegram_log, image_url=img, message_id='fileprocess_ktv_result')
                      
                except Exception as exception:
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())


        logger.debug('flag_rclone_start : %s', flag_rclone_start)                
        #self.update_state(state='PROGRESS',meta={'flag_rclone_start':flag_rclone_start})
        #if flag_rclone_start:
        #    scheduler.execute_job('rclone')
        Logic.check_library_completed()
        return flag_rclone_start

    @staticmethod
    def _make_dir_list():
        """
        이동할 폴더목록을 만든다. 방송목록
        규칙 
         - 폴더 depth를 고려하지 않고 파일이 있는 폴더만 목록화
         - 파일이 없는 폴더로 목록화
         - 폴더만 있는 폴더는 카테고리로 간주하여 제외
         - 폴더이름이 'Season', '시즌' 으로 시작할 경우 제외
         - 폴더와 파일이 같이 있는 경우가 있다면?? 일단은 제외

        너무 오래걸려서 depth 추가
        """
        dir_list = []
        for library_root in Logic._LIBRARY_ROOT_LIST:
            #if library_root.depth == 0:
            #    dir_list = Logic._explore(library_root, library_root.mount_path, dir_list)
            #else:
            dir_list = Logic._explore_by_depth(library_root, library_root.mount_path, dir_list, library_root.depth, 1)
        return dir_list
    """
    @staticmethod 
    def _explore(library_root, fnpath, dir_list):
        logger.debug('_explore %s %s %s', library_root, fnpath, dir_list)
        flag_append = False
        flag_exist_file = False
        flag_exist_dir = False
        listdir = os.listdir(fnpath)
        for var in listdir:
            _abspath = os.path.join(fnpath, var)
            if os.path.isdir(_abspath):
                if var.lower().startswith('season') or var.startswith(u'시즌'):
                    flag_append = True
                    break
                elif var.startswith('.'):
                    pass
                else:
                    flag_exist_dir = True
                    self._explore(library_root, _abspath, dir_list)
            else:
                flag_exist_file = True

        if flag_exist_dir and flag_exist_file:
            pass
        elif flag_exist_dir and not flag_exist_file:
            pass
        elif not flag_exist_dir and flag_exist_file:
            flag_append = True
        elif not flag_exist_dir and not flag_exist_file:
            flag_append = True

        if flag_append:
            dir_list.append(EntityLibraryPath(library_root, os.path.basename(fnpath), fnpath))
        return dir_list
    """

    @staticmethod
    def _explore_by_depth(library_root, fnpath, dir_list, library_root_depth, current_depth):
        listdir = os.listdir(fnpath)
        for var in listdir:
            _abspath = os.path.join(fnpath, var)
            if os.path.isdir(_abspath):
                if library_root_depth > current_depth:
                    Logic._explore_by_depth(library_root, _abspath, dir_list, library_root_depth, (current_depth+1))
                else:
                    dir_list.append(EntityLibraryPath(library_root, var, _abspath))
        return dir_list

    @staticmethod
    def _get_find_dir(dir_list, entity):
        ret = []
        for item in dir_list:
            if entity.filename.find(item.basename) != -1:
                ret.append(item)
            elif entity.nd_compare_name.find(item.compare_name) != -1:
                ret.append(item)
            elif entity.nd_compare_name.replace(u'시즌', '').find(item.compare_name.replace(u'시즌', '')) != -1:
                ret.append(item)
            elif entity.daum_info is not None and entity.daum_info.title == item.basename:
                ret.append(item)
        #완전히 일치할 경우
        logger.debug('entity.filename_name : %s entity.nd_compare_name: %s', entity.filename_name, entity.nd_compare_name)
        for item in ret:
            logger.debug('item.basename : %s item.basename: %s', item.basename, item.compare_name)
            if entity.filename_name == item.basename:
                return [item]
            # 2019-05-28
            elif entity.nd_compare_name == item.compare_name:
                return [item]
        return ret
    
    

    # PLEX -> SJVA 로 결과를 전송한 후 호출 
    # /api/scan_complete
    plex_update_list = []
    @staticmethod
    def receive_scan_result(id, filename):
        try:
            import plex
            #with db.session.no_autoflush:
            logger.debug('Receive Scan Completed : %s-%s', id, filename)
            #modelfile = db.session.query(ModelKtvFile).filter_by(id=int(id)).with_for_update().first()
            modelfile = db.session.query(ModelKtvFile).filter_by(id=int(id)).first()
            if modelfile is not None:
                modelfile.scan_status = 3
                modelfile.scan_time = datetime.now()
                #if modelfile.plex_show_id == -1:
                plex.Logic.get_section_id(modelfile, more=True)
                #db.session.commit()
                if scheduler.is_running('ktv_process'):
                    Logic.plex_update_list.append(modelfile)
                    logger.debug('>> plex_update_list insert!!')
                else:
                    db.session.add(modelfile)
                    db.session.commit()
                    logger.debug('>> direct commit!!')

                if ModelSetting.query.filter_by(key='telegram').first().value == 'True':
                    text = '<PLEX 스캔 완료 - KTV>\n%s\n\n%s' % (modelfile.filename, modelfile.plex_part)
                    ToolBaseNotify.send_message(text, message_id='fileprocess_ktv_scan_completed')

                    
        except Exception as exception:
            logger.debug('>>>>> receive_scan_result')
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            
    
    """
    @staticmethod
    def check_library_completed0():
        Logic.check_library_completed()
        return
        try:
            if app.config['config']['use_celery']:
                result =Logic.check_library_completed.apply_async()
                # Logic.process_download_file.apply_async()
                result.get()
            else:
                Logic.check_library_completed()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    """

    # 2019-05-13
    # 업로드 -> 아래로직으로 라이브러리에 파일이 없으면 send_command
    # 결과로 -> scan_completed 반영. show id 가 -1면 수정
    # 아래 로직 다시 타면 in_library로 변경
    # 업로드 체크.. 파일이 없어졌으면... sync path scan 명령을 내린다
    # 파일이 그래도 있다면 업로드다 안되었다고 판단하자.. 만약 copy라면 무시
    #

    @staticmethod
    @celery.task
    def check_library_completed():
        try:
            import plex
            logger.debug('==========Cloud upload file check==========')
            entity_list = ModelKtvFile.get_library_check_list()
            for entity in entity_list:
                logger.debug('filename:%s', entity.filename)
                if entity.move_type == 0: #로컬
                    # 올수가 있을까?
                    plex.Logic.send_scan_command(entity, package_name)
                    db.session.add(entity)
                else:
                    if not os.path.exists(entity.move_abspath_sync):
                        #동기화 완료후 파일을 삭제했다고 가정
                        plex.Logic.send_scan_command(entity, package_name)
                        db.session.add(entity)
                    else:
                        logger.debug(' - upload not completed!!')
                """
                if os.path.exists(entity.get_finalpath()):
                    # 이건 최초 다운받을때 쇼가 아예 없었다면 항상 False이다.
                    # 쇼ID가 없을 때는 전체 라이브러리에서 재 탐색해야한다.
                    exist_in_library = PlexHandle.instance().exist_file_in_library(entity)
                    logger.debug(' - check exist file in library : %s %s', exist_in_library, entity.get_finalpath())
                    if exist_in_library:
                        logger.debug('  * exist!! status change!!') 
                        entity.set_scan_status(EntityShow.ScanStatus.EXIST_IN_LIBRARY)
                        DBManager.update_status_download_korea_tv(entity)
                    else:
                        logger.debug('  * not exist!! send add command!!')
                        self._send_scan_command(entity)
                else:
                    logger.debug(' - upload not completed!!')
                """
            logger.debug('get_image_empty_list')
            entity_list = ModelKtvFile.get_image_empty_list()

            for entity in entity_list:
                logger.debug('filename:%s', entity.filename)
                plex.Logic.get_section_id(entity, more=True)
                db.session.add(entity)
            db.session.commit()
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())  
    

    #####################
    #db
    @staticmethod
    def filelist(req):
        try:
            ret = {}
            page = 1
            page_size = int(db.session.query(ModelSetting).filter_by(key='web_page_size').first().value)
            job_id = ''
            search = ''
            if 'page' in req.form:
                page = int(req.form['page'])
            #if 'job_select' in req.form:
            #    if req.form['job_select'] != 'all':
            #        job_id = int(req.form['job_select'])
            if 'search_word' in req.form:
                search = req.form['search_word']

            query = db.session.query(ModelKtvFile)
            #if job_id != '':
            #    query = query.filter(ModelRcloneFile.job_id==job_id)
            if search != '':
                query = query.filter(ModelKtvFile.plex_abspath.like('%'+search+'%'))
            count = query.count()
            query = (query.order_by(desc(ModelKtvFile.id))
                        .limit(page_size)
                        .offset((page-1)*page_size)
                )
            logger.debug('ModelKtvFile count:%s', count)

            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            #ret['paging'] = paging
            ret['paging'] = Util.get_paging_info(count, page, page_size)
            try:
                import plex
                ret['plex_server_hash'] = plex.Logic.get_server_hash()
            except Exception as exception:
                ret['plex_server_hash'] = ""
            
            return ret
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())


    @staticmethod
    def library_save(req):
        try:
            #with db.session.no_autoflush:
            if True:
                library_id = int(req.form['library_id'])
                if library_id == -1:
                    item = ModelKtvLibrary()

                else:
                    item = db.session.query(ModelKtvLibrary).filter_by(id=library_id).with_for_update().first()

                item.library_type = int(req.form['library_type'])
                item.library_path = req.form['library_path']
                if item.library_type == 1:
                    item.rclone_path = req.form['rclone_path']
                item.replace_for_plex_source = req.form['replace_for_plex_source']
                item.replace_for_plex_target = req.form['replace_for_plex_target']
                item.index = int(req.form['index'])
                #item.local_path = local_path
                db.session.add(item)
                db.session.commit()
                logger.debug('item.library_type:%s',item.library_type)
                if item.library_type != 0: 
                    Logic.call_rclone_plugin(item)
                    
            return True                  
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False

    @staticmethod
    def call_rclone_plugin(item, remove=False):
        local = os.path.join(db.session.query(ModelSetting).filter_by(key='download_path').first().value, 'rclone_%s' % item.rclone_path.split(':')[0], os.path.basename(item.library_path))
        logger.debug('Local:%s', local)
        import rclone
        rclone.Logic.rclone_job_by_ktv(local, item.rclone_path, remove)

    @staticmethod
    def library_list():
        try:
            return db.session.query(ModelKtvLibrary).order_by(ModelKtvLibrary.index).all()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False

    @staticmethod
    def library_remove(req):
        try:
            #with db.session.no_autoflush:
            if True:
                library_id = int(req.form['library_id'])
                lib = db.session.query(ModelKtvLibrary).filter_by(id=library_id).first()
                if lib.library_type != 0: 
                    Logic.call_rclone_plugin(lib, remove=True)
                db.session.delete(lib)
                db.session.commit()
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def reset_db():
        try:
            db.session.query(ModelKtvFile).delete()
            db.session.commit()
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False

    # synoindex를 위해
    ######################
    listener = MyEvent()

    @staticmethod
    def add_listener(f):
        try:
            #Logic.listener_list.append(f)
            #Logic.listener.handle(f)
            Logic.listener += f
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def remove_listener(f):
        try:
            #Logic.listener_list.remove(f)
            #Logic.listener.unhandle(f)
            Logic.listener -= f
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False
    

    @staticmethod
    def send_to_listener(target_file):
        try:
            args = []
            kargs = {'plugin':'ktv', 'type':'add', 'filepath':target_file, 'is_file':True}
            #for f in Logic.library_list:
            #    f(**tmp)
            Logic.listener.fire(*args, **kargs)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    ######################


