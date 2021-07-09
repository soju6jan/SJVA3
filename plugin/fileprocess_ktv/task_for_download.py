# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, re, json, threading, time, shutil, yaml
from datetime import datetime
# third-party
import requests
# third-party
from flask import request, render_template, jsonify, redirect
from sqlalchemy import or_, and_, func, not_, desc

# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util, path_app_root
from framework.common.plugin import LogicModuleBase, default_route_socketio
from tool_base import ToolBaseFile, d
from tool_expand import EntityKtv

# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting


class Task(object):
    @staticmethod
    @celery.task(bind=True)
    def start(self, configs, call_module):
        #logger.warning(f"Task.start : {call_module}")

        is_dry = True if call_module.find('_dry') != -1 else False
        for config in configs:
            source = config['소스 폴더']
            target = config['타겟 폴더']
            error = config['에러 폴더']

            for base, dirs, files in os.walk(source):
                for idx, original_filename in enumerate(files):
                    #if idx>0:return
                    if ModelSetting.get_bool(f"{call_module}_task_stop_flag"):
                        logger.warning("사용자 중지")
                        return 'stop'
                    try:
                        data = {'filename':original_filename, 'foldername':base, 'log':[]}
                        filename = original_filename
                        #logger.warning(f"{idx} / {len(files)} : {filename}")
                        filename = Task.process_pre(config, base, filename, is_dry, data)
                        data['filename_pre'] = filename
                        if filename is None:
                            continue
                        entity = EntityKtv(filename, dirname=base, meta=True, config=config)
                        data['entity'] = entity.data
                        if entity.data['filename']['is_matched']:
                            if entity.data['meta']['find']:
                                Task.move_file(config, entity, os.path.join(base, original_filename), target, data, is_dry)
                            else:
                                if entity.data['process_info']['status'] == 'ftv':
                                    data['result_folder'] = os.path.join(config['경로 설정']['ftv'].format(error=error), f"{entity.data['process_info']['ftv_title']} ({entity.data['process_info']['ftv_year']})", f"Season {entity.data['filename']['sno']}")
                                else:
                                    data['result_folder'] = config['경로 설정']['no_meta'].format(error=error)
                                    if config['메타 검색 실패시 방송별 폴더 생성']:
                                        data['result_folder']  = os.path.join(data['result_folder'], entity.data['filename']['name'])

                                data['result_filename'] = original_filename
                                if is_dry == False:
                                    ToolBaseFile.file_move(os.path.join(base, original_filename), data['result_folder'], data['result_filename'])
                        else:
                            data['result_folder'] = config['경로 설정']['no_tv'].format(error=error)
                            data['result_filename'] = original_filename
                            if is_dry == False:
                                ToolBaseFile.file_move(os.path.join(base, original_filename), data['result_folder'], data['result_filename'])
                    except Exception as e: 
                        P.logger.error(f"Exception:{e}")
                        P.logger.error(traceback.format_exc())
                    finally:
                        if app.config['config']['use_celery']:
                            self.update_state(state='PROGRESS', meta=data)
                        else:
                            P.logic.get_module(call_module.replace('_dry', '')).receive_from_task(data, celery=False)
                        

                if base != source and len(os.listdir(base)) == 0 :
                    try:
                        if is_dry == False:
                            os.rmdir(base)
                    except Exception as e: 
                        P.logger.error(f"Exception:{e}")
                        P.logger.error(traceback.format_exc())
            for base, dirs, files in os.walk(source):
                if base != source and len(dirs) == 0 and len(files) == 0:
                    try:
                        if is_dry == False:
                            os.rmdir(base)
                    except Exception as e: 
                        P.logger.error(f"Exception:{e}")
                        P.logger.error(traceback.format_exc())
        
        logger.debug(f"task {call_module} 종료")
        return 'wait'


    def process_pre(config, base, original_filename, is_dry, data):
        filename = original_filename
        if '전처리' not in config:
            return filename

        for key, value in config['전처리'].items():
            if key == '변환':
                if value is None:
                    continue
                for rule in value:
                    try:
                        filename = re.sub(rule['source'], rule['target'], filename).strip()
                    except Exception as e: 
                            P.logger.error(f"Exception:{e}")
                            P.logger.error(traceback.format_exc())

            elif key == '삭제':
                if value is None:
                    continue
                for regex in value:
                    try:
                        if re.search(regex, filename):
                            try:
                                data['result_folder'] = 'REMOVE'
                                if is_dry == False:
                                    os.remove(os.path.join(base, original_filename))
                            except Exception as e: 
                                P.logger.error(f"Exception:{e}")
                                P.logger.error(traceback.format_exc())
                            finally:
                                return
                    except Exception as e: 
                            P.logger.error(f"Exception:{e}")
                            P.logger.error(traceback.format_exc())
            
            elif key == '이동':
                if value is None:
                    continue
                for target, regex_list in value.items():
                    for regex in regex_list:
                        try:
                            if re.search(regex, filename):
                                if target[0] == '/' or target[1] == ':': # 절대경로
                                    target_folder = target
                                else:
                                    if target in config['경로 설정']:
                                        target_folder = config['경로 설정'][target].format(error=config['에러 폴더'])
                                    else:
                                        target_folder = os.path.join(config['에러 폴더'], target)
                                data['result_folder'] = target
                                data['result_filename'] = original_filename
                                if is_dry == False:
                                    ToolBaseFile.file_move(os.path.join(base, original_filename), target_folder, original_filename)
                                return
                        except Exception as e: 
                                P.logger.error(f"Exception:{e}")
                                P.logger.error(traceback.format_exc())
        return filename




    def move_file(config, entity, source_path, target_folder, data, is_dry):
        #if entity.data['process_info']['status'] in ['number_and_date_match', 'meta_epi_empty', 'number_and_date_match_by_release', 'number_and_date_match_ott', 'meta_epi_not_find', 'no_date']:
        if True:
            year_tmp = entity.data['meta']['info']['year']
            if year_tmp == 0 or year_tmp == '0':
                year_tmp = ''
            genre = entity.data['meta']['info']['genre'][0].split('/')[0]
            if entity.data['meta']['info']['code'][1] == 'D':
                genre = config['메타 사이트별 장르 접두사']['daum'] + ' ' + genre
            elif entity.data['meta']['info']['code'][1] == 'W':
                genre = config['메타 사이트별 장르 접두사']['wavve'] + ' ' + genre
            elif entity.data['meta']['info']['code'][1] == 'V':
                genre = config['메타 사이트별 장르 접두사']['tving'] + ' ' + genre
            genre = genre.strip()
            genre = config['장르 변경 규칙'].get(genre, genre)

            program_folder = config['타겟 폴더 구조'].format(
                title=ToolBaseFile.text_for_filename(entity.data['meta']['info']['title']), 
                year=year_tmp,
                studio=entity.data['meta']['info']['studio'],
                genre=genre,
                release=entity.data['filename']['release'],
            )
            tmps = program_folder.replace('(1900)', '').replace('()', '').replace('[]', '').strip()
            tmps = re.sub("\s{2,}", ' ', tmps) 
            tmps = re.sub("/{2,}", '/', tmps) 
            tmps = tmps.split('/')
            program_folder = os.path.join(target_folder, *tmps)
        
            #logger.debug(f"program_folder : {program_folder}")
            #logger.error(entity.data['process_info']['status'])

            program_folder = Task.get_prefer_folder(config, entity, program_folder)
            
            target_filename = entity.get_newfilename()
            if target_filename is not None:
                #logger.warning(program_folder)
                #logger.error(f"original : {entity.data['filename']['original']}")
                #logger.error(f'target_filename : {target_filename}')
                data['result_folder'] = program_folder
                data['result_filename'] = target_filename
                if is_dry == False:
                    ToolBaseFile.file_move(source_path, program_folder, target_filename)
            else:
                logger.error(f"타겟 파일 None")

    def get_prefer_folder(config, entity, program_folder):
        if config['타겟 폴더 탐색 사용'] == '미사용':
            return program_folder
        
        compare_folder_name = os.path.split(program_folder)[-1]
        if 'target_folder_list' not in config:
            config['target_folder_list'] = []
            for base, dirs, files in os.walk(config['타겟 폴더']):
                for _dir in dirs:
                    logger.debug(os.path.join(base, _dir))
                    config['target_folder_list'].append(os.path.join(base, _dir))

        for _dir in config['target_folder_list']:
            folder_name = os.path.split(_dir)[-1]
            if config['타겟 폴더 탐색 사용'] == '방송제목포함':
                if folder_name.find(entity.data['meta']['info']['title']) != -1:
                    return _dir
            elif config['타겟 폴더 탐색 사용'] == '완전일치':
                if compare_folder_name == folder_name:
                    return _dir
        return program_folder 