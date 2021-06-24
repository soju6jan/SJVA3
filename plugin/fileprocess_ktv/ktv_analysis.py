# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, re, json, threading, time, shutil, fnmatch, glob
from datetime import datetime, timedelta
# third-party
import requests
# third-party
from flask import request, render_template, jsonify, redirect
from sqlalchemy import or_, and_, func, not_, desc

# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from framework.common.plugin import LogicModuleBase, default_route_socketio
from tool_expand import ToolExpandFileProcess
from tool_base import ToolShutil, d, ToolUtil, ToolBaseFile
from tool_expand import EntityKtv

# 패키지방과 음악사이
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting
name = 'analysis'
#########################################################

class LogicKtvAnalysis(LogicModuleBase):
    db_default = {
        f'{name}_db_version' : '1',
        #f'{name}_interval' : '0 7 * * *',
        #f'{name}_auto_start' : 'False',
        f'{name}_path' : '',
        f'{name}_path_source' : '',
        f'{name}_path_finish' : '',
        f'{name}_path_incomplete' : '',
        #f'{name}_not_movie_day' : '0',
        f'{name}_task_stop_flag' : 'False',
        f'{name}_remove_empty_folder' : 'True',
    }

    def __init__(self, P):
        super(LogicKtvAnalysis, self).__init__(P, 'setting', scheduler_desc='국내TV 파일처리 - 폴더분석')
        self.name = name
        self.data = {
            'data' : [],
            'is_working' : 'wait'
        }
        default_route_socketio(P, self)
        #app.config['config']['use_celery'] = False

    def process_menu(self, sub, req):
        try:
            arg = P.ModelSetting.to_dict()
            arg['sub'] = self.name
            if sub == 'setting':
                arg['scheduler'] = str(scheduler.is_include(self.get_scheduler_name()))
                arg['is_running'] = str(scheduler.is_running(self.get_scheduler_name()))
            elif sub == 'status':
                arg['apikey'] = SystemModelSetting.get('auth_apikey')
            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"{package_name}/{name}/{sub}")

    def process_ajax(self, sub, req):
        try:
            if sub == 'command':
                command = req.form['command']
                #logger.warning(command)
                ret = {}
                if command == 'start':
                    ret = {'ret':'success', 'msg':'작업을 시작합니다.'}
                    analysis_path = req.form['arg1']
                    ModelSetting.set(f'{name}_path', analysis_path)
                    def func():
                        time.sleep(1)
                        self.scheduler_function()
                    th = threading.Thread(target=func, args=())
                    th.setDaemon(True)
                    th.start()
                elif command == 'stop':
                    if self.data['is_working'] == 'run':
                        ModelSetting.set(f'{name}_task_stop_flag', 'True')
                        ret = {'ret':'success', 'msg':'잠시 후 중지됩니다.'}
                    else:
                        ret = {'ret':'warning', 'msg':'대기중입니다.'}
                elif command == 'refresh':
                    self.refresh_data()
                    return jsonify(ret)
                elif command == 'move':
                    ret = self.folder_move(int(req.form['arg1']), req.form['arg2'], req.form['arg3'])
                elif command == 'rename':
                    ret = self.file_rename(req.form['arg1'], req.form['arg2'])
                elif command == 'move_file_other':
                    ret = self.move_file_other(req.form['arg1'])
                elif command == 'file_remove':
                    ret = self.file_remove(req.form['arg1'])
                elif command == 'folder_remove':
                    ret = self.folder_remove(int(req.form['arg1']))
                elif command == 'insert_season':
                    ret = self.insert_season(int(req.form['arg1']))
                return jsonify(ret)


        except Exception as e: 
            P.logger.error('Exception:%s', e)
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'exception', 'log':str(e)})


    def scheduler_function(self):
        self.data['data'] = []
        self.data['is_working'] = 'run'
        self.refresh_data()
        ModelSetting.set(f'{name}_task_stop_flag', 'False')
        if app.config['config']['use_celery']:
            result = Task.start.apply_async()
            try:
                ret = result.get(on_message=self.receive_from_task, propagate=True)
            except:
                logger.debug('CELERY on_message not process.. only get() start')
                ret = result.get()
        else:
            Task.start()
        self.data['is_working'] = ret
        self.refresh_data()

    #########################################################

    def refresh_data(self, index=-1):
        #logger.warning(f"refresh_data : {index}")
        if index == -1:
            self.socketio_callback('refresh_all', self.data)
        else:
            self.socketio_callback('refresh_one', self.data['data'][index])


    def receive_from_task(self, arg, celery=True):
        try:
            result = None
            if celery:
                if arg['status'] == 'PROGRESS':
                    result = arg['result']
            else:
                result = arg
            if result is not None:
                result['index'] = len(self.data['data'])
                self.data['data'].append(result)
                self.refresh_data(index=result['index'])
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    def folder_move(self, index, target, mode):
        select_data = self.data['data'][index]
        def func():
            time.sleep(1)
            if mode == 'normal':
                parent = os.path.dirname(target)
                if os.path.exists(parent) == False:
                    os.makedirs(parent)
                shutil.move(select_data['folder_path'], target)
                new_data = {'index' : index, 'status':'move', 'target' : target}
                self.data['data'][index] = new_data
                self.refresh_data(index=index)
            elif mode == 'season':
                if os.path.exists(target) == False:
                    os.makedirs(target)
                new_target = os.path.join(target, f"Season {select_data['entity']['meta']['info']['season']} {select_data['entity']['meta']['info']['title']}")
                shutil.move(select_data['folder_path'], new_target)
                new_data = {'index' : index, 'status':'move', 'target' : new_target}
                self.data['data'][index] = new_data
                self.refresh_data(index=index)


        if os.path.exists(select_data['folder_path']) == False:
            ret = {'ret':'danger', 'msg':'폴더가 없습니다.'}
        #elif os.path.exists(select_data['target_fodler']):
        #    ret = {'ret':'danger', 'msg':'대상 폴더가 이미 있습니다.'}
        else:
            th = threading.Thread(target=func, args=())
            th.setDaemon(True)
            th.start()
            ret = {'ret':'success', 'msg':'이동을 시작합니다.'}
        return ret


    def folder_remove(self, index):
        folder = self.data['data'][index]['folder_path']
        def func():
            time.sleep(1)
            ret = ToolBaseFile.rmtree(folder)
            new_data = {'index' : index, 'status':'remove', 'target' : folder}
            self.data['data'][index] = new_data
            self.refresh_data(index=index)

        if os.path.exists(folder) == False:
            ret = {'ret':'danger', 'msg':'폴더가 없습니다.'}
        else:
            th = threading.Thread(target=func, args=())
            th.setDaemon(True)
            th.start()
            ret = {'ret':'success', 'msg':'폴더를 삭제합니다.'}
        return ret


    def file_rename(self, index, target):
        idx = index.split('_')
        def func(folder, source, target):
            time.sleep(1)
            #shutil.move(os.path.join(folder, source), os.path.join(folder, target))
            os.rename(os.path.join(folder, source), os.path.join(folder, target))
            new_data = {'folder_path' : folder}
            Task.analysis(new_data)
            new_data['index'] = int(idx[0])
            self.data['data'][int(idx[0])] = new_data
            self.refresh_data(index=int(idx[0]))
        
        folder = self.data['data'][int(idx[0])]['folder_path']
        source = self.data['data'][int(idx[0])]['files'][int(idx[1])]['filename']['original']
        if os.path.exists(os.path.join(folder, source)) == False:
            ret = {'ret':'danger', 'msg':'파일이 없습니다.'}
        elif os.path.exists(os.path.join(folder, target)):
            ret = {'ret':'danger', 'msg':'대상 파일이 이미 있습니다.'}
        else:
            th = threading.Thread(target=func, args=(folder, source, target))
            th.setDaemon(True)
            th.start()
            ret = {'ret':'success', 'msg':'파일명을 변경합니다.'}
        return ret


    def move_file_other(self, index):
        idx = index.split('_')
        def func(folder, source):
            time.sleep(1)
            other = os.path.join(folder, 'other')
            if os.path.exists(other) == False:
                os.makedirs(other)
            shutil.move(os.path.join(folder, source), other)
            new_data = {'folder_path' : folder}
            Task.analysis(new_data)
            new_data['index'] = int(idx[0])
            self.data['data'][int(idx[0])] = new_data
            self.refresh_data(index=int(idx[0]))

        folder = self.data['data'][int(idx[0])]['folder_path']
        source = self.data['data'][int(idx[0])]['files'][int(idx[1])]['filename']['original']
        filepath = os.path.join(folder, source)
        if os.path.exists(filepath) == False:
            ret = {'ret':'danger', 'msg':'파일이 없습니다.'}
        #elif os.path.exists(os.path.join(folder, target)):
        #    ret = {'ret':'danger', 'msg':'대상 파일이 이미 있습니다.'}
        else:
            th = threading.Thread(target=func, args=(folder, source))
            th.setDaemon(True)
            th.start()
            ret = {'ret':'success', 'msg':'파일을 이동합니다.'}
        return ret


    def file_remove(self, index):
        idx = index.split('_')
        def func(folder, source):
            time.sleep(1)
            os.remove(os.path.join(folder, source))
            new_data = {'folder_path' : folder}
            Task.analysis(new_data)
            new_data['index'] = int(idx[0])
            self.data['data'][int(idx[0])] = new_data
            self.refresh_data(index=int(idx[0]))

        folder = self.data['data'][int(idx[0])]['folder_path']
        source = self.data['data'][int(idx[0])]['files'][int(idx[1])]['filename']['original']
        filepath = os.path.join(folder, source)
        if os.path.exists(filepath) == False:
            ret = {'ret':'danger', 'msg':'파일이 없습니다.'}
        else:
            th = threading.Thread(target=func, args=(folder, source))
            th.setDaemon(True)
            th.start()
            ret = {'ret':'success', 'msg':'파일을 삭제합니다.'}
        return ret
    

    def insert_season(self, index):
        folder = self.data['data'][index]['folder_path']
        def func():
            time.sleep(1)
            #shutil.move(os.path.join(folder, source), os.path.join(folder, target))
            
            select_data = self.data['data'][index]
            season_no = select_data['entity']['meta']['info']['season']
            if season_no != -1:
                for item in self.data['data'][index]['files']:
                    target = item['filename']['original']
                    target = target.replace(f".E{str(item['filename']['no']).zfill(2)}.", f".S{str(season_no).zfill(2)}E{str(item['filename']['no']).zfill(2)}.")
                    target = target.replace(f".e{str(item['filename']['no']).zfill(2)}.", f".s{str(season_no).zfill(2)}e{str(item['filename']['no']).zfill(2)}.")
                    os.rename(os.path.join(folder, item['filename']['original']), os.path.join(folder, target))
            new_data = {'folder_path' : folder}
            Task.analysis(new_data)
            new_data['index'] = index
            self.data['data'][index] = new_data
            self.refresh_data(index=index)
        
        if os.path.exists(folder) == False:
            ret = {'ret':'danger', 'msg':'폴더가 없습니다.'}
        else:
            th = threading.Thread(target=func, args=())
            th.setDaemon(True)
            th.start()
            ret = {'ret':'success', 'msg':'시즌 번호 추가 작업을 시작합니다.'}
        return ret

  








class Task(object):
    
    @staticmethod
    @celery.task(bind=True)
    def start(self):
        #app.config['config']['use_celery'] = False
        #if app.config['config']['use_celery']:
        #    self.update_state(state='PROGRESS', meta=data)
        #else:
        #    P.logic.get_module('jav_censored_tool').receive_from_task(data, celery=False)
        logger.warning(f"Analysis Task.start")
        folder_path = ModelSetting.get(f'{name}_path')
        logger.warning(f"분석 폴더 : {folder_path}")

        for base, dirs, files in os.walk(folder_path):
            if ModelSetting.get_bool(f"{name}_task_stop_flag"):
                logger.warning("사용자 중지")
                return 'stop'
            if len(dirs) == 0 and len(files) == 0:
                if ModelSetting.get_bool(f"{name}_remove_empty_folder"):
                    ret = ToolBaseFile.rmtree(base)
                    logger.error(f"폴더 삭제 : {base} {ret}")

            if len(files) > 0: # 파일만 있는 폴더
                if base.split('/')[-1] in ['behindthescenes', 'deleted', 'featurette', 'interview', 'scene', 'short', 'trailer', 'other']:
                    logger.warning(f"base : {base}")
                    continue
                #logger.warning(base)
                data = {'folder_path' : base}
                Task.analysis(data)
                if app.config['config']['use_celery']:
                    self.update_state(state='PROGRESS', meta=data)
                else:
                    P.logic.get_module(f'{name}').receive_from_task(data, celery=False)
                #return
        logger.warning(f"종료")
        return 'wait'


    @staticmethod
    def analysis(data):

        logger.warning(f"분석시작 : {data['folder_path']}")

        data['folder_name'] = os.path.basename(data['folder_path'])
        data['keyword'] = re.sub('\[.*?\]', '', data['folder_name'] )
        match = re.search('\((?P<year>\d+)\)',  data['keyword'])
        try:
            data['year'] = int(match.group('year')) if match else -1
            if data['year'] < 1940 or data['year'] > 2030:
                raise Exception()
        except:
            data['year'] = -1
        data['keyword'] = re.sub('\((?P<year>\d+)\)', '', data['keyword']).strip()
        
        
        entity = EntityKtv(data['keyword'], meta=True, is_title=True)
        data['entity'] = entity.data
        
        if entity.data['meta']['find']:
            data['listdir']  = os.listdir(data['folder_path'])
            data['files']  = []
            data['folders'] = []

            data['min_date'] = {'value':999999, 'file':''}
            data['max_date'] = {'value':0, 'file':''}
            data['min_no'] = {'value':9999, 'file':''}
            data['max_no'] = {'value':-1, 'file':''}
            data['episode_keys'] = []
            for f in data['listdir']:
                if os.path.isdir(os.path.join(data['folder_path'], f)):
                    data['folders'].append(f)
                    continue
                else:
                    #data['files'][f] = {}
                    tmp_entity = EntityKtv(f)
                    if tmp_entity.data['filename']['no'] not in data['episode_keys']:
                        data['episode_keys'].append(tmp_entity.data['filename']['no'])
                    #logger.warning(d(tmp.data))
                    stat = os.stat(os.path.join(data['folder_path'], f))
                    tmp_entity.data['size'] = ToolUtil.sizeof_fmt(stat.st_size)
                    tmp_entity.data['ctime'] = ToolUtil.timestamp_to_datestr(stat.st_ctime)
                    #logger.warning(tmp_entity.data)

                    data['files'].append(tmp_entity.data)
                    try:
                        tmp = int(tmp_entity.data['filename']['date'])
                        if tmp > data['max_date']['value']:
                            data['max_date']['value'] = tmp
                            data['max_date']['file'] = f
                        if tmp < data['min_date']['value']:
                            data['min_date']['value'] = tmp
                            data['min_date']['file'] = f
                    except:
                        pass
                    try:
                        tmp = tmp_entity.data['filename']['no']
                        if tmp > data['max_no']['value']:
                            data['max_no']['value'] = tmp
                            data['max_no']['file'] = f
                        if tmp < data['min_no']['value']:
                            data['min_no']['value'] = tmp
                            data['min_no']['file'] = f
                    except Exception as exception: 
                        logger.error('Exception:%s', exception)
                        logger.error(traceback.format_exc())

            data['files'] = sorted(data['files'], key = lambda k: k['filename']['no'])


            data['episode_keys'] = list(sorted(data['episode_keys']))
            data['episode_keys_empty'] = []
            try:
                meta_max = 0
                if entity.data['meta']['info']['status'] == 2 and len(data['episode_keys']) > 0:
                    keys = entity.data['meta']['info']['extra_info']['episodes'].keys()
                    if len(keys) > 0:
                        meta_max = max(keys)
                    #logger.warning(meta_max)
                last_max = max([meta_max, data['episode_keys'][-1]])
                #logger.warning(last_max)
                for i in range(data['episode_keys'][0]+1, last_max+1):
                    if i not in data['episode_keys']:
                        data['episode_keys_empty'].append(i)
            except Exception as e:
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
            #logger.warning(data['episode_keys_empty'])
            #logger.warning(f"보유 에피소드 수 : {len(data['episode_keys'])}")
            #logger.warning(f"보유 에피소드 : {data['episode_keys']}")
            #logger.warning(f"최대날짜 : {data['max_date']}")
            #logger.warning(f"파일수 : {len(data['listdir'])} files 수 : {len(data['episode_keys'])}")
            
            #today = int(datetime.now().strftime('%Y%m%d')[2:])
            today = datetime.now()
            try:
                tmp = str(data['max_date']['value'])
                if tmp[0] in ['8', '9']:
                    tmp = '19' + tmp
                else:
                    tmp = '20' + tmp
                max_date = datetime.strptime(tmp, '%Y%m%d')
            except:
                max_date = today

            data['day_delta'] = (today - max_date).days
            #if entity.data['meta']['info']['status'] == 2 and (data['day_delta'] > ModelSetting.get_int(f'{name}_not_movie_day') or ModelSetting.get_int(f'{name}_not_movie_day') == 0):
            if entity.data['meta']['info']['status'] == 2:
                data['move_result'] = 'finish'
            else:
                data['move_result'] = 'is_onair'

            data['target_fodler'] = ''
            if data['move_result'] == 'finish':
                if entity.data['meta']['info']['episode'] > 0:
                    if len(data['episode_keys']) >= entity.data['meta']['info']['episode']:
                        # 종영이고 메타에 에피수가 있고 모두 있음
                        data['episode_result'] = 'finish_all'
                        data['target_fodler'] = data['folder_path'].replace(ModelSetting.get(f'{name}_path_source'), ModelSetting.get(f'{name}_path_finish'))
                    else:
                        # 종영이고 메타에 에피수가 있고 일부만 있음
                        data['episode_result'] = 'finish_part'
                        data['target_fodler'] = data['folder_path'].replace(ModelSetting.get(f'{name}_path_source'), ModelSetting.get(f'{name}_path_incomplete'))
                elif data['max_no']['value'] - data['min_no']['value'] + 1 == len(data['episode_keys']):
                    # 종영이고 메타에 에피수가 없고 최소~최대 까지 있음
                    data['episode_result'] = 'meta_no_epi_count_all'
                    data['target_fodler'] = data['folder_path'].replace(ModelSetting.get(f'{name}_path_source'), ModelSetting.get(f'{name}_path_finish'))
                else:
                    # 종영이고 메타에 에피수가 없고 최소~최대 범위내에서 일부없음
                    data['episode_result'] = 'meta_no_epi_count_part'
                    data['target_fodler'] = data['folder_path'].replace(ModelSetting.get(f'{name}_path_source'), ModelSetting.get(f'{name}_path_incomplete'))
                
                data['target_fodler1'] = data['folder_path'].replace(ModelSetting.get(f'{name}_path_source'), ModelSetting.get(f'{name}_path_finish'))
                data['target_fodler2'] = data['folder_path'].replace(ModelSetting.get(f'{name}_path_source'), ModelSetting.get(f'{name}_path_incomplete'))
            else:
                if data['max_no']['value'] - data['min_no']['value'] + 1 == len(data['episode_keys']):
                    # onair이고 최소~최대 까지 있음
                    data['episode_result'] = 'onalr_all'
                else:
                    # onair이고 최소~최대 범위내에서 일부 없음
                    data['episode_result'] = 'onalr_part'



