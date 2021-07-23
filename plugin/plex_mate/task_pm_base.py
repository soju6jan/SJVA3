# python
import os, sys, traceback, re, json, threading, time, shutil, fnmatch, glob
from datetime import datetime, timedelta
# third-party
import requests

# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from plugin import LogicModuleBase, default_route_socketio
from tool_expand import ToolExpandFileProcess
from tool_base import ToolShutil, d, ToolUtil, ToolBaseFile, ToolOSCommand
from tool_expand import EntityKtv

from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting


class Task(object):
    
    @staticmethod
    @celery.task()
    def get_size(args):
        logger.warning(args)
        ret = ToolOSCommand.get_size(args[0])
        logger.warning(ret)
        return ret

    @staticmethod
    @celery.task()
    def backup(args):
        try:
            logger.warning(args)
            db_path = args[0]
            if os.path.exists(db_path):
                dirname = os.path.dirname(db_path)
                basename = os.path.basename(db_path)
                tmp = os.path.splitext(basename)
                newfilename = f"{tmp[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{tmp[1]}"
                if ModelSetting.get_bool('base_backup_location_mode'):
                    newpath = os.path.join(dirname, newfilename)
                else:
                    newpath = os.path.join(ModelSetting.get('base_backup_location_manual'), newfilename)
                shutil.copy(db_path, newpath)
                ret = {'ret':'success', 'target':newpath}
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            ret = {'ret':'fail', 'log':str(e)}
        return ret
         
    @staticmethod
    @celery.task()
    def clear(args):
        ret = ToolBaseFile.rmtree2(args[0])
        return Task.get_size(args)



































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
                    if tmp_entity.data['filename']['is_matched'] == False:
                        continue
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
