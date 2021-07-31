# python
import os, sys, traceback, re, json, threading, time, shutil, fnmatch, glob, urllib.parse
from datetime import datetime, timedelta
# third-party
import requests, sqlite3

# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from framework.common.plugin import LogicModuleBase, default_route_socketio
from tool_expand import ToolExpandFileProcess
from tool_base import ToolShutil, d, ToolUtil, ToolBaseFile, ToolOSCommand

from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting


class PlexWebHandle(object):
    
    @classmethod
    def system_agents(cls, url=None, token=None):
        if url is None:
                url = ModelSetting.get('base_plex_url')
        if token is None:
            token = ModelSetting.get('base_token')
        #url = f'{url}/:/prefs?X-Plex-Token={token}'
        url = f'{url}/system/agents?X-Plex-Token={token}'
        logger.warning(url)
        res = requests.get(url, headers={'Accept':'application/json'})
        return res.text
        #logger.warning(res.text)
        #return res.json()
        #return {'ret':'success', 'msg':page.text}


    @classmethod
    def get_sjva_version(cls, url=None, token=None):
        try:
            if url is None:
                url = ModelSetting.get('base_plex_url')
            if token is None:
                token = ModelSetting.get('base_token')
            url = f'{url}/:/plugins/com.plexapp.plugins.SJVA/function/version?X-Plex-Token={token}'
            page = requests.get(url)
            return page.text
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @classmethod
    def get_sjva_agent_version(cls, url, token):
        try:
            if url is None:
                url = ModelSetting.get('base_plex_url')
            if token is None:
                token = ModelSetting.get('base_token')
            url = f'{url}/:/plugins/com.plexapp.agents.sjva_agent/function/version?X-Plex-Token={token}'
            page = requests.get(url)
            return page.text
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    @classmethod
    def refresh(cls, movie_item):
        try:
            url = f"{ModelSetting.get('base_url')}/library/metadata/{movie_item['id']}/refresh?X-Plex-Token={ModelSetting.get('base_token')}"
            ret = requests.put(url)
            logger.warning(ret.request.method)
            logger.warning(ret.text)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @classmethod
    def scan_refresh(cls, library_section_id, folderpath):
        try:
            #http://[PMS_IP_ADDRESS]:32400/library/sections/29/refresh?path=/Users/plexuser/Movies/Media/Movies/1080p&X-Plex-Token=YourTokenGoesHere

            tmp = {'path':folderpath}
            url = f"{ModelSetting.get('base_url')}/library/sections/{library_section_id}/refresh?{urllib.parse.urlencode(tmp)}&X-Plex-Token={ModelSetting.get('base_token')}"
            ret = requests.get(url)
            logger.warning(ret.request.method)
            logger.warning(ret.text)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())