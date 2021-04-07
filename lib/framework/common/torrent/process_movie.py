# -*- coding: utf-8 -*-
import traceback
import os
import json
import time
import copy
import re

from guessit import guessit


from framework.common.torrent import logger
from framework.common.daum import MovieSearch
from system.model import ModelSetting as SystemModelSetting


class ProcessMovie(object):
    @staticmethod
    def get_info_from_rss(f):
        try:
            logger.debug('INFO: [%s]', f)
            item = {}
            item['flag_move'] = False
            item['name'] = f
            item['guessit'] = guessit(f)
            if 'language' in item['guessit']:
                item['guessit']['language'] = ''
            if 'screen_size' not in item['guessit']:
                item['guessit']['screen_size'] = '--'
            if 'source' not in item['guessit']:
                item['guessit']['source'] = '--'
            item['search_name'] = None
            item['movie'] = None
            match = re.compile(r'^(?P<name>.*?)[\s\.\[\_\(]\d{4}').match(item['name'])
            if match:
                item['search_name'] = match.group('name').replace('.', ' ').strip()
                item['search_name'] = re.sub(r'\[(.*?)\]', '', item['search_name'] )
            else:
                return
            if 'year' in item['guessit']:
                item['is_include_kor'], movie = MovieSearch.search_movie(item['search_name'], item['guessit']['year'])
                if movie and movie[0]['score'] == 100:
                    item['movie'] = movie[0]
                    if item['movie']['country'].startswith(u'한국'):
                        if item['is_include_kor']:
                            # VOD 가능성 높음
                            item['target'] = 'kor_vod'
                        else:
                            # 외국 파일일 가능성 높음...
                            item['target'] = 'kor'
                    else:
                        if item['is_include_kor']:
                            # VOD 가능성 높음
                            item['target'] = 'vod'
                        elif item['name'].lower().find('.kor') != -1:
                            #item['target'] = 'kor'
                            # 한국어 자막일 가능성 높음
                            item['target'] = 'vod'
                        else:
                            # 외국 파일일 가능성 높음...
                            item['target'] = 'sub_x'
                    item['flag_move'] = True
                else:
                    logger.debug('NO META!!!!!!!!!!')
                    if item['is_include_kor'] == False:
                        logger.debug('imdb search %s %s ', item['search_name'].lower(), item['guessit']['year'])
                        movie = MovieSearch.search_imdb(item['search_name'].lower(), item['guessit']['year'])
                        if movie is not None:
                            logger.debug('IMDB TITLE:[%s][%s]', movie['title'], movie['year'])
                            item['movie'] = movie
                            item['target'] = 'imdb'
                            item['flag_move'] = True
            item['guessit'] = ''
            return item
        except Exception as exception: 
            logger.error('Exxception:%s', exception)
            logger.error(traceback.format_exc())