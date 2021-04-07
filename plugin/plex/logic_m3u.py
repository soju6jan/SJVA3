# -*- coding: utf-8 -*-
#########################################################
# python
import os
from datetime import datetime, timedelta
import traceback
import logging
import subprocess
import time
import re
import threading
import json
import requests
import urllib

# third-party
from sqlalchemy import desc
from sqlalchemy import or_, and_, func, not_
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from plexapi.exceptions import BadRequest
from plexapi.library import ShowSection
from lxml import etree as ET
import lxml

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, path_app_root, socketio, py_urllib2
from framework.job import Job
from framework.util import Util
from system.logic import SystemLogic

# 로그
from .plugin import logger, package_name
from .model import ModelSetting


#########################################################

class LogicM3U(object):
    #EXTM3U #EXTINF:-1 tvg-id="41" tvg-name="가이드채널" tvg-chno="1" tvg-logo="" group-title="",가이드채널 http://192.168.0.691:5004/auto/ch261000000-773.mpeg 

    channel_index = 1

    @staticmethod
    def make_m3u():
        try:
            from .logic import Logic
            server_url = ModelSetting.get('server_url')
            server_token = ModelSetting.get('server_token')
            if Logic.server is None:
                Logic.server = PlexServer(server_url, server_token)

            json_info = json.loads(ModelSetting.get('tivimate_json'))
            data = "#EXTM3U\n"

            root = ET.Element('tv')
            root.set('generator-info-name', "plex")
            LogicM3U.channel_index = 1
            for info in json_info:
                if info['type'] == 'recent_add':
                    if info['section'] == 'episode':
                        url = '%s/hubs/home/recentlyAdded?type=2&X-Plex-Token=%s' % (server_url, server_token)
                        channel_title = u'최신TV'
                    elif info['section'] == 'movie':
                        url = '%s/hubs/home/recentlyAdded?type=1&X-Plex-Token=%s' % (server_url, server_token)
                        channel_title = u'최신영화'
                    else:
                        url = '%s/library/sections/%s/recentlyAdded?X-Plex-Token=%s' % (server_url, info['section'], server_token)
                        channel_title = u''
                    logger.debug(url)

                    doc = lxml.html.parse(py_urllib2.urlopen(url))
                    videos = doc.xpath("//video")
                    if channel_title == '':
                        channel_title = doc.xpath("//mediacontainer")[0].attrib['librarysectiontitle']

                    data, root = LogicM3U.make_list(data, root, videos, info, channel_title)
                elif info['type'] == 'show':
                    # 
                    url = '%s/library/metadata/%s/children?X-Plex-Token=%s' % (server_url, info['metadata'], server_token)
                    logger.debug(url)
                    doc = lxml.html.parse(py_urllib2.urlopen(url))
                    seasons = doc.xpath("//directory")
                    logger.debug(seasons)
                    
                    if seasons:
                        channel_title = doc.xpath("//mediacontainer")[0].attrib['title2']
                        include_parent = True if len(seasons) > 1 else False
                        for s in seasons:
                            logger.debug(s.attrib)
                            if 'ratingkey' in s.attrib:
                                logger.debug(s.attrib['ratingkey'])

                                url = '%s/library/metadata/%s/children?X-Plex-Token=%s' % (server_url, s.attrib['ratingkey'], server_token)
                                doc2 = lxml.html.parse(py_urllib2.urlopen(url))
                                videos = doc2.xpath("//video")
                                
                                data, root = LogicM3U.make_list(data, root, videos, info, channel_title, include_parent=include_parent)
                    else:
                        channel_title = '%s %s' % (doc.xpath("//mediacontainer")[0].attrib['title1'], doc.xpath("//mediacontainer")[0].attrib['title2'])
                        videos = doc.xpath("//video")
                        data, root = LogicM3U.make_list(data, root, videos, info, channel_title,include_parent=True)
            tree = ET.ElementTree(root)
            ret = ET.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8")

            return data, ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())  


    @staticmethod
    def make_list(data, root, videos, info, channel_title, include_parent=False):
        server_url = ModelSetting.get('server_url')
        server_token = ModelSetting.get('server_token')
        current_count = 0
        for tag_video in videos:
            
            channel_tag = None
            program_tag = None
            try:
                tmp = tag_video.xpath('.//media')
                if tmp:
                    tag_media = tmp[0]
                else:
                    logger.debug('continue1')
                    continue
                tag_part = tag_media.xpath('.//part')[0]
                if 'duration' not in tag_media.attrib:
                    logger.debug('continue3')
                    continue

                if tag_video.attrib['type'] == 'movie':
                    title = tag_video.attrib['title']
                elif tag_video.attrib['type'] == 'episode':
                    #logger.debug(tag_video.attrib)
                    if 'index' in tag_video.attrib:
                        title = u'%s %s (%s회)' % (tag_video.attrib['grandparenttitle'], (tag_video.attrib['parenttitle'] if include_parent else ''), tag_video.attrib['index'])
                    else:
                        title = u'%s %s (%s)' % (tag_video.attrib['grandparenttitle'], (tag_video.attrib['parenttitle'] if include_parent else ''),tag_video.attrib['title'])
                elif tag_video.attrib['type'] == 'clip':
                    title = u'%s' % tag_video.attrib['title']
                title = title.replace('  ', ' ')
                
                duration = int(tag_media.attrib['duration'])
                video_url = '%s%s?X-Plex-Token=%s&dummy=/series/' % (server_url, tag_part.attrib['key'], server_token)
                #video_url = '%s%s' % (server_url, tag_part.attrib['key'])
                icon_url = '%s%s?X-Plex-Token=%s' % (server_url, tag_video.attrib['thumb'], server_token)
                tmp = '#EXTINF:-1 tvg-id="{channel_number}" tvg-name="{channel_title}" tvh-chno="{channel_number}" tvg-logo="{logo}" group-title="{channel_title}",{title}\n{url}\n'
                
                data += tmp.format(channel_title=channel_title, channel_number=LogicM3U.channel_index, logo=icon_url, url=video_url, title=title)
                #data.append(video_url)
                ############################
                channel_tag = ET.SubElement(root, 'channel') 
                channel_tag.set('id', str(LogicM3U.channel_index))
                channel_tag.set('repeat-programs', 'true')

                display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                display_name_tag.text = '%s(%s)' % (channel_title, LogicM3U.channel_index)
                display_name_tag = ET.SubElement(channel_tag, 'display-number') 
                display_name_tag.text = str(LogicM3U.channel_index)
                
                #datetime_start = datetime(2019,1,1) + timedelta(hours=-9)
                #datetime_start = datetime.now() + timedelta(hours=+9)
                datetime_start = datetime.now()
                for i in range(3):
                    datetime_stop = datetime_start + timedelta(seconds=duration/1000+1)
                    program_tag = ET.SubElement(root, 'programme')
                    program_tag.set('start', datetime_start.strftime('%Y%m%d%H%M%S') + ' +0900')
                    program_tag.set('stop', datetime_stop.strftime('%Y%m%d%H%M%S') + ' +0900')
                    program_tag.set('channel', str(LogicM3U.channel_index))
                    datetime_start = datetime_stop

                    #program_tag.set('video-src', video_url)
                    #program_tag.set('video-type', 'HTTP_PROGRESSIVE')
                    
                    title_tag = ET.SubElement(program_tag, 'title')
                    title_tag.set('lang', 'ko')
                    title_tag.text = title

                    
                    icon_tag = ET.SubElement(program_tag, 'icon')
                    icon_tag.set('src', icon_url)
                    if 'summary' in tag_video.attrib:
                        desc_tag = ET.SubElement(program_tag, 'desc')
                        desc_tag.set('lang', 'ko')
                        desc_tag.text = tag_video.attrib['summary']
                channel_tag = None
                program_tag = None
                LogicM3U.channel_index += 1
                current_count += 1
                if 'count' in info and current_count > info['count']:
                    break
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
                if channel_tag is not None:
                    root.remove(channel_tag)
                if program_tag is not None:
                    root.remove(channel_tag)
        return data, root