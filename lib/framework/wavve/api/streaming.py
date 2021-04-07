# -*- coding: utf-8 -*-
#from common.decorator import try_except
import traceback
import json
from framework.wavve.api import session, logger, get_baseparameter, config
from framework import py_urllib, SystemModelSetting

def get_guid():
    try:
        tmp = SystemModelSetting.get('wavve_guid')
        if tmp != '':
            return tmp
    except:
        pass
    
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


def get_proxies():
    proxy = get_proxy()
    if proxy is not None:
        return {"https": proxy, 'http':proxy}

# for ffmpeg
def get_proxy():
    if SystemModelSetting.get_bool('site_wavve_use_proxy'):
        return SystemModelSetting.get('site_wavve_proxy_url')


# 02-28 isabr y > n 이었음. proxy 필요없음
 
def streaming(contenttype, contentid, quality, action='hls', ishevc='y', isabr='y', return_url=False):
    """재생관련 정보 (스트리밍 / 다운로드 url 발급)"""
    # contenttype : live, vod, movie, clip, timemachine, onairvod
    # contentid  : live = channelid, 프로그램 = programid, vod = contentid, 영화 = movieid, 클립 = clipid
    # action : hls, dash, progressive, download
    # quality : 100p (라디오), 360p, 480p, 720p, 1080p, 2160p, default, radio   
    # authtype  : signed url = url, http header 인증 = cookie
    # isabr - adaptive streaming 여부 : y, n
    # ishevc - hevc 여부 : y, n
    if quality == 'FHD':
        quality = '1080p'
    elif quality == 'HD':
        quality = '720p'
    elif quality == 'SD':
        quality = '480p'
    elif quality == 'UHD':
        quality = '2160p'
    #quality = '2160p'
    if contenttype == 'live' :
        ishevc = 'n'
        isabr = 'n'

    try:
        param = get_baseparameter()
        param['credential'] = SystemModelSetting.get('site_wavve_credential')
        if contenttype == 'general':
            contenttype = 'vod'

        elif contenttype == 'onair':
            contenttype = 'onairvod'
        param['contenttype'] = contenttype
        param['contentid'] = contentid
        param['action'] = action
        param['quality'] = quality
        #param['guid'] = get_guid()
        param['guid'] = ''
        param['deviceModelId'] = 'Windows 10'
        param['authtype'] = 'url' #cookie, url
        #if contenttype == 'vod':
        #    isabr = 'y'
        param['isabr'] = isabr
        param['ishevc'] = ishevc
        param['lastplayid'] = 'none'

        url = "%s/streaming?%s" % (config['base_url'], py_urllib.urlencode(param))
        if return_url:
            logger.debug(url)
            return url
        response = session.get(url, headers=config['headers'], proxies=get_proxies())
        data = response.json()

        if response.status_code == 200:
            logger.debug(url)
            logger.debug(data)
            try:
                if data['playurl'].startswith('https://event.pca.wavve.com'):
                    logger.debug('playurl startswith https://event.pca.wavve.com!!!!!')
                    return streaming_imsi(contenttype, contentid, quality, action=action, ishevc=ishevc, isabr=isabr)
            except:
                logger.debug('https://event.pca.wavve.com error')

            return data
        else:
            if 'resultcode' in data:
                #logger.debug(data['resultmessage'])
                pass
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


# https://event.pca.wavve.com
def streaming_imsi(contenttype, contentid, quality, action='hls', ishevc='y', isabr='y'):
    """재생관련 정보 (스트리밍 / 다운로드 url 발급)"""
    # contenttype : live, vod, movie, clip, timemachine, onairvod
    # contentid  : live = channelid, 프로그램 = programid, vod = contentid, 영화 = movieid, 클립 = clipid
    # action : hls, dash, progressive, download
    # quality : 100p (라디오), 360p, 480p, 720p, 1080p, 2160p, default, radio   
    # authtype  : signed url = url, http header 인증 = cookie
    # isabr - adaptive streaming 여부 : y, n
    # ishevc - hevc 여부 : y, n
    if quality == 'FHD':
        quality = '1080p'
    elif quality == 'HD':
        quality = '720p'
    elif quality == 'SD':
        quality = '480p'
    elif quality == 'UHD':
        quality = '2160p'
    #quality = '2160p'
    if contenttype == 'live' :
        ishevc = 'n'
        isabr = 'n'

    try:
        param = get_baseparameter()
        param['credential'] = SystemModelSetting.get('site_wavve_credential')
        if contenttype == 'general':
            contenttype = 'vod'

        elif contenttype == 'onair':
            contenttype = 'onairvod'
        param['contenttype'] = contenttype
        param['contentid'] = contentid
        param['action'] = action
        param['quality'] = quality
        #param['guid'] = get_guid()
        param['guid'] = ''
        #param['deviceModelId'] = 'Windows 10'
        param['authtype'] = 'url' #cookie, url
        #if contenttype == 'vod':
        #    isabr = 'y'
        param['isabr'] = isabr
        param['ishevc'] = ishevc
        param['lastplayid'] = 'none'

        param['device'] = 'smarttv'

        url = "%s/streaming?%s" % (config['base_url'], py_urllib.urlencode(param))
        response = session.get(url, headers=config['headers'])
        data = response.json()

        if response.status_code == 200:
            #logger.debug(data)
            logger.debug(data['playurl'])
            return data
        else:
            if 'resultcode' in data:
                #logger.debug(data['resultmessage'])
                pass
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())



# 2020-03-06
# isabr=y 필수 조건에서 adaptive 형식의 m3u8을 리턴함. 
# ffmpeg에 이 URL을 넣어줘도 되지만, 명시적으로 가장 나중의 것을 넣어주도록 한다.
# 이전단계에서 선택한 화질의 비트레이트가 가장 마지막에 위치하고, 그 이하 화질이 위에 위치

def get_prefer_url(url):
    try:
        response = session.get(url, headers=config['headers'])
        data = response.text.strip()

        last_url = None
        last_quality = 0
        for t in data.split('\n'):
            if t.strip().find('chunklist.m3u8') != -1:
                t_quality = int(t.split('/')[0])
                if t_quality > last_quality:
                    last_quality = t_quality
                    last_url = t
        if last_url is not None and last_url != '':
            last_url = url.split('chunklist')[0] + last_url
            return last_url
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
    return url



def streaming2(contenttype, contentid, quality, action='dash', ishevc='n', isabr='y', return_url=False):
    """재생관련 정보 (스트리밍 / 다운로드 url 발급)"""
    # contenttype : live, vod, movie, clip, timemachine, onairvod
    # contentid  : live = channelid, 프로그램 = programid, vod = contentid, 영화 = movieid, 클립 = clipid
    # action : hls, dash, progressive, download
    # quality : 100p (라디오), 360p, 480p, 720p, 1080p, 2160p, default, radio   
    # authtype  : signed url = url, http header 인증 = cookie
    # isabr - adaptive streaming 여부 : y, n
    # ishevc - hevc 여부 : y, n
    if quality == 'FHD':
        quality = '1080p'
    elif quality == 'HD':
        quality = '720p'
    elif quality == 'SD':
        quality = '480p'
    elif quality == 'UHD':
        quality = '2160p'
    #quality = '2160p'
    if contenttype == 'live' :
        ishevc = 'n'
        isabr = 'n'

    try:
        param = get_baseparameter()
        param['credential'] = SystemModelSetting.get('site_wavve_credential')
        if contenttype == 'general':
            contenttype = 'vod'

        elif contenttype == 'onair':
            contenttype = 'onairvod'
        param['contenttype'] = contenttype
        param['contentid'] = contentid
        param['action'] = action
        param['quality'] = quality
        #param['guid'] = get_guid()
        param['guid'] = ''
        param['deviceModelId'] = 'Windows 10'
        param['authtype'] = 'url' #cookie, url
        #if contenttype == 'vod':
        #    isabr = 'y'
        param['isabr'] = isabr
        param['ishevc'] = ishevc
        param['lastplayid'] = 'none'

        url = "%s/streaming?%s" % (config['base_url'], py_urllib.urlencode(param))
        #logger.debug("STREAM2 : %s", url)
        if return_url:
            return url
        response = session.get(url, headers=config['headers'], proxies=get_proxies())
        data = response.json()
        
        #logger.debug(json.dumps(data, indent=4))
        if response.status_code == 200:
            #if data['playurl'].endswith('.mpd'):
            if data['playurl'].find('.mpd') != -1:
                if data['playurl'].endswith('.mpd'):
                    data['playurl'] += '?' + data['awscookie']
                ret = {}
                ret['uri'] = data['playurl']
                ret['drm_scheme'] = 'widevine'
                ret['drm_license_uri'] = data['drm']['drmhost']
                ret['drm_key_request_properties'] = {
                    'origin' : 'https://www.wavve.com',
                    'sec-fetch-site' : 'same-site',
                    'sec-fetch-mode' : 'cors',
                    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36',
                    #'Host' : 'cj.drmkeyserver.com',
                    'referer' : 'https://www.wavve.com',
                    'pallycon-customdata' : data['drm']['customdata'],
                    'cookie' : data['awscookie'],
                    'content-type' : 'application/octet-stream',
                }
                data['playurl'] = ret

            else:
                return streaming(contenttype, contentid, quality, ishevc='n')
            return data
        else:
            if 'resultcode' in data:
                #logger.debug(data['resultmessage'])
                pass
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())



def getpermissionforcontent(contentid, contenttype='movie'):
    try:
        param = get_baseparameter()
        param['contentid'] = contentid
        param['contenttype'] = contenttype
        param['credential'] = SystemModelSetting.get('site_wavve_credential')

        url = "%s/getpermissionforcontent?%s" % (config['base_url'], py_urllib.urlencode(param))
        response = session.get(url, headers=config['headers'])
        data = response.json()
        return data
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())