# -*- coding: utf-8 -*-
#from common.decorator import try_except
import traceback
import json
from framework import py_urllib, SystemModelSetting
from framework.wavve.api import session, get_baseparameter, config, logger


def movie_contents_movieid(movie_id):
    """영화 상세 정보"""
    try:
        param = get_baseparameter()
        url = "%s/movie/contents/%s?%s" % (config['base_url'], movie_id, py_urllib.urlencode(param))
        #logger.debug(url)
        response = session.get(url, headers=config['headers'])
        data = response.json()
        if response.status_code == 200:
            return data
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())




 
def movie_contents(page=0, limit=20, genre='all'):
    """영화 전체 목록"""
    #https://apis.pooq.co.kr/cf/movie/contents?WeekDay=all
    # broadcastid=154923
    # came=movie
    # contenttype=movie
    # orderby=viewtime
    # price=all
    # sptheme=svod
    # uiparent=FN0
    # uirank=0
    # uitype=MN85

    try:
        param = get_baseparameter()
        param['targetage'] = 'auto'
        param['genre'] = genre
        param['country'] = 'all'
        param['offset'] = (page-1)*limit
        param['limit'] = limit
        param['orderby'] = 'viewtime'
        url = "%s/movie/contents?%s" % (config['base_url'], py_urllib.urlencode(param))
        #logger.debug(url)
        response = session.get(url, headers=config['headers'])
        data = response.json()
        if response.status_code == 200:
            return data
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())




    