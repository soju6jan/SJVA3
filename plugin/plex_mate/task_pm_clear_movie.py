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
        ce = con.execute(config['영화 쿼리'], (section_id,))
        ce.row_factory = dict_factory
        fetch = ce.fetchall()
        status = {'is_working':'run', 'total_size':0, 'remove_size':0, 'count':len(fetch), 'current':0}
        for movie in fetch:
            if ModelSetting.get_bool('clear_movie_task_stop_flag'):
                return 'stop'
            time.sleep(0.05)
            status['current'] += 1
            data = {'mode':'movie', 'status':status, 'command':command, 'section_id':section_id, 'dryrun':dryrun, 'process':{}}
            data['db'] = movie
            #logger.warning(movie['title'])

            
            Task.analysis(data, con, cur)
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
    def analysis(data, con, cur):
        #logger.warning(f"분석시작 : {data['db']['title']}")

        

        data['meta'] = {'remove':0, 'agents' : 0}
        data['meta']['metapath'] = os.path.join(ModelSetting.get('base_path_metadata'), 'Movies', data['db']['hash'][0], f"{data['db']['hash'][1:]}.bundle")
        data['meta']['total'] = ToolBaseFile.size(start_path=data['meta']['metapath'])

        combined_xmlpath = os.path.join(data['meta']['metapath'], 'Contents', '_combined', 'Info.xml')
        if os.path.exists(combined_xmlpath) == False:
            return
        Task.xml_analysis(combined_xmlpath, data)

        #logger.warning(data['db']['user_thumb_url'])
        #logger.warning(data['info']['posters'])
        data['process'] = {}
        for tag, value in TAG.items():
            data['process'][tag] = {
                'db' : data['db'][f'user_{value[0]}_url'],
                'db_type' : '', 
                'url' : '',
                'filename' : '',
            }


        # DB에 저장값과 일치한 로컬파일을 찾음. 상황별로 삭제 제외하기 위해
        # 2단계 적용을 위한 로컬파일에 해당하는 URL을 구함
        for tag, value in TAG.items():
            if data['process'][tag]['db'] != '':
                data['process'][tag]['db_type'] = data['process'][tag]['db'].split('//')[0]
                data['process'][tag]['filename'] = data['process'][tag]['db'].split('/')[-1]
                for item in data['info'][value[1]]:
                    if data['process'][tag]['filename'] == item['filename']:
                        data['process'][tag]['url'] = item['url']
                        break


        #logger.error(d(data['process']))

        # 1단계.
        # _combined 에서 ..stored 
        c_metapath = os.path.join(data['meta']['metapath'], 'Contents')
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
                                # 먼저 에이전트 폴더들이 삭제될 수 있음.
                                if data['dryrun'] == False:# and os.path.exists(img_path) == True:
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

        if data['command'] == 'start1':
            return
        
        # 2단계 TAG별 URL 로 세팅하고 xml 파일만 남기고 제거
        if data['dryrun'] == False:
            #sql = 'UPDATE metadata_items SET user_thumb_url = "{}", user_art_url = "{}", user_banner_url = "{}" WHERE id = {} ;'.format(
            #    data['process']['poster']['url'],
            #   data['process']['art']['url'],
            #    data['process']['banner']['url'],
            #    data['db']['id']
            #)
            sql = 'UPDATE metadata_items SET '
            if data['process']['poster']['url'] != '':
                sql += ' user_thumb_url = "{}", '.format(data['process']['poster']['url'])
            if data['process']['art']['url'] != '':
                sql += ' user_art_url = "{}", '.format(data['process']['art']['url'])
            if data['process']['banner']['url'] != '':
                sql += ' user_banner_url = "{}", '.format(data['process']['banner']['url'])
            if sql != 'UPDATE metadata_items SET ':
                sql = sql.strip().rstrip(',')
                sql += '  WHERE id = {} ;'.format(data['db']['id'])
                sql_filepath = os.path.join(path_data, 'tmp', f"movie_{data['db']['id']}.sql")
                PlexDBHandle.execute_query(sql, sql_filepath=sql_filepath)
                
        for f in os.listdir(c_metapath):
            _path = os.path.join(c_metapath, f)
            if f == '_combined':
                for tag, value in TAG.items():
                    tag_path = os.path.join(_path, value[1])
                    if os.path.exists(tag_path):
                        if data['dryrun'] == False:
                            data['meta']['remove'] += ToolBaseFile.size(start_path=tag_path)
                            ToolBaseFile.rmtree(tag_path)
                        
                tmp = os.path.join(_path, 'extras')
                if os.path.exists(tmp) and len(os.listdir(tmp)) == 0:
                    if data['dryrun'] == False:
                        ToolBaseFile.rmtree(tmp)
                tmp = os.path.join(_path, 'extras.xml')
                if os.path.exists(tmp):
                    if os.path.exists(tmp):
                        data['meta']['remove'] += os.path.getsize(tmp)
                        if data['dryrun'] == False:
                            os.remove(tmp)
            else:
                tmp = ToolBaseFile.size(start_path=_path)
                if data['dryrun'] == False:
                    data['meta']['remove'] += tmp
                    ToolBaseFile.rmtree(_path)
                else:
                    if f == '_stored':
                        data['meta']['remove'] += tmp

        if data['command'] == 'start2':
            return

        

        media_ce = con.execute('SELECT user_thumb_url, user_art_url, media_parts.file, media_parts.hash FROM metadata_items, media_items, media_parts WHERE metadata_items.id = media_items.metadata_item_id AND media_items.id = media_parts.media_item_id AND metadata_items.id = ?;', (data['db']['id'],))
        media_ce.row_factory = dict_factory
        data['media'] = {'total':0, 'remove':0}

        for item in media_ce.fetchall():
            logger.warning(d(item))
            if item['hash'] == '':
                continue
            mediapath = os.path.join(ModelSetting.get('base_path_media'), 'localhost', item['hash'][0], f"{item['hash'][1:]}.bundle")
            data['media']['total'] += ToolBaseFile.size(start_path=mediapath)
            if item['user_thumb_url'].startswith('media') == False:
                img = os.path.join(mediapath, 'Contents', 'Thumbnails', 'thumb1.jpg')
                if os.path.exists(img):
                    data['media']['remove'] += os.path.getsize(img)
                    if data['dryrun'] == False:
                        os.remove(img)
            if item['user_art_url'].startswith('media') == False:
                img = os.path.join(mediapath, 'Contents', 'Art', 'art1.jpg')
                if os.path.exists(img):
                    data['media']['remove'] += os.path.getsize(img)
                    if data['dryrun'] == False:
                        os.remove(img)

        

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
