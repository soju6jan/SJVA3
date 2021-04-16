# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import time
import shutil
import re

# third-party
import requests

# sjva 공용
from framework import app, db, scheduler, path_app_root, celery, py_urllib
from framework.job import Job
from framework.util import Util

try:
    import plexapi
except ImportError:
    os.system("{} install plexapi".format(app.config['config']['pip']))
    import plexapi  

from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from plexapi.exceptions import BadRequest
from plexapi.library import ShowSection

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting
#########################################################


class LogicNormal(object):
    server_instance = None
    
    # 2020-06-18
    # 파일을 받아서 파일이 속한 메타키를 넘긴다.
    

    # 경로로만 section_id를 얻는다. 실제로 라이브러리에 있는지는 모른다.
    

    @staticmethod
    def get_section_id_by_filepath(filepath):
        try:
            if LogicNormal.server_instance is None:
                LogicNormal.server_instance = PlexServer(ModelSetting.get('server_url'), ModelSetting.get('server_token'))
            if LogicNormal.server_instance is None:
                return

            sections = LogicNormal.server_instance.library.sections()
            # 가장 긴 경로를 리턴
            tmp_len = 0
            tmp_section_id = -1
            for section in sections:
                for location in section.locations:
                    if filepath.find(location) != -1:
                        if len(location) > tmp_len:
                            tmp_len = len(location)
                            tmp_section_id = section.key
            logger.debug('PLEX get_section_id_by_filepath %s:%s', tmp_section_id, filepath)
            return tmp_section_id
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())  
        return -1

    # SJVA.bundle를 사용하여 라이브러리에 있는지 확인한다.
    @staticmethod
    def is_exist_in_library_using_bundle(filepath):
        try:
            url = '%s/:/plugins/com.plexapp.plugins.SJVA/function/count_in_library?filename=%s&X-Plex-Token=%s' % (ModelSetting.get('server_url'), py_urllib.quote(filepath.encode('utf8')), ModelSetting.get('server_token'))
            data = requests.get(url).text
            if data == '0':
                return False
            else:
                try:
                    tmp = int(data)
                    if tmp > 0:
                        return True
                except:
                    return False
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False

    @staticmethod
    def get_library_key_using_bundle(filepath, section_id=-1):
        try:
            url = '%s/:/plugins/com.plexapp.plugins.SJVA/function/db_handle?action=get_metadata_id_by_filepath&args=%s&X-Plex-Token=%s' % (ModelSetting.get('server_url'), py_urllib.quote(filepath.encode('utf8')), ModelSetting.get('server_token'))
            data = requests.get(url).text
            return data
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    # 메타 아이디로 파일목록을 받는다. 한편에 여러 파일이 있는경우 순서대로 출력한다.
    @staticmethod
    def get_filepath_list_by_metadata_id_using_bundle(metadata_id):
        try:
            url = '%s/:/plugins/com.plexapp.plugins.SJVA/function/db_handle?action=get_filepath_list_by_metadata_id&args=%s&X-Plex-Token=%s' % (ModelSetting.get('server_url'), metadata_id, ModelSetting.get('server_token'))
            data = requests.get(url).text
            ret = [x.strip() for x in data.split('\n')]
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    

    @staticmethod
    def metadata_refresh(filepath=None, metadata_id=None):
        try:
            if metadata_id is None:
                if filepath is not None:
                    metadata_id = LogicNormal.get_library_key_using_bundle(filepath)
            if metadata_id is None:
                return False   
            url = '%s/library/metadata/%s/refresh?X-Plex-Token=%s'  % (ModelSetting.get('server_url'), metadata_id, ModelSetting.get('server_token'))
            data = requests.put(url).text
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        return False
    
    @staticmethod
    def os_path_exists(filepath):
        try:
            url = '%s/:/plugins/com.plexapp.plugins.SJVA/function/os_path_exists?filepath=%s&X-Plex-Token=%s' % (ModelSetting.get('server_url'), py_urllib.quote(filepath.encode('utf8')), ModelSetting.get('server_token'))
            data = requests.get(url).text
            return (data=='True')
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        return False
    
    @staticmethod
    def find_by_filename_part(keyword):
        try:
            query = "SELECT metadata_items.id, media_items.id, file, media_items.duration, media_items.bitrate, media_parts.created_at, media_items.size, media_items.width, media_items.height, media_items.video_codec, media_items.audio_codec FROM media_parts, media_items, metadata_items WHERE media_parts.media_item_id = media_items.id and media_items.metadata_item_id = metadata_items.id and LOWER(media_parts.file) LIKE '%{keyword}%' and media_items.width > 0 ORDER BY media_items.bitrate DESC".format(keyword=keyword)

            url = '%s/:/plugins/com.plexapp.plugins.SJVA/function/db_query?query=%s&X-Plex-Token=%s' % (ModelSetting.get('server_url'), py_urllib.quote(query.encode('utf8')), ModelSetting.get('server_token'))
            data1 = requests.get(url).json()

            query = "SELECT metadata_items.id, media_items.id, file, media_streams.url FROM media_parts, media_items, metadata_items, media_streams WHERE media_streams.media_item_id = media_items.id and media_parts.media_item_id = media_items.id and media_items.metadata_item_id = metadata_items.id and media_streams.stream_type_id = 3 and media_parts.file LIKE '%{keyword}%' ORDER BY media_items.bitrate DESC".format(keyword=keyword)

            url = '%s/:/plugins/com.plexapp.plugins.SJVA/function/db_query?query=%s&X-Plex-Token=%s' % (ModelSetting.get('server_url'), py_urllib.quote(query.encode('utf8')), ModelSetting.get('server_token'))
            data2 = requests.get(url).json()
            
            #logger.debug(data2)

            #logger.debug(data1)

            ret = {'ret' : True}
            ret['list'] = []
            ret['metadata_id'] = []
            for tmp in data1['data']:
                if tmp == '':
                    continue
                tmp = tmp.split('|')
                item = {}
                item['metadata_id'] = '/library/metadata/%s' % tmp[0]
                item['media_id'] = tmp[1]
                item['filepath'] = tmp[2]
                item['filename'] = tmp[2]
                lastindex = 0
                if tmp[2][0] == '/':
                    lastindex = tmp[2].rfind('/')
                else:
                    lastindex = tmp[2].rfind('\\')
                item['dir'] = tmp[2][:lastindex]
                item['filename'] = tmp[2][lastindex+1:]

                item['duration'] = int(tmp[3])
                item['bitrate'] = int(tmp[4])
                item['created_at'] = tmp[5]
                item['size'] = int(tmp[6])
                item['size_str'] = Util.sizeof_fmt(item['size'], suffix='B')
                item['width'] = int(tmp[7])
                item['height'] = int(tmp[8])
                item['video_codec'] = tmp[9]
                item['audio_codec'] = tmp[10]
                ret['list'].append(item)
                if item['metadata_id'] not in ret['metadata_id']:
                    ret['metadata_id'].append(item['metadata_id'])
            
            for tmp in data2['data']:
                if tmp == '':
                    continue
                tmp = tmp.split('|')
                for item in ret['list']:
                    if item['media_id'] == tmp[1] and item['filepath'] == tmp[2]:
                        item['sub'] = tmp[3]
                        break
            logger.debug(ret)
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        return None


    @staticmethod
    def execute_query(query):
        try:
            url = '{server}/:/plugins/com.plexapp.plugins.SJVA/function/db_query?query={query}&X-Plex-Token={token}'.format(server=ModelSetting.get('server_url'), query=query, token=ModelSetting.get('server_token'))
            return requests.get(url).json()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        return False

