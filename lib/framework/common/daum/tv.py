
# -*- coding: utf-8 -*-
#########################################################
# python
import os
from datetime import datetime
import traceback
import logging
import subprocess
import time
import re
import threading
import json
import requests
import lxml.html
from enum import Enum

from framework import py_urllib
from framework.common.daum import logger


_REGEX_FILENAME = r'^(?P<name>.*?)\.E(?P<no>\d+)(\-E\d{1,4})?\.?(END\.)?(?P<date>\d{6})\.(?P<etc>.*?)(?P<quality>\d+)[p|P](\-?(?P<release>.*?))?(\.(.*?))?$'
_REGEX_FILENAME_NO_EPISODE_NUMBER = r'^(?P<name>.*?)\.(E(?P<no>\d+)\.?)?(END\.)?(?P<date>\d{6})\.(?P<etc>.*?)(?P<quality>\d+)[p|P](\-?(?P<release>.*?))?(\.(.*?))?$'
_REGEX_FILENAME_RENAME = r'(?P<title>.*?)[\s\.]E?(?P<no>\d{1,2})[\-\~\s\.]?E?\d{1,2}'

class DaumTV:

    # 파일명으로 국내 TV 영상이 맞는지 확인한다
    # 맞다면 파트별로 분리
    @staticmethod
    def check_filename(filename):
        logger.debug('check_filename filename : %s', filename)
        try:
            ret = None
            match1 = re.compile(_REGEX_FILENAME).match(filename)
            match2 = re.compile(_REGEX_FILENAME_NO_EPISODE_NUMBER).match(filename)

            for regex in [_REGEX_FILENAME, _REGEX_FILENAME_NO_EPISODE_NUMBER]:
                match = re.compile(regex).match(filename)
                if match:
                    logger.debug('QQQQQQQQQQQ')
                    ret = {}
                    ret['title'] = match1.group('name')
                    ret['no'] = match1.group('no')
                    ret['date'] = match1.group('date')
                    ret['etc'] = match1.group('etc').replace('.', '')
                    ret['quality'] = match1.group('quality')
                    ret['release'] = None
                    if 'release' in match1.groupdict():
                        ret['release'] = match1.group('release')
                    else:
                        ret['release'] = None
                    if ret['no'] is not None and ret['no'] != '': 
                        ret['no'] = int(ret['no'])
                    else: 
                        ret['no'] = -1
                    return DaumTV.change_filename_continous_episode(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @staticmethod 
    def change_filename_continous_episode(ret):
        try:
            if ret['title'].find(u'합') == -1:
                return ret
            match = re.compile(_REGEX_FILENAME_RENAME).match(ret['title'])
            if match:
                logger.debug(u'합본 : %s', ret['filename'])
                ret['title'] = match.group('title').strip()
                # 기존 규칙으로 매칭되어있다면 굳이 바꿀 필요는 없다.
                if ret['no'] == -1:
                    ret['no'] = int(match.group('no'))
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())



    @staticmethod
    def get_html(url):
        try:
            from framework.common.daum import headers, session
            from lib_metadata import SiteUtil
            data = SiteUtil.get_text_daum(url)
            return data

        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_daum_tv_info(search_name, daum_id=None, on_home=False):
        try:
            entity = {}
            #logger.debug('get_daum_tv_info 1 %s', search_name)
            search_name = DaumTV.get_search_name_from_original(search_name)
            #logger.debug('get_daum_tv_info 2 %s', search_name)

            if daum_id is not None:
                url = 'https://search.daum.net/search?w=tv&q=%s&irk=%s&irt=tv-program&DA=TVP' % (py_urllib.quote(search_name.encode('utf8')), daum_id)
            else:
                url = 'https://search.daum.net/search?w=tv&q=%s' % (py_urllib.quote(search_name.encode('utf8')))

            data = DaumTV.get_html(url)
            match = re.compile(r'irk\=(?P<id>\d+)').search(data)
            root = lxml.html.fromstring(data)
            daum_id = match.group('id') if match else ''
            
            entity = {}
            entity['daum_id'] = daum_id
            items = root.xpath('//*[@id="tv_program"]/div[1]/div[2]/strong')
            if not items: 
                return None
            if len(items) == 1:
                entity['title'] = items[0].text.strip()
                entity['title'] = entity['title'] .replace('?', '').replace(':', '')

            entity['status'] = 0
            # 방송종료, 방송예정
            items = root.xpath('//*[@id="tv_program"]/div[1]/div[2]/span')
            if items:
                if items[0].text.strip() == u'방송종료':
                    entity['status'] = 1
                elif items[0].text.strip() == u'방송예정':
                    entity['status'] = 2
            
            items = root.xpath('//*[@id="tv_program"]/div[1]/div[3]/span')
            # 2019-02-25 방송종료시 정보 없어짐
            if items:
                entity['studio'] = items[0].text.strip()
                try: 
                    entity['broadcast_info'] = items[1].text.strip()
                except: 
                    pass
                try: 
                    entity['broadcast_term'] = items[2].text.strip()
                except: 
                    pass
                try:
                    items = root.xpath('//*[@id="tv_program"]/div[1]/div[2]/span')
                except:
                    pass
            else:
                if on_home:
                    logger.debug('on_home : %s', search_name)
                    xml_root = DaumTV.get_show_info_on_home_title(search_name, daum_id=daum_id)
                    home_ret = DaumTV.get_show_info_on_home(xml_root)
                    if home_ret :
                        entity['studio'] = home_ret['studio']
                        entity['broadcast_info'] = home_ret['broadcast_info']
                        entity['broadcast_term'] = home_ret['broadcast_term']
                        #방송예정은 items True가 되어 여기 안온다.

            try:
                match = re.compile(r'(\d{4}\.\d{1,2}\.\d{1,2})~').search(entity['broadcast_term'])
                if match:
                    entity['start_date'] = match.group(1)
            except:
                pass

            items = root.xpath('//*[@id="tv_program"]/div[1]/dl[1]/dd')
            if len(items) == 1:
                entity['genre'] = items[0].text.strip().split(' ')[0]
                entity['genre'] = entity['genre'].split('(')[0].strip()


            items = root.xpath('//*[@id="tv_program"]/div[1]/dl[2]/dd')
            if len(items) == 1:
                entity['summary'] = items[0].text.replace('&nbsp', ' ')

            items = root.xpath('//*[@id="tv_program"]/div[1]/div[1]/a/img')
            if len(items) == 1:
                entity['poster_url'] = 'https:%s' % items[0].attrib['src']

            items = root.xpath('//*[@id="clipDateList"]/li')
            entity['episode_list'] = {}

            if len(items) > 300: 
                items = items[len(items)-300:]
            today = int(datetime.now().strftime('%Y%m%d'))

            for item in items:
                try:
                    a_tag = item.xpath('a') 
                    if len(a_tag) == 1:
                        span_tag = a_tag[0].xpath('span[@class="txt_episode"]')
                        if len(span_tag) == 1:
                            if item.attrib['data-clip'] in entity['episode_list']:
                                #같은날짜 같은회차가 두번나올때가 있다. 버그로 보임
                                #EBS 초대석, 2010912 28회
                                if entity['episode_list'][item.attrib['data-clip']][0] == span_tag[0].text.strip().replace(u'회', ''):
                                    pass
                                else:
                                    # 에피소드 넘버가 1차이가 날때만, 마지막꺼와
                                    idx = len(entity['episode_list'][item.attrib['data-clip']]) - 1
                                    _ = abs(int(entity['episode_list'][item.attrib['data-clip']][idx]) - int(span_tag[0].text.strip().replace(u'회', '')))
                                    #2019-06-24
                                    #슬플때사랑한다, 21, 22 순서 
                                    if _ <= 4:
                                        if item.attrib['data-clip'] != '' and today >= int(item.attrib['data-clip']):
                                            entity['last_episode_date'] = item.attrib['data-clip']
                                            entity['last_episode_no'] = span_tag[0].text.strip().replace(u'회', '')
                                        entity['episode_list'][item.attrib['data-clip']].append(span_tag[0].text.strip().replace(u'회', ''))
                                    else:
                                        pass
                                    # Daum에 뜬금없는 에피소드가 끼어져있다
                                    # 무시
                                        
                            else:
                                if item.attrib['data-clip'] != '' and today >= int(item.attrib['data-clip']):
                                    entity['last_episode_date'] = item.attrib['data-clip']
                                    entity['last_episode_no'] = span_tag[0].text.strip().replace(u'회', '')
                                entity['episode_list'][item.attrib['data-clip']] = [span_tag[0].text.strip().replace(u'회', '')]
                except Exception as exception: 
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())
            #전체 에피소드 갯수 : len(items)
            #에피소드 dict 갯수  len(entity.episode_list)  
            #정확히 반이면 1일 2회 방송, 1/4이면 1일 4회 방송
            
            # 2019-06-24
            #if len(entity.episode_list) != 0 and len(items) % len(entity.episode_list) == 0:
            #    entity.episode_count_one_day = len(items) / len(entity.episode_list)
            try:
                if len(entity['episode_list']):
                    entity['episode_count_one_day'] = int(round(float(len(items)) / len(entity['episode_list'])))
                    if entity['episode_count_one_day'] == 0:
                        entity['episode_count_one_day'] = 1
                else:
                    entity['episode_count_one_day'] = 1
            except:
                entity['episode_count_one_day'] = 1

            #entity['episode_list_json'] = json.dumps(entity['episode_list'])
            #entity['episode_list_json'] = entity['episode_list']
            #logger.debug(entity['episode_list_json'])
            #entity.save()
            logger.debug('daum tv len(entity.episode_list) : %s %s %s', len(items), len(entity['episode_list']), entity['episode_count_one_day'])
            #logger.debug(entity.episode_list)
            #logger.debug(items)
            return entity  
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    

    @staticmethod
    def get_search_name_from_original(search_name):
        search_name = search_name.replace('일일연속극', '').strip()
        search_name = search_name.replace('특별기획드라마', '').strip()
        search_name = re.sub(r'\[.*?\]', '', search_name).strip()
        # 2020-10-10
        channel_list = ['채널 A', '채널A']
        for tmp in channel_list:
            if search_name.startswith(tmp):
                search_name = search_name.replace(tmp, '').strip()
        search_name = re.sub(r'^.{2,3}드라마', '', search_name).strip()
        #2019-08-01
        search_name = re.sub(r'^.{1,3}특집', '', search_name).strip()
        return search_name


    @staticmethod
    def get_show_info(title, no=None, date=None):
        try:
            # Home
            title = DaumTV.get_search_name_from_original(title)
            url = 'https://search.daum.net/search?q=%s' % (py_urllib.quote(title.encode('utf8')))
            data = DaumTV.get_html(url)
            root = lxml.html.fromstring(data)
            home_info = DaumTV.get_show_info_on_home(root)
            tv = DaumTV.get_daum_tv_info(title)
            ret = {'home':home_info, 'tv':tv}
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @staticmethod
    def get_show_info_on_home(root):
        try:
            tags = root.xpath('//*[@id="tvpColl"]/div[2]/div/div[1]/span/a')
            # 2019-05-13
            #일밤- 미스터리 음악쇼 복면가왕 A 태그 2개
            if len(tags) < 1:
                return
            tag_index = len(tags)-1
            entity = {}
            entity['title'] = tags[tag_index].text
            logger.debug('22222get_show_info_on_home title: %s', entity['title'])
            match = re.compile(r'q\=(?P<title>.*?)&').search(tags[tag_index].attrib['href'])
            if match:
                entity['title'] = py_urllib.unquote(match.group('title'))
            entity['id'] = re.compile(r'irk\=(?P<id>\d+)').search(tags[tag_index].attrib['href']).group('id')

            entity['status'] = 1  
            tags = root.xpath('//*[@id="tvpColl"]/div[2]/div/div[1]/span/span')
            if len(tags) == 1:
                if tags[0].text == u'방송종료':
                    entity['status'] = 2
                elif tags[0].text == u'방송예정':
                    entity['status'] = 0
            logger.debug('get_show_info_on_home status: %s', entity['status'])
            tags = root.xpath('//*[@id="tvpColl"]/div[2]/div/div[1]/div')
            entity['extra_info'] = tags[0].text_content().strip()
            logger.debug('get_show_info_on_home extra_info: %s', entity['extra_info'])

            entity['studio'] = ''
            tags = root.xpath('//*[@id="tvpColl"]/div[2]/div/div[1]/div/a')
            if len(tags) == 1:
                entity['studio'] = tags[0].text
            else:
                tags = root.xpath('//*[@id="tvpColl"]/div[2]/div/div[1]/div/span[1]')
                if len(tags) == 1:
                    entity['studio'] = tags[0].text
            logger.debug('get_show_info_on_home studio: %s', entity['studio'])

            tags = root.xpath('//*[@id="tvpColl"]/div[2]/div/div[1]/div/span')
            entity['extra_info_array'] = [tag.text for tag in tags]
            entity['broadcast_info'] = entity['extra_info_array'][-2].strip()
            entity['broadcast_term'] = entity['extra_info_array'][-1].split(',')[-1].strip()
            entity['year'] = re.compile(r'(?P<year>\d{4})').search(entity['extra_info_array'][-1]).group('year')
            logger.debug('get_show_info_on_home 1: %s', entity['status'])
            #시리즈
            entity['series'] = []
            entity['series'].append({'title':entity['title'], 'id' : entity['id'], 'year' : entity['year']})
            tags = root.xpath('//*[@id="tv_series"]/div/ul/li')

            if tags:
                # 2019-03-05 시리즈 더보기 존재시
                try:
                    more = root.xpath('//*[@id="tv_series"]/div/div/a')
                    url = more[0].attrib['href']
                    if not url.startswith('http'):
                        url = 'https://search.daum.net/search%s' % url
                    logger.debug('MORE URL : %s', url)
                    if more[0].xpath('span')[0].text == u'시리즈 더보기':
                        more_root = HTML.ElementFromURL(url)
                        tags = more_root.xpath('//*[@id="series"]/ul/li')
                except Exception as exception:
                    logger.debug('Not More!')
                    logger.debug(traceback.format_exc())

                for tag in tags:
                    dic = {}
                    dic['title'] = tag.xpath('a')[0].text
                    dic['id'] = re.compile(r'irk\=(?P<id>\d+)').search(tag.xpath('a')[0].attrib['href']).group('id')
                    if tag.xpath('span'):
                        dic['date'] = tag.xpath('span')[0].text
                        dic['year'] = re.compile(r'(?P<year>\d{4})').search(dic['date']).group('year')
                    else:
                        dic['year'] = None
                    entity['series'].append(dic)
                entity['series'] = sorted(entity['series'] , key=lambda k: int(k['id'])) 
            logger.debug('SERIES : %s', len(entity['series']))
            #동명
            entity['equal_name'] = []
            tags = root.xpath(u'//div[@id="tv_program"]//dt[contains(text(),"동명 콘텐츠")]//following-sibling::dd')
            if tags:
                tags = tags[0].xpath('*')
                for tag in tags:
                    if tag.tag == 'a':
                        dic = {}
                        dic['title'] = tag.text
                        dic['id'] = re.compile(r'irk\=(?P<id>\d+)').search(tag.attrib['href']).group('id')
                    elif tag.tag == 'span':
                        match = re.compile(r'\((?P<studio>.*?),\s*(?P<year>\d{4})?\)').search(tag.text)
                        if match:
                            dic['studio'] = match.group('studio')
                            dic['year'] = match.group('year')
                        elif tag.text == u'(동명프로그램)':
                            entity['equal_name'].append(dic)
                        elif tag.text == u'(동명회차)':
                            continue
            logger.debug(entity)
            return entity
        except Exception as exception:
            logger.debug('Exception get_show_info_by_html : %s', exception)
            logger.debug(traceback.format_exc())


    ##########################
    # PLEX
    @staticmethod
    def get_show_info_on_home_title(title, daum_id=None):
        try:
            title = title.replace(u'[종영]', '')
            if daum_id is None:
                url = 'https://search.daum.net/search?q=%s' % (py_urllib.quote(title.encode('utf8')))
            else:
                url = 'https://search.daum.net/search?q=%s&irk=%s&irt=tv-program&DA=TVP' % (py_urllib.quote(title.encode('utf8')), daum_id)

            return DaumTV.get_lxml_by_url(url)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def get_lxml_by_url(url):
        try:
            from lib_metadata import SiteUtil
            return SiteUtil.get_tree_daum(url)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())