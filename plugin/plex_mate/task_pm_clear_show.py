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
from tool_expand import EntityKtv, ToolExpandDiscord

from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting
from .logic_pm_base import LogicPMBase
from .plex_db import PlexDBHandle, dict_factory

from .task_pm_clear_movie import TAG, Task as TaskMovie
from .plex_web import PlexWebHandle


class Task(object):

    @staticmethod
    @celery.task(bind=True)
    def start(self, command, section_id, dryrun):
        config = LogicPMBase.load_config()
        dryrun = True if dryrun == 'true'  else False

        db_file = ModelSetting.get('base_path_db')
        con = sqlite3.connect(db_file)
        cur = con.cursor()
        #ce = con.execute('SELECT * FROM metadata_items WHERE metadata_type = 1 AND library_section_id = ? ORDER BY title', (section_id,))
        #ce = con.execute('SELECT * FROM metadata_items WHERE metadata_type = 1 AND library_section_id = ? AND user_thumb_url NOT LIKE "upload%" AND (user_thumb_url NOT LIKE "http%" OR refreshed_at is NULL) ORDER BY title', (section_id,))
        query = config.get('파일정리 TV 쿼리', 'SELECT * FROM metadata_items WHERE metadata_type = 2 AND library_section_id = ? ORDER BY title')            
        ce = con.execute(query, (section_id,))
        ce.row_factory = dict_factory
        fetch = ce.fetchall()
        status = {'is_working':'run', 'total_size':0, 'remove_size':0, 'count':len(fetch), 'current':0}

        for show in fetch:
            try:
                if ModelSetting.get_bool('clear_show_task_stop_flag'):
                    return 'stop'
                time.sleep(0.05)
                status['current'] += 1
                data = {'mode':'show', 'status':status, 'command':command, 'section_id':section_id, 'dryrun':dryrun, 'process':{}, 'file_count':0, 'remove_count':0}
                data['db'] = show

                Task.show_process(data, con, cur)
            
                data['status']['total_size'] += data['meta']['total']
                data['status']['remove_size'] += data['meta']['remove']
                if 'media' in data:
                    data['status']['total_size'] += data['media']['total']
                    data['status']['remove_size'] += data['media']['remove']
                #P.logic.get_module('clear').receive_from_task(data, celery=False)
                #continue
                if 'use_filepath' in data:
                    del data['use_filepath']
                if 'remove_filepath' in data:
                    del data['remove_filepath']
                if 'seasons' in data:
                    del data['seasons']
                if app.config['config']['use_celery']:
                    self.update_state(state='PROGRESS', meta=data)
                else:
                    self.receive_from_task(data, celery=False)
            except Exception as e:
                logger.error(f'Exception:{str(e)}')
                logger.error(traceback.format_exc())
                logger.error(show['title'])
        logger.warning(f"종료")
        return 'wait'




    @staticmethod
    def show_process(data, con, cur):

        data['meta'] = {'remove':0}
        data['meta']['metapath'] = os.path.join(ModelSetting.get('base_path_metadata'), 'TV Shows', data['db']['hash'][0], f"{data['db']['hash'][1:]}.bundle")

        data['meta']['total'] = ToolBaseFile.size(start_path=data['meta']['metapath'])
        if data['command'] == 'start0':
            return
        combined_xmlpath = os.path.join(data['meta']['metapath'], 'Contents', '_combined', 'Info.xml')
        if os.path.exists(combined_xmlpath) == False:
            return 
        data['use_filepath'] = []
        data['remove_filepath'] = []
        data['seasons'] = {}
        data['media'] = {'total':0, 'remove':0}
        ret = Task.xml_analysis(combined_xmlpath, data, data)
        if ret == False:
            logger.warning(f"{data['db']['title']} 쇼 분석 실패")
            return
        
        season_cs = con.execute('SELECT * FROM metadata_items WHERE metadata_type = 3 and parent_id = ? ORDER BY "index"', (data['db']['id'],))
        season_cs.row_factory = dict_factory
        for season in season_cs.fetchall():
            episode_cs = con.execute('SELECT * FROM metadata_items WHERE metadata_type = 4 and parent_id = ? ORDER BY "index"', (season['id'],))
            episode_cs.row_factory = dict_factory

            for episode in episode_cs.fetchall():
                season_index = season['index']
                episode_index = episode['index']
                if episode['index'] == -1:
                    if episode['available_at'] is not None:
                        episode_index = episode['available_at'].split(' ')[0]
                    else:
                        episode_index = episode['originally_available_at'].split(' ')[0]
                    #season_index = episode_index.split('-')[0]
                if season_index not in data['seasons']:
                    data['seasons'][season_index] = {'db':season}
                    combined_xmlpath = os.path.join(data['meta']['metapath'], 'Contents', '_combined', 'seasons', f"{season_index}.xml")
                    ret = Task.xml_analysis(combined_xmlpath, data['seasons'][season_index], data)
                    if ret == False:
                        logger.warning(combined_xmlpath)
                        logger.warning(f"{data['db']['title']} 시즌 분석 실패 : season_index - {season_index}")
                        #logger.warning(combined_xmlpath)
                        #return
                    data['seasons'][season_index]['episodes'] = {}
                data['seasons'][season_index]['episodes'][episode_index] = {'db':episode}
                combined_xmlpath = os.path.join(data['meta']['metapath'], 'Contents', '_combined', 'seasons', f"{season_index}", "episodes", f"{episode_index}.xml")
                ret = Task.xml_analysis(combined_xmlpath, data['seasons'][season_index]['episodes'][episode_index], data, is_episode=True)
                if ret == False:
                    logger.warning(combined_xmlpath)
                    #logger.warning(d(episode))
                    logger.warning(f"{data['db']['title']} 에피소드 분석 실패")
                    #del data['seasons'][season_index]['episodes'][episode_index]
                    #return
        
        #logger.warning(d(data['use_filepath']))
        #logger.warning(d(data))

        query = ""

        if data['command'] in ['start22', 'start3', 'start4']:
            # 쇼 http로 
            sql = 'UPDATE metadata_items SET '
            if data['process']['poster']['url'] != '':
                sql += ' user_thumb_url = "{}", '.format(data['process']['poster']['url'])
                try: data['use_filepath'].remove(data['process']['poster']['localpath'])
                except: pass
                try: data['use_filepath'].remove(data['process']['poster']['realpath'])
                except: pass
            if data['process']['art']['url'] != '':
                sql += ' user_art_url = "{}", '.format(data['process']['art']['url'])
                try: data['use_filepath'].remove(data['process']['art']['localpath'])
                except: pass
                try: data['use_filepath'].remove(data['process']['art']['realpath'])
                except: pass
            if data['process']['banner']['url'] != '':
                sql += ' user_banner_url = "{}", '.format(data['process']['banner']['url'])
                try: data['use_filepath'].remove(data['process']['banner']['localpath'])
                except: pass
                try: data['use_filepath'].remove(data['process']['banner']['realpath'])
                except: pass
            if data['process']['theme']['url'] != '':
                sql += ' user_music_url = "{}", '.format(data['process']['theme']['url'])
                
            if sql != 'UPDATE metadata_items SET ':
                sql = sql.strip().rstrip(',')
                sql += '  WHERE id = {} ;\n'.format(data['db']['id'])
                query += sql

            for season_index, season in data['seasons'].items():
                if 'process' not in season:
                    continue
                sql = 'UPDATE metadata_items SET '
                if season['process']['poster']['url'] != '':
                    sql += ' user_thumb_url = "{}", '.format(season['process']['poster']['url'])
                    try: data['use_filepath'].remove(season['process']['poster']['localpath'])
                    except: pass
                    try: data['use_filepath'].remove(season['process']['poster']['realpath'])
                    except: pass
                if season['process']['art']['url'] != '':
                    sql += ' user_art_url = "{}", '.format(season['process']['art']['url'])
                    try: data['use_filepath'].remove(season['process']['art']['localpath'])
                    except: pass
                    try: data['use_filepath'].remove(season['process']['art']['realpath'])
                    except: pass
                if season['process']['banner']['url'] != '':
                    sql += ' user_banner_url = "{}", '.format(season['process']['banner']['url'])
                    try: data['use_filepath'].remove(season['process']['banner']['localpath'])
                    except: pass
                    try: data['use_filepath'].remove(season['process']['banner']['realpath'])
                    except: pass
                if sql != 'UPDATE metadata_items SET ':
                    sql = sql.strip().rstrip(',')
                    sql += '  WHERE id = {} ;\n'.format(season['db']['id'])
                    query += sql

        
        if data['command'] in ['start21', 'start22', 'start3', 'start4']:
            
            for season_index, season in data['seasons'].items():
                for episode_index, episode in season['episodes'].items():
                    #logger.warning(episode['process']['thumb'])
                    media_item_cs = con.execute('SELECT * FROM media_items WHERE metadata_item_id = ? ORDER BY id', (episode['db']['id'],))
                    media_item_cs.row_factory = dict_factory
                    episode['media_list'] = []

                    for media_item in media_item_cs.fetchall():
                        media_part_cs = con.execute('SELECT * FROM media_parts WHERE media_item_id = ? ORDER BY id', (media_item['id'],))
                        media_part_cs.row_factory = dict_factory
                        for media_part in media_part_cs.fetchall():
                            media_hash = media_part['hash']
                            #logger.warning(f"  파일 : {media_part['file']} {media_hash}")
                            mediapath = os.path.join(ModelSetting.get('base_path_media'), 'localhost', media_hash[0], f"{media_hash[1:]}.bundle", 'Contents', 'Thumbnails', 'thumb1.jpg')
                            if os.path.exists(mediapath):
                                #logger.warning("미디오 썸네일 있음")
                                episode['media_list'].append(mediapath)
                                data['media']['total'] = os.path.getsize(mediapath)
                                #data['remove_size'] += os.stat(mediapath).st_size
                                #os.remove(mediapath)
                                #media://0/10c056239442666d0931c90996ff69673861d95.bundle/Contents/Thumbnails/thumb1.jpg
                    # 2021-11-01
                    # 4단계 미디어파일을 디코에 올리고 그 url로 대체한다.
                    # 
                    if data['command'] == 'start4' and episode['process']['thumb']['db_type'] == 'media':
                        localpath = os.path.join(ModelSetting.get('base_path_media'), 'localhost', episode['process']['thumb']['db'].replace('media://', ''))
                        if localpath[0] != '/':
                            localpath = localpath.replace('/', '\\')
                        if os.path.exists(localpath):
                            if data['dryrun'] == False:
                                discord_url = ToolExpandDiscord.discord_proxy_image_localfile(localpath)
                                if discord_url is not None:
                                    episode['process']['thumb']['url'] = discord_url
                                    logger.warning(discord_url)
                        else:
                            #logger.warning(episode)
                            logger.warning(f"썸네일 없음 1: {episode['db']['id']}")
                            PlexWebHandle.analyze_by_id(episode['db']['id'])
                    if data['command'] == 'start4' and episode['process']['thumb']['db'] == '':
                        logger.warning(f"썸네일 없음 분석 2: {episode['db']['id']}")
                        PlexWebHandle.analyze_by_id(episode['db']['id'])



                    if episode['process']['thumb']['url'] != '':
                        query += f'UPDATE metadata_items SET user_thumb_url = "{episode["process"]["thumb"]["url"]}" WHERE id = {episode["db"]["id"]};\n'
                        try: data['use_filepath'].remove(episode['process']['thumb']['localpath'])
                        except: pass
                        try: data['use_filepath'].remove(episode['process']['thumb']['realpath'])
                        except: pass
                        if data['command'] in ['start3', 'start4']:
                            for mediafilepath in episode['media_list']:
                                if os.path.exists(mediapath):
                                    data['media']['remove'] += os.path.getsize(mediapath)
                                    if data['dryrun'] == False:
                                        os.remove(mediapath)
                    elif episode['process']['thumb']['db'] == '':
                        if len(episode['media_list']) > 0:
                            tmp = f"media://{episode['media_list'][0].split('localhost/')[1]}"
                            query += f'UPDATE metadata_items SET user_thumb_url = "{tmp}" WHERE id = {episode["db"]["id"]};\n'

                    
                    if data['dryrun'] == False and data['command'] in ['start3', 'start4']:
                        for mediafilepath in episode['media_list']:
                            content_folder = os.path.dirname(os.path.dirname(mediafilepath))
                            for base, folders, files in os.walk(content_folder):
                                if not folders and not files:
                                    os.removedirs(base)


        #logger.error(data['command'])
        #logger.error(query)
        if query != '' and data['dryrun'] == False:
            PlexDBHandle.execute_query(query)


        #logger.error(data['meta']['remove'] )
        for base, folders, files in os.walk(data['meta']['metapath']):
            for f in files:
                data['file_count'] += 1
                filepath = os.path.join(base, f)
                #if filepath.find('themes') == -1:
                #    continue
                if filepath not in data['use_filepath']:
                    if os.path.exists(filepath):
                        data['remove_count'] += 1
                        if filepath not in data['remove_filepath']:
                            data['remove_filepath'].append(filepath)
                        if os.path.islink(filepath) == False:
                            data['meta']['remove'] += os.path.getsize(filepath)
                        #logger.error(filepath)
                        if data['dryrun'] == False:
                            os.remove(filepath)

        for base, folders, files in os.walk(data['meta']['metapath']):
            if not folders and not files:
                os.removedirs(base)


        

        if data['command'] == 'start1':
            return                  


                        
          


    @staticmethod
    def xml_analysis(combined_xmlpath, data, show_data, is_episode=False):
        #logger.warning(combined_xmlpath)
        import xml.etree.ElementTree as ET
        #text = ToolBaseFile.read(combined_xmlpath)
        #logger.warning(text)
        # 2021-12-11 4단계로 media파일을 디코 이미로 대체할때 시즌0 같이 아예 0.xml 파일이 없을 때도 동작하도록 추가
        
        if is_episode:
            data['process'] = {}
            data['process']['thumb'] = {
                'db' : data['db'][f'user_thumb_url'],
                'db_type' : data['db'][f'user_thumb_url'].split('://')[0],
                'url' : '',
                'filename' : '',
            }
        if os.path.exists(combined_xmlpath) == False:
            logger.info(f"xml 파일 없음 : {combined_xmlpath}")
            #logger.error(data['process']['thumb'])
            logger.debug(data)
            logger.debug(is_episode)
            return False
        if combined_xmlpath not in show_data['use_filepath']:
            show_data['use_filepath'].append(combined_xmlpath)
            
        tree = ET.parse(combined_xmlpath)
        root = tree.getroot()
        data['xml_info'] = {}
        if is_episode == False:
            tags = TAG
        else:
            tags = {'thumb' : ['thumb', 'thumbs']}

        for tag, value in tags.items():
            tmp = root.find(value[1])
            if root.find(value[1]) is None:
                continue
            data['xml_info'][value[1]] = []
            for item in root.find(value[1]).findall('item'):
                entity = {}
                if 'url' not in item.attrib:
                    continue
                entity['url'] = item.attrib['url']
                if 'preview' in item.attrib:
                    entity['filename'] = item.attrib['preview']
                elif 'media' in item.attrib:
                    entity['filename'] = item.attrib['media']
                entity['provider'] = item.attrib['provider']
                data['xml_info'][value[1]].append(entity)

        if 'process' not in data:
            data['process'] = {}
        for tag, value in tags.items():
            if value[1] in data['xml_info']:
                data['process'][tag] = {
                    'db' : data['db'][f'user_{value[0]}_url'],
                    'db_type' : '', 
                    'url' : '',
                    'filename' : '',
                }

        for tag, value in tags.items():
            if value[1] in data['xml_info']:
                if data['process'][tag]['db'] != '':
                    #logger.error(data['process'][tag]['db'])
                    data['process'][tag]['db_type'] = data['process'][tag]['db'].split('://')[0]
                    if data['process'][tag]['db_type'] != 'metadata':
                        #logger.warning(combined_xmlpath)
                        #logger.warning(data['process'][tag]['db_type'])
                        continue
                    
                    data['process'][tag]['filename'] = data['process'][tag]['db'].split('/')[-1]
                    # db에 현재 선택되어 있는 이미지파일에 맞는 url을 가져온다
                    for item in data['xml_info'][value[1]]:
                        if data['process'][tag]['filename'] == item['filename']:
                            data['process'][tag]['url'] = item['url']
                            tmp = combined_xmlpath.split('/_combined/')
                            tmp2 = data['process'][tag]['db'].split('metadata://')
                            filepath = f"{tmp[0]}/_combined/{tmp2[1]}"
                            if os.path.exists(filepath):
                                data['process'][tag]['localpath'] = filepath
                                if filepath not in show_data['use_filepath']:
                                    show_data['use_filepath'].append(filepath)
                                
                                if os.path.islink(filepath):
                                    data['process'][tag]['islink'] = True
                                    data['process'][tag]['realpath'] = os.path.realpath(filepath)
                                    if data['process'][tag]['realpath'] not in show_data['use_filepath']:
                                        show_data['use_filepath'].append(data['process'][tag]['realpath'])
                                else:
                                    data['process'][tag]['islink'] = False
 
                            break
                        
        return True