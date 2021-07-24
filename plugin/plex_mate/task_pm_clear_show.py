# python
import os, sys, traceback, re, json, threading, time, shutil, fnmatch, glob, platform
from datetime import datetime, timedelta
# third-party
import requests, sqlite3, yaml

# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from plugin import LogicModuleBase, default_route_socketio
from tool_expand import ToolExpandFileProcess
from tool_base import ToolShutil, d, ToolUtil, ToolBaseFile, ToolOSCommand, ToolSubprocess
from tool_expand import EntityKtv

from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting
from .logic_pm_base import LogicPMBase
from .plex_db import PlexDBHandle, dict_factory


# tag : db에서는 구분 값 / xml info - 폴더명
TAG = {
    'poster' : ['thumb', 'posters'],
    'art' : ['art', 'art'],
    'banner' : ['banner', 'banners']
}


class Task(object):

    @staticmethod
    @celery.task(bind=True)
    def start(self, command, section_id, dryrun):
        config = LogicPMBase.load_config()
        logger.warning(command)
        logger.warning(section_id)
        dryrun = True if dryrun == 'true'  else False
        logger.warning(dryrun)


        db_file = ModelSetting.get('base_path_db')
        con = sqlite3.connect(db_file)
        cur = con.cursor()
        #ce = con.execute('SELECT * FROM metadata_items WHERE metadata_type = 1 AND library_section_id = ? ORDER BY title', (section_id,))
        #ce = con.execute('SELECT * FROM metadata_items WHERE metadata_type = 1 AND library_section_id = ? AND user_thumb_url NOT LIKE "upload%" AND (user_thumb_url NOT LIKE "http%" OR refreshed_at is NULL) ORDER BY title', (section_id,))
        ce = con.execute(config['TV 쿼리'], (section_id,))
        ce.row_factory = dict_factory
        fetch = ce.fetchall()
        status = {'is_working':'run', 'total_size':0, 'remove_size':0, 'count':len(fetch), 'current':0}
        for show in fetch:
            if ModelSetting.get_bool('clear_show_task_stop_flag'):
                return 'stop'
            time.sleep(0.05)
            status['current'] += 1
            data = {'mode':'show', 'status':status, 'command':command, 'section_id':section_id, 'dryrun':dryrun, 'process':{}}
            data['db'] = show
            #logger.warning(movie['title'])
            
            hash_value = show['hash']
            metapath = os.path.join(ModelSetting.get('base_path_metadata'), 'TV Shows', data['db']['hash'][0], f"{data['db']['hash'][1:]}.bundle")
            data['meta'] = {}
            data['meta']['total'] = ToolBaseFile.size(start_path=metapath)
            data['meta']['remove'] = 0

            season_cs = con.execute('SELECT * FROM metadata_items WHERE metadata_type = 3 and parent_id = ? ORDER BY "index"', (show['id'],))
            season_cs.row_factory = dict_factory

            for season in season_cs.fetchall():
                data['season'] = season
                #logger.warning(season['guid'])
                #logger.warning(season['id'])
                
                #episode_cs = conn.execute('SELECT * FROM metadata_items WHERE metadata_type = 4 and parent_id = ? AND user_thumb_url NOT LIKE "http%" ORDER BY "index"', (season['id'],))
                episode_cs = con.execute('SELECT * FROM metadata_items WHERE metadata_type = 4 and parent_id = ? ORDER BY "index"', (season['id'],))
                episode_cs.row_factory = dict_factory

                for episode in episode_cs.fetchall():
                    
                    #if episode['user_thumb_url'].startswith('metadata') == False:
                    #    #logger.error('1111111111111111111111111111111111111111')
                    #    #return
                    #    continue

                    #logger.warning("메타 썸네일임")
                    season_index = season['index']
                    episode_index = episode['index']

                    if episode['index'] == -1:
                        episode_index = episode['available_at'].split(' ')[0]
                        season_index = episode_index.split('-')[0]

                    combined_xmlpath = os.path.join(metapath, 'Contents', '_combined', 'seasons', f"{season_index}", "episodes", f"{episode_index}.xml")

                    episode_data = {'db':episode}
                    Task.xml_analysis(combined_xmlpath, episode_data)
                    episode_data['process'] = {}
                    for tag, value in TAG.items():
                        episode_data['process'][tag] = {
                            'db' : episode_data['db'][f'user_{value[0]}_url'],
                            'db_type' : '', 
                            'url' : '',
                            'filename' : '',
                        }

                    for tag, value in TAG.items():
                        if episode_data['process'][tag]['db'] != '':
                            episode_data['process'][tag]['db_type'] = episode_data['process'][tag]['db'].split('//')[0]
                            episode_data['process'][tag]['filename'] = episode_data['process'][tag]['db'].split('/')[-1]
                            for item in episode_data['info'][value[1]]:
                                if episode_data['process'][tag]['filename'] == item['filename']:
                                    episode_data['process'][tag]['url'] = item['url']
                                    break

                    #logger.warning(d(episode_data))
                    continue
                    c_metapath = os.path.join(metapath, 'Contents')
                    for f in os.listdir(c_metapath):
                        _path = os.path.join(c_metapath, f)
                        # 윈도우는 combined에 바로 데이터가 있어서 무조건 삭제?
                        if f == '_stored':
                            tmp = ToolBaseFile.size(start_path=_path)
                            data['meta']['stored'] = tmp
                            if platform.system() == 'Windows':
                                data['meta']['remove'] += tmp
                                if data['dryrun'] == False:
                                    ToolBaseFile.rmtree(_path)
                        elif f == '_combined':
                            for tag, value in TAG.items():
                                tag_path = os.path.join(_path, value[1])
                                #logger.warning(tag_path)
                                if os.path.exists(tag_path) == False:
                                    continue
                                for img_file in os.listdir(tag_path):
                                    img_path = os.path.join(tag_path, img_file)
                                    if os.path.islink(img_path):
                                        if os.path.realpath(img_path).find('_stored') == -1:
                                            # 저장된 파일에 대한 링크가 아니기 삭제
                                            if data['dryrun'] == False and os.path.exists(img_path) == True:
                                                os.remove(img_path)
                                    else: #윈도우
                                        if img_file != data['process'][tag]['filename']:
                                            # 저장파일이 아니기 때문에 삭제
                                            data['meta']['remove'] += os.path.getsize(img_path)
                                            if data['dryrun'] == False and os.path.exists(img_path) == True:
                                                os.remove(img_path)
                            
                        else:
                            tmp = ToolBaseFile.size(start_path=_path)
                            data['meta']['remove'] += tmp
                            data['meta']['agents'] += tmp
                            if data['dryrun'] == False:
                                ToolBaseFile.rmtree(_path)

                    for thumb in data['episode_thumbs']:
                        #logger.warning(d(thumb))
                        stored_path1 = os.path.join(metapath, 'Contents', '_stored', 'seasons', f"{season_index}", "episodes", f"{episode_index}", "thumbs", thumb['filename'])
                        if os.path.exists(stored_path1):
                            #logger.warning(f"파일있음1 : {stored_path1}")
                            data['remove_size'] += os.stat(stored_path1).st_size
                            data['remove_1'] += 1
                            if is_dry == False:
                                os.remove(stored_path1)

                        stored_path2 = os.path.join(metapath, 'Contents', thumb['provider'], 'seasons', f"{season_index}", "episodes", f"{episode_index}", "thumbs", thumb['filename'].replace(f"{thumb['provider']}_", ''))
                        if os.path.exists(stored_path2):
                            #logger.warning(f"파일있음2 : {stored_path2}")
                            data['remove_size'] += os.stat(stored_path2).st_size
                            data['remove_2'] += 1
                            if is_dry == False:
                                os.remove(stored_path2)

                    """
                    sql = 'UPDATE metadata_items SET user_thumb_url = ? WHERE id = ?' 
                    conn.execute(sql, (data['episode_thumbs'][0]['url'], episode['id']))
                    """
                    if len(data['episode_thumbs']) > 0:
                        sql = 'UPDATE metadata_items SET user_thumb_url = "{}" WHERE id = {} ;'.format(data['episode_thumbs'][0]['url'], episode['id']) 
                        #.replace('/', '\/')
                        #logger.error(sql)
                        sql_filepath = os.path.join(path_data, 'tmp', f"{episode['id']}.sql")
                        ToolBaseFile.write(sql, sql_filepath)
                        #logger.warning([SQLITE, DB, sql_filepath])
                        if is_dry == False:
                            ret = ToolSubprocess.execute_command_return([SQLITE, DB, f".read {sql_filepath}"])
                            logger.warning(ret)



            data['status']['total_size'] += data['meta']['total']
            data['status']['remove_size'] += data['meta']['remove']
            if 'media' in data:
                data['status']['total_size'] += data['media']['total']
                data['status']['remove_size'] += data['media']['remove']
            #P.logic.get_module('clear').receive_from_task(data, celery=False)
            #continue
            if app.config['config']['use_celery']:
                self.update_state(state='PROGRESS', meta=data)
            else:
                self.receive_from_task(data, celery=False)
        logger.warning(f"종료")
        return 'wait'


        

    @staticmethod
    def xml_analysis(combined_xmlpath, data):
        import xml.etree.ElementTree as ET
        #text = ToolBaseFile.read(combined_xmlpath)
        #logger.warning(text)
        tree = ET.parse(combined_xmlpath)
        root = tree.getroot()
        data['info'] = {}
        data['info']['posters'] = []
        for tag in ['posters', 'art', 'banners']:
            data['info'][tag] = []
            if root.find(tag) is None:
                continue

            for item in root.find(tag).findall('item'):
                entity = {}
                if 'url' not in item.attrib:
                    continue
                entity['url'] = item.attrib['url']
                if 'preview' in item.attrib:
                    entity['filename'] = item.attrib['preview']
                elif 'media' in item.attrib:
                    entity['filename'] = item.attrib['media']
                entity['provider'] = item.attrib['provider']
                data['info'][tag].append(entity)
