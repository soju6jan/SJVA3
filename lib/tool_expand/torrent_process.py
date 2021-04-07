
# -*- coding: utf-8 -*-
import requests, re, json, time
import traceback, unicodedata
from datetime import datetime
import traceback
import os
import json
import time
import copy

from framework import app, SystemModelSetting, py_urllib
from framework.util import Util
from tool_expand import ToolExpandFileProcess
from framework.logger import get_logger

logger = get_logger('torrent_process')

class TorrentProcess(object):
    @classmethod
    def is_broadcast_member(cls):
        #if SystemModelSetting.get('ddns') == 'https://server.sjva.me':
        #    return True
        if app.config['config']['is_server'] or app.config['config']['is_debug']:
            return True
        return False

    # 토렌트정보 수신 후 
    @classmethod
    def receive_new_data(cls, entity, package_name):
        try:
            if not cls.is_broadcast_member():
                return
            if package_name == 'bot_downloader_ktv':
                cls.append('ktv', entity)
            elif package_name == 'bot_downloader_movie':
                cls.append('movie', entity)
            elif package_name == 'bot_downloader_av':
                cls.append('av', entity)

        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @classmethod
    def append(cls, type, data):
        try:
            import requests
            import json
            response = requests.post("https://sjva.me/sjva/torrent_%s.php" % type, data={'data':json.dumps(data.as_dict())})
            #logger.debug(response.text)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @classmethod
    def server_process(cls, save_list, category=None):
        if cls.is_broadcast_member():
            #logger.debug(category)
            if category == 'KTV':
                cls.server_process_ktv(save_list)
            elif category == 'MOVIE':
                return cls.server_process_movie(save_list)
                
            elif category == 'AV':
                return cls.server_process_av(save_list, 'censored')
            

    # ModelBbs2 인스턴스                        
    @classmethod
    def server_process_ktv(cls, save_list):
        #logger.debug(save_list)

        # Daum정보를 가져온다
        for item in save_list:
            item = item.as_dict()
            if item['torrent_info'] is not None:
                # 하나의 마그넷 단위
                try:
                    for info in item['torrent_info']:
                        # 파이
                        logger.debug('Magnet : %s', info['magnet_uri'])
                        logger.debug('Name : %s', info['name'])
                        info['video_count'] = 0
                        info['files_original'] = copy.deepcopy(info['files'])
                        for f in info['files']:
                            cls.analyse_torrent_info_file(f)
                            if f['type'] == 'video':
                                import ktv
                                entity = ktv.EntityShow(f['filename'], by='only_filename')
                                f['ktv'] = {}
                                f['ktv']['filename_rule'] = entity.filename
                                f['ktv']['name'] = entity.filename_name
                                f['ktv']['date'] = entity.filename_date
                                f['ktv']['number'] = entity.filename_no
                                f['ktv']['quality'] = entity.filename_quality
                                f['ktv']['release'] = entity.filename_release
                                if entity.daum_info is not None:
                                    daum = entity.daum_info.as_dict()
                                    f['daum'] = {
                                        'daum_id' : str(daum['daum_id']),
                                        'poster_url' : daum['poster_url'],
                                        'genre' : daum['genre'],
                                        'title' : daum['title'],
                                    }
                                else:
                                    f['daum'] = None
                                info['video_count'] += 1
                        # 방송
                        if info['video_count'] == 1:
                            ret = {}
                            ret['server_id'] = item['id']
                            ret['broadcast_type'] = 'auto'
                            ret['hash'] = info['info_hash']
                            ret['file_count'] = info['num_files']
                            ret['files'] = info['files_original']
                            ret['total_size'] = info['total_size']
                            ret['video_count'] = info['video_count']
                            for f in info['files']:
                                if f['type'] == 'video':
                                    ret['filename'] = f['filename'] #마그넷인포의 파일명
                                    ret['ktv'] = f['ktv']
                                    ret['daum'] = f['daum']
                            info['broadcast'] = ret

                            telegram = {}
                            telegram['plugin'] = 'bot_downloader_ktv'
                            telegram['sub'] = 'torrent'
                            telegram['data'] = ret
                            
                            text = json.dumps(telegram, indent=2)
                            from framework.common.telegram_bot import TelegramBot
                            TelegramBot.super_send_message(text)
                            time.sleep(0.5)
                            
                        
                        
                except Exception as exception: 
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())        


    @classmethod
    def server_process_movie(cls, save_list):
        from framework.common.torrent.process_movie import ProcessMovie
        lists = []
        for item in save_list:
            item = item.as_dict()
            sub = []
            if item['files']:
                for tmp in item['files']:
                    ext = os.path.splitext(tmp[1])[1].lower()
                    if ext in ['.smi', '.srt', '.ass']:
                        sub.append(tmp)

            if item['torrent_info'] is not None:
                # 하나의 마그넷 단위
                try:
                    for info in item['torrent_info']:

                        fileinfo = cls.get_max_size_fileinfo(info)
                        movie = ProcessMovie.get_info_from_rss(fileinfo['filename'])
                        #logger.debug(fileinfo)
                        #logger.debug(movie)

                        torrent_info = {}
                        torrent_info['name'] = info['name']
                        torrent_info['size'] = info['total_size']
                        torrent_info['num'] = info['num_files']
                        torrent_info['hash'] = info['info_hash']
                        torrent_info['filename'] = fileinfo['filename']
                        torrent_info['dirname'] = fileinfo['dirname']
                        torrent_info['url'] = item['url']

                        movie_info = {}
                        if movie['movie'] is not None:
                            movie_info['title'] = movie['movie']['title']
                            movie_info['target'] = movie['target'].replace('sub_x', 'sub')
                            movie_info['kor'] = movie['is_include_kor']
                            if movie_info['target'] == 'imdb':
                                movie_info['id'] = movie['movie']['id']
                                movie_info['year'] = movie['movie']['year']
                            else:
                                movie_info['daum'] = {}
                                movie_info['id'] = movie['movie']['id']
                                movie_info['daum']['country'] = movie['movie']['country']
                                movie_info['year'] = movie['movie']['year']
                                movie_info['daum']['poster'] = movie['movie']['more']['poster']
                                movie_info['daum']['eng'] = movie['movie']['more']['eng_title']
                                movie_info['daum']['rate'] = movie['movie']['more']['rate']
                                movie_info['daum']['genre'] = movie['movie']['more']['genre']
                        else:
                            movie_info = None
                        ret = {}
                        ret['server_id'] = item['id']
                        if len(sub) > 0 :
                            ret['s'] = sub
                        if movie_info is not None:
                            ret['m'] = movie_info
                        ret['t'] = torrent_info

                        #logger.debug(ret)
                        lists.append(ret)
                        #return ret

                        # 방송
                        telegram = {}
                        telegram['plugin'] = 'bot_downloader_movie'
                        telegram['data'] = ret
                        
                        text = json.dumps(telegram, indent=2)
                        from framework.common.telegram_bot import TelegramBot
                        TelegramBot.super_send_message(text)
                        time.sleep(0.5)
                        #return lists
                except Exception as exception: 
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())     

        return lists

    @classmethod
    def server_process_av(cls, save_list, av_type):
        lists = []
        for item in save_list:
            item = item.as_dict()
            logger.debug(item['title'])
            #av_type = item['board']
            # 2020-05-31 javdb,141jav-NONE, avnori-torrent_ymav, javnet censored_tor
            #av_type = 'censored' if av_type in ['NONE', 'torrent_ymav', 'censored_tor'] else av_type
            #av_type = 'uncensored' if av_type in ['torrent_nmav', 'uncensored_tor'] else av_type
            #av_type = 'western' if av_type in ['torrent_amav', 'white_tor'] else av_type

            #logger.debug(json.dumps(item, indent=4))
            
            if item['torrent_info'] is None:
                from torrent_info import Logic as TorrentInfoLogic
                for m in item['magnet']:
                    logger.debug('Get_torrent_info:%s', m)
                    for i in range(1):
                        tmp = None
                        try:
                            tmp = TorrentInfoLogic.parse_magnet_uri(m, no_cache=True)
                        except:
                            logger.debug('Timeout..')
                        if tmp is not None:
                            break
                    if tmp is not None:
                        if item['torrent_info'] is None:
                            item['torrent_info'] = []
                        item['torrent_info'].append(tmp)



            if item['torrent_info'] is not None:
                # 하나의 마그넷 단위
                try:
                    for info in item['torrent_info']:


                        fileinfo = cls.get_max_size_fileinfo(info)
                        av = cls.server_process_av2(fileinfo['filename'], av_type)
                        #logger.debug(fileinfo)
                        #logger.debug(json.dumps(av, indent=4))

                        #2020-05-31 검색안되는건 그냥 방송안함.
                        if av is None:
                            logger.debug(u'AV 검색 실패')
                            logger.debug(fileinfo['filename'])
                            #logger.debug(av_type)
                            continue
                        
                        if info['num_files'] > 30:
                            continue
                        try:
                            if fileinfo['filename'].lower().find('ch_sd') != -1:
                                continue
                        except: pass
                        torrent_info = {}
                        torrent_info['name'] = info['name']
                        torrent_info['size'] = info['total_size']
                        torrent_info['num'] = info['num_files']
                        torrent_info['hash'] = info['info_hash']
                        torrent_info['filename'] = fileinfo['filename']
                        torrent_info['dirname'] = fileinfo['dirname']
                        torrent_info['url'] = item['url']

                        av_info = None
                        if av is not None:
                            av_info = {}
                            av_info['meta'] = av['type']
                            av_info['code_show'] = av['data']['originaltitle']
                            av_info['title'] = av['data']['title']
                            try:
                                av_info['poster'] = av['data']['thumb'][1]['value']
                            except:
                                try:
                                    av_info['poster'] = av['data']['thumb'][0]['value']
                                except:
                                    av_info['poster'] = None
                            av_info['genre'] = av['data']['genre']
                            if av_info['genre'] is None:
                                av_info['genre'] = []
                            av_info['performer'] = []
                            if av['data']['actor'] is not None:
                                for actor in av['data']['actor']:
                                    av_info['performer'].append(actor['name'])
                            av_info['studio'] = av['data']['studio']
                            av_info['date'] = av['data']['premiered']
                            av_info['trailer'] = ''
                            if av['data']['extras'] is not None and len(av['data']['extras']) > 0:
                                av_info['trailer'] = av['data']['extras'][0]['content_url']
                        else:
                            logger.debug('AV 검색 실패')
                            logger.debug(fileinfo['filename'])
                            #av_info = {}
                            #av_info['title'] = info['name']
                        
                        ret = {'av_type' :av_type}
                        ret['server_id'] = item['id']
                        if av_info is not None:
                            ret['av'] = av_info
                        ret['t'] = torrent_info
                        lists.append(ret)

                        # 방송
                        telegram = {}
                        telegram['plugin'] = 'bot_downloader_av'
                        telegram['data'] = ret
                        
                        text = json.dumps(telegram, indent=2)
                        from framework.common.telegram_bot import TelegramBot
                        TelegramBot.super_send_message(text)
                        time.sleep(0.5)
                        #return lists
                        
                except Exception as exception: 
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())     


                
        return lists




    # torrent_info > files > 하나의 파일 . 
    # path, size 가 있음.
    @classmethod
    def analyse_torrent_info_file(cls, file_info):
        try:
            file_info['dirs'] = os.path.split(file_info['path'])
            file_info['filename'] = os.path.basename(file_info['dirs'][-1])
            file_info['filename_except_ext'], file_info['ext'] = os.path.splitext(file_info['filename'] )
            if file_info['ext'].lower() in ['.mp4', '.mkv', '.avi', '.wmv']:
                file_info['type'] = 'video'
            elif file_info['ext'].lower() in ['.srt', '.smi', '.ass']:
                file_info['type'] = 'sub'
            else:
                file_info['type'] = None
            return file_info
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        

    @classmethod
    def get_max_size_fileinfo(cls, torrent_info):
        try:
            ret = {}
            max_size = -1
            max_filename = None
            for t in torrent_info['files']:
                if t['size'] > max_size:
                    max_size = t['size']
                    max_filename = str(t['path'])
            t = max_filename.split('/')
            ret['filename'] = t[-1]
            if len(t) == 1:
                ret['dirname'] = ''
            elif len(t) == 2:
                ret['dirname'] = t[0]
            else:
                ret['dirname'] = max_filename.replace('/%s' % ret['filename'], '')
            ret['max_size'] = max_size
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    
    
    @classmethod
    def server_process_av2(cls, filename, av_type):
        try:
            logger.debug('filename :%s, av_type:%s', filename, av_type)
            if av_type == 'censored':
                tmp = ToolExpandFileProcess.change_filename_censored(filename)
                logger.debug('TMP1: %s', tmp)
                tmp = ToolExpandFileProcess.remove_extension(tmp)
                logger.debug('TMP2: %s', tmp)
                from metadata import Logic as MetadataLogic
                data = MetadataLogic.get_module('jav_censored').search(tmp, manual=False)
                logger.debug(data)

                if len(data) > 0 and data[0]['score'] > 95:
                    meta_info = MetadataLogic.get_module('jav_censored').info(data[0]['code'])
                    ret = {'type':'dvd', 'data':meta_info}
                else:
                    data = MetadataLogic.get_module('jav_censored_ama').search(tmp, manual=False)
                    process_no_meta = False
                    logger.debug(data)
                    if data is not None and len(data) > 0 and data[0]['score'] > 95:
                        meta_info = MetadataLogic.get_module('jav_censored_ama').info(data[0]['code'])
                        if meta_info is not None:
                            ret = {'type':'ama', 'data':meta_info}
                    #else:
                    #    ret = {'type':'etc', 'data':None}
            else:
                ret = {'type':av_type}
            return ret
        except Exception as exception: 
            logger.error('Exxception:%s', exception)
            logger.error(traceback.format_exc())            