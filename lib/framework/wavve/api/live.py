# -*- coding: utf-8 -*-
#from common.decorator import try_except
import sys, traceback
import json
from framework import py_urllib, py_urllib2
from framework.wavve.api import session, get_baseparameter, config, logger
from framework.util import Util


def live_all_channels(genre='all'):
    try:
        param = get_baseparameter()
        param['genre'] = genre
        param['type'] = 'all'
        param['offset'] = 0
        param['limit'] = 999
        url = "%s/live/all-channels?%s" % (config['base_url'], py_urllib.urlencode(param))
        response = session.get(url, headers=config['headers'])
        data = response.json()
        #logger.debug(url)
        #logger.debug(data)
        if response.status_code == 200:
            return data
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())    


def live_epgs_channels(channel_id, startdatetime, enddatetime):
    try:
        param = get_baseparameter()
        param['genre'] = 'all'
        param['type'] = 'all'
        param['offset'] = 0
        param['limit'] = 999
        param['startdatetime'] = startdatetime
        param['enddatetime'] = enddatetime
        param['orderby'] = 'old'
        url = "%s/live/epgs/channels/%s?%s" % (config['base_url'], channel_id, py_urllib.urlencode(param))
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



def get_live_quality_list(source_id):
    try:
        url = 'https://wapie.pooq.co.kr/v1/lives30/%s' % source_id
        params = DEFAULT_PARAM.copy()
        params['credential'] = 'none'
        url = '%s?%s' % (url, py_urllib.urlencode(params))
        request = py_urllib2.Request(url)
        response = py_urllib2.urlopen(request)
        if sys.version_info[0] == 2:
            data = json.load(response, encoding='utf8')
        else:
            data = json.load(response)
        result = data['result']['qualityList'][0]['quality']
        return result
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def get_quality_to_pooq(quality):
    if quality == 'FHD':
        return '5000'
    elif quality == 'HD':
        return '2000'
    elif quality == 'SD':
        return '1000'
    return '5000'




