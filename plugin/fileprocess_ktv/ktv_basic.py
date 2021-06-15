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
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from framework.common.plugin import LogicModuleBase, default_route_socketio
from tool_base import ToolBaseFile, d

# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting
name = 'basic'


#########################################################

class LogicKtvBasic(LogicModuleBase):
    db_default = {
        f'{name}_db_version' : '1',
        f'{name}_interval' : '30',
        f'{name}_auto_start' : 'False',
        f'{name}_path_source' : '',
        f'{name}_path_target' : '',
        f'{name}_path_error' : '',
        f'{name}_folder_format' : '{genre}/{title}',
        f'{name}_advaned' : '',
    }

    def __init__(self, P):
        super(LogicKtvBasic, self).__init__(P, 'setting', scheduler_desc='국내TV 파일처리 - 기본')
        self.name = name


    def process_menu(self, sub, req):
        try:
            arg = P.ModelSetting.to_dict()
            arg['sub'] = self.name
            if sub == 'setting':
                arg['scheduler'] = str(scheduler.is_include(self.get_scheduler_name()))
                arg['is_running'] = str(scheduler.is_running(self.get_scheduler_name()))
            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"{package_name}/{name}/{sub}")


    def process_ajax(self, sub, req):
        try:
            pass
        except Exception as e: 
            P.logger.error('Exception:%s', e)
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})

    def scheduler_function(self):
        Task.start()
        return
        if app.config['config']['use_celery']:
            result = Task.start.apply_async()
            try:
                ret = result.get(on_message=self.receive_from_task, propagate=True)
            except:
                logger.debug('CELERY on_message not process.. only get() start')
                ret = result.get()
        else:
            Task.start()
    
    def receive_from_task(self, arg, celery=True):
        logger.warning(arg)

    def plugin_load(self):
        Task.start()
        #load_yaml()


    #########################################################


def load_yaml():
    logger.error('1111111111111111111')
    import yaml

    with open(os.path.join(path_data, 'db', f"{package_name}.yaml")) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
        #print(members)

    logger.warning(d(config))
    return config


from tool_expand import EntityKtv

class Task(object):

    @staticmethod
    @celery.task(bind=True)
    def start(self):
        #if app.config['config']['use_celery']:
        #    self.update_state(state='PROGRESS', meta=data)
        #else:
        #    P.logic.get_module('jav_censored_tool').receive_from_task(data, celery=False)
        config = load_yaml()

        logger.warning(f"Task.start")
        source = ModelSetting.get(f"{name}_path_source")
        target = ModelSetting.get(f"{name}_path_target")

        for base, dirs, files in os.walk(source):
            for idx, original_filename in enumerate(files):
                #if idx>0:return
                try:
                    filename = original_filename
                    logger.warning(f"{idx} / {len(files)} : {filename}")
                    filename = Task.process_pre(config, base, filename)
                    if filename is None:
                        continue

                    entity = EntityKtv(filename, dirname=base, meta=True)
                    if entity.data['filename']['is_matched']:
                        if entity.data['meta']['find']:
                            logger.debug(f"메타 매칭 : {entity.data['meta']['info']['code'] } {entity.data['meta']['info']['title'] }")
                            Task.move_file(config, entity, os.path.join(base, original_filename), target)
                        else:
                            logger.error(f"메타 못찾음")
                            if entity.data['process_info']['status'] == 'ftv':
                                ToolBaseFile.file_move(os.path.join(base, original_filename), os.path.join(ModelSetting.get(f'{name}_path_error'), config['foldername']['ftv'], f"{entity.data['process_info']['ftv_title']} ({entity.data['process_info']['ftv_year']})", f"Season {entity.data['filename']['sno']}"), original_filename)
                            else:
                                ToolBaseFile.file_move(os.path.join(base, original_filename), os.path.join(ModelSetting.get(f'{name}_path_error'), config['foldername']['no_meta']), original_filename)
                    else:
                        logger.error(f"형식 안맞음")
                        ToolBaseFile.file_move(os.path.join(base, original_filename), os.path.join(ModelSetting.get(f'{name}_path_error'), config['foldername']['no_ktv']), original_filename)
                except Exception as e: 
                    P.logger.error(f"Exception:{e}")
                    P.logger.error(traceback.format_exc())
            
            if base != source and len(os.listdir(base)) == 0 :
                try:
                    os.rmdir(base)
                except Exception as e: 
                    P.logger.error(f"Exception:{e}")
                    P.logger.error(traceback.format_exc())
        for base, dirs, files in os.walk(source):
            if base != source and len(dirs) == 0 and len(files) == 0:
                try:
                    os.rmdir(base)
                except Exception as e: 
                    P.logger.error(f"Exception:{e}")
                    P.logger.error(traceback.format_exc())


        logger.error(f"종료")


    def process_pre(config, base, original_filename):
        filename = original_filename
        if '전처리' not in config:
            return filename

        logger.error(filename)
        for key, value in config['전처리'].items():
            if key == '변환':
                if value is None:
                    continue
                for rule in value:
                    try:
                        logger.debug(f"rule : {rule['source']} => {rule['target']}")
                        filename = re.sub(rule['source'], rule['target'], filename)
                        logger.warning(f"변환값 : {filename}")
                    except Exception as e: 
                            P.logger.error(f"Exception:{e}")
                            P.logger.error(traceback.format_exc())

            elif key == '삭제':
                if value is None:
                    continue
                for regex in value:
                    try:
                        if re.search(regex, filename):
                            logger.debug(f"규칙에 의해 삭제 : {regex}")
                            try:
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
                                logger.debug(f"규칙에 의해 이동 : {regex}")
                                if target in config['foldername']:
                                    target_folder = os.path.join(ModelSetting.get(f"{name}_path_error"), target)
                                else:
                                    target_folder = target
                                ToolBaseFile.file_move(os.path.join(base, original_filename), target_folder, original_filename)
                                return
                        except Exception as e: 
                                P.logger.error(f"Exception:{e}")
                                P.logger.error(traceback.format_exc())
        return filename




    def move_file(config, entity, source_path, target_folder):
        pass
        logger.error(entity.data['process_info']['status'])
        if entity.data['process_info']['status'] in ['number_and_date_match', 'meta_epi_empty', 'number_and_date_match_by_release', 'number_and_date_match_ott', 'meta_epi_not_find', 'no_date']:
        #if True:
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

            program_folder = ModelSetting.get(f'{name}_folder_format').format(
                title=ToolBaseFile.text_for_filename(entity.data['meta']['info']['title']), 
                year=year_tmp,
                studio=entity.data['meta']['info']['studio'],
                genre=genre,
                release=entity.data['filename']['release'],
            )
            tmps = program_folder.replace('()', '').replace('[]', '').strip()
            tmps = re.sub("\s{2,}", ' ', tmps) 
            tmps = re.sub("/{2,}", '/', tmps) 
            tmps = tmps.split('/')
            program_folder = os.path.join(target_folder, *tmps)
        
            logger.warning(f"program_folder : {program_folder}")
            logger.error(entity.data['process_info']['status'])
            if entity.data['process_info']['status'] == 'meta_epi_empty':
                logger.error(d(entity.data['meta']['info']['extra_info']['episodes']))
            
            target_filename = entity.get_newfilename()
            if target_filename is not None:
                logger.warning(program_folder)
                logger.error(f"original : {entity.data['filename']['original']}")
                logger.error(f'target_filename : {target_filename}')
                ToolBaseFile.file_move(source_path, program_folder, target_filename)
            else:
                logger.error(f"타겟 파일 None")


            
        