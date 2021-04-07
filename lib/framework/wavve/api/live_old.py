# -*- coding: utf-8 -*-
#from common.decorator import try_except
import sys, traceback
import json
from framework import py_urllib, py_urllib2
from framework.wavve.api import session, get_baseparameter, config, logger


DEFAULT_PARAM = {'deviceTypeId':'pc', 'marketTypeId':'generic', 'apiAccessCredential':'EEBE901F80B3A4C4E5322D58110BE95C', 'drm':'WC', 'country':'KOR'}

def get_live_list():
    try:
        url = 'https://wapie.pooq.co.kr/v1/livesgenresort30/'
        params = DEFAULT_PARAM.copy()
        params['credential'] = 'none'
        params['orderby'] = 'g'
        url = '%s?%s' % (url, py_urllib.urlencode(params))
        #logger.debug('get_live_list:%s', url)
        request = py_urllib2.Request(url)
        response = py_urllib2.urlopen(request)
        if sys.version_info[0] == 2:
            data = json.load(response, encoding='utf8')
        else:
            data = json.load(response)
        return data['result']['list']
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())    


def get_live_json(source_id, quality, credential):
    try:
        quality = get_quality_to_pooq(quality)
        quality_list = get_live_quality_list(source_id)
        if not quality in quality_list: 
            quality = quality_list[0]
        url = 'https://wapie.pooq.co.kr/v1/lives30/%s/url' % source_id
        params = DEFAULT_PARAM.copy()
        params['deviceModelId'] = 'Macintosh'
        params['authType'] = 'cookie'
        params['guid'] = get_guid()
        params['lastPlayId'] = 'none'
        params['quality'] = quality
        params['credential'] = credential
        
        url = '%s?%s' % (url, py_urllib.urlencode(params))
        request = py_urllib2.Request(url)
        response = py_urllib2.urlopen(request)
        if sys.version_info[0] == 2:
            data = json.load(response, encoding='utf8')
        else:
            data = json.load(response)
        return data

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


def get_guid():
    import hashlib
    m = hashlib.md5()

    def GenerateID( media ):
        from datetime import datetime
        requesttime = datetime.now().strftime('%Y%m%d%H%M%S')
        randomstr = GenerateRandomString(5)
        uuid = randomstr + media + requesttime
        return uuid

    def GenerateRandomString( num ):
        from random import randint
        rstr = ""
        for i in range(0,num):
            s = str(randint(1,5))
            rstr += s
        return rstr
    uuid = GenerateID("POOQ")
    m.update(uuid)
    return str(m.hexdigest())