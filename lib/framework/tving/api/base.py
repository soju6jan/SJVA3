# -*- coding: utf-8 -*-
import os
import traceback
import sys
import requests
import time
import json
import base64

from framework import app, py_urllib, SystemModelSetting
from framework.logger import get_logger
from framework.util import Util
from support.base import d
logger = get_logger('tving_api')

#session = requests.session()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer' : '',
#    'Cookie' :'over18=1'
} 

config = {
    'param' : "&free=all&lastFrequency=n&order=broadDate", #최신
    'program_param' : '&free=all&order=frequencyDesc&programCode=%s',
    'default_param' : '&screenCode=CSSD0100&networkCode=CSND0900&osCode=CSOD0900&teleCode=CSCD0900&apiKey=1e7952d0917d6aab1f0293a063697610'
}


def get_proxies():
    proxy = get_proxy()
    if proxy is not None:
        return {"https": proxy, 'http':proxy}

# for ffmpeg
def get_proxy():
    if SystemModelSetting.get_bool('site_tving_use_proxy'):
        return SystemModelSetting.get('site_tving_proxy_url')


def do_login(user_id, user_pw, login_type):
    try:
        url = 'https://user.tving.com/user/doLogin.tving'
        if login_type == '0': 
            login_type_value = '10'
        else: 
            login_type_value = '20'
        params = { 
            'userId' : user_id,
            'password' : user_pw,
            'loginType' : login_type_value
        }
        res = requests.post(url, data=params)
        cookie = res.headers['Set-Cookie']
        #logger.debug(res.text)
        #logger.debug(cookie)
        for c in cookie.split(','):
            c = c.strip()
            if c.startswith('_tving_token'):
                ret = c.split(';')[0]
                return ret
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def get_vod_list(p=None, page=1):
    try:
        url = 'http://api.tving.com/v1/media/episodes?pageNo=%s&pageSize=18&adult=all&guest=all&scope=all&personal=N' % page
        if p is not None: 
            url += p
        else:
            url += config['param']
        url += config['default_param']
        res = requests.get(url)
        #logger.debug(url)
        return res.json()
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def get_episode_json_default(episode_code, quality):
    logger.debug('get_episode_json_default :%s, %s', episode_code, quality)
    ts = '%d' % time.time()
    try:
        if quality == 'stream70':
            tmp_param = config['default_param'].replace('CSSD0100', 'CSSD1200')
            url = 'http://api.tving.com/v2/media/stream/info?info=y%s&noCache=%s&mediaCode=%s&streamCode=%s&callingFrom=FLASH' % (tmp_param, ts, episode_code, quality)    
        else:
            url = 'http://api.tving.com/v2/media/stream/info?info=y%s&noCache=%s&mediaCode=%s&streamCode=%s&callingFrom=FLASH' % (config['default_param'], ts, episode_code, quality)
        
        headers['Cookie'] = SystemModelSetting.get('site_tving_token')
        r = requests.get(url, headers=headers, proxies=get_proxies())
        logger.debug(url)
        data = r.json()
        
        #logger.debug(json.dumps(data, indent=4))
        logger.debug('json message : %s', data['body']['result']['message'])
        url = data['body']['stream']['broadcast']['broad_url']
        #logger.debug(url)
        decrypted_url = decrypt(episode_code, ts, url)
        logger.debug(decrypted_url)
        if decrypted_url.find('m3u8') == -1:
            decrypted_url = decrypted_url.replace('rtmp', 'http')
            decrypted_url = decrypted_url.replace('?', '/playlist.m3u8?')
        #2020-06-12
        if decrypted_url.find('smil/playlist.m3u8') != -1 and decrypted_url.find('content_type=VOD') != -1 :
            tmps = decrypted_url.split('playlist.m3u8')
            r = requests.get(decrypted_url, headers=headers, proxies=get_proxies())
            lines = r.text.split('\n')
            logger.debug(lines)
            i = -1
            last = ''
            while len(last) == 0:
                last = lines[i].strip()
                i -= 1
            decrypted_url = '%s%s' % (tmps[0], last)
        logger.debug('last decrypted_url : %s', decrypted_url)
        return data, decrypted_url
    except Exception as exception:
        logger.error(r.text)
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())




def get_episode_json_default_live(episode_code, quality, inc_quality=True):
    #logger.debug('get_episode_json_default :%s, %s, %s', episode_code, quality, token)
    ts = '%d' % time.time()
    try:
        if inc_quality:
            url = 'http://api.tving.com/v2/media/stream/info?info=y%s&noCache=%s&mediaCode=%s&streamCode=%s&callingFrom=FLASH' % (config['default_param'], ts, episode_code, quality)
        else:
            url = 'http://api.tving.com/v2/media/stream/info?info=y%s&noCache=%s&mediaCode=%s&callingFrom=FLASH' % (config['default_param'], ts, episode_code)

        headers['Cookie'] = SystemModelSetting.get('site_tving_token')
        r = requests.get(url, headers=headers, proxies=get_proxies())
        data = r.json()
        #logger.debug(d(data))
        #logger.debug(url)
        if data['body']['stream']['drm_yn'] == 'N':
            if 'broad_url' in data['body']['stream']['broadcast']:
                url = data['body']['stream']['broadcast']['broad_url']
            else:
                #return get_stream_info(episode_code, quality)
                #return data, None
                #url = data['body']['stream']['broadcast']['widevine']['broad_url']
                return

            decrypted_url = decrypt(episode_code, ts, url)
            if decrypted_url.find('.mp4') != -1 and decrypted_url.find('/VOD/') != -1:
                return data, decrypted_url
            if decrypted_url.find('Policy=') == -1:
                data, ret = get_episode_json_default_live(episode_code, quality, inc_quality=False)
                if quality == 'stream50' and ret.find('live2000.smil'):
                    ret = ret.replace('live2000.smil', 'live5000.smil')
                    return data, ret
            #logger.debug('decrypted_url : %s', decrypted_url)
            return data, decrypted_url
        else:
            url = data['body']['stream']['broadcast']['widevine']['broad_url']
            logger.error(url)
            decrypted_url = decrypt(episode_code, ts, url)
            logger.error(decrypted_url)


    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def get_episode_json(episode_code, quality, is_live=False):
    try:
        if is_live:
            return get_episode_json_default_live(episode_code, quality)
        else:
            return get_episode_json_default(episode_code, quality)
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())



def decrypt(code, key, value):
    try:
        from Crypto.Cipher import DES3      
        if app.config['config']['is_py2']:
            data = base64.decodestring(value.encode())
            cryptoCode = 'cjhv*tving**good/%s/%s' % (code[-3:], key)
            key = cryptoCode[:24]
            des3 = DES3.new(key, DES3.MODE_ECB)
            ret = des3.decrypt(data)
            pad_len = ord(ret[-1])
        else:
            data = base64.decodebytes(value.encode())
            cryptoCode = 'cjhv*tving**good/%s/%s' % (code[-3:], key)
            key = cryptoCode[:24]
            des3 = DES3.new(key, DES3.MODE_ECB)
            ret = des3.decrypt(data)
            pad_len = ret[-1]
        ret = ret[:-pad_len]
        return ret.decode()
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def get_filename(episode_data):
    try:
        title = episode_data["body"]["content"]["program_name"]
        title = title.replace("<", "").replace(">", "").replace("\\", "").replace("/", "").replace(":", "").replace("*", "").replace("\"", "").replace("|", "").replace("?", "").replace("  ", " ").strip()
        episodeno = episode_data["body"]["content"]["frequency"]
        airdate = str(episode_data["body"]["content"]["info"]["episode"]["broadcast_date"])[2:]

        currentQuality = None
        if episode_data["body"]["stream"]["quality"] is None:
            currentQuality = "stream40"
        else:
            qualityCount = len(episode_data["body"]["stream"]["quality"])
            for i in range(qualityCount):
                if episode_data["body"]["stream"]["quality"][i]["selected"] == "Y":
                    currentQuality = episode_data["body"]["stream"]["quality"][i]["code"]
                    break
        if currentQuality is None:
            return
        qualityRes = get_quality_to_res(currentQuality)
        episodeno_str = str(episodeno)
        if episodeno < 10:
            episodeno_str = '0' + episodeno_str
        
        ret = '%s.E%s.%s.%s-ST.mp4' % (title, episodeno_str, airdate, qualityRes)
        return ret
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def get_quality_to_tving(quality):
    if quality == 'FHD':
        return 'stream50'
    elif quality == 'HD':
        return 'stream40'
    elif quality == 'SD':
        return 'stream30'
    elif quality == 'UHD':
        return 'stream70'
    return 'stream50'


def get_quality_to_res(quality):
    if quality == 'stream50':
        return '1080p'
    elif quality == 'stream40':
        return '720p'
    elif quality == 'stream30':
        return '480p'
    elif quality == 'stream70':
        return '2160p'
    elif quality == 'stream25':
        return '270p'
    return '1080p'


# 채널 목록
def get_live_list(list_type=0, order='rating', include_drm=False):
    if list_type == 0 or list_type == '0': 
        params = ['&channelType=CPCS0100']
    elif list_type == 1 or list_type == '1': 
        params = ['&channelType=CPCS0300']
    else: 
        params = ['&channelType=CPCS0100', '&channelType=CPCS0300']
    ret = []
    for param in params:
        page = 1
        while True:
            hasMore, data = get_live_list2(param, page, order=order, include_drm=include_drm)
            for i in data: 
                ret.append(i)
            if hasMore == 'N': 
                break
            page += 1
    return ret


def is_drm_channel(code):
    # C07381:ocn C05661:디즈니채널  C44441:koon  C04601:ocn movie  C07382:ocn thrill
    return (code in ['C07381', 'C05661', 'C44441', 'C04601', 'C07382'])

def get_live_list2(param, page, order='rating', include_drm=True):
    has_more = 'N'
    try:
        result = []
        url = 'http://api.tving.com/v1/media/lives?pageNo=%s&pageSize=20&order=%s&adult=all&free=all&guest=all&scope=all' % (page, order)
        
        if param is not None: 
            url += param
        url += config['default_param']			
        res = requests.get(url)
        data = res.json()

        #logger.debug(url)
        for item in data["body"]["result"]:
            try:
                # 2020-11-10 현재 /v1 에서는 drm채널인지 알려주지않고, 방송이 drm 적용인지 알려줌. 그냥 fix로..
                info = {'is_drm':is_drm_channel(item['live_code'])}
                info['id'] = item["live_code"]
                info['title'] = item['schedule']['channel']['name']['ko']
                info['episode_title'] = ' '
                info['img'] = 'http://image.tving.com/upload/cms/caic/CAIC1900/%s.png' % item["live_code"]
                if item['schedule']['episode'] is not None:
                    info['episode_title'] = item['schedule']['episode']['name']['ko']
                    if info['title'].startswith('CH.') and len(item['schedule']['episode']['image']) > 0:
                        info['img'] = 'http://image.tving.com' + item['schedule']['episode']['image'][0]['url']
                info['free'] = (item['schedule']['broadcast_url'][0]['broad_url1'].find('drm') == -1)
                info['summary'] = info['episode_title']
                result.append(info)
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
        has_more = data["body"]["has_more"]
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
    return has_more, result


def get_movie_json(code):
    ts = '%d' % time.time()
    try:
        quality = 'stream70'
        if quality == 'stream70':
            tmp_param = config['default_param'].replace('CSSD0100', 'CSSD1200')
            url = 'http://api.tving.com/v1/media/stream/info?info=y%s&noCache=%s&mediaCode=%s&streamCode=%s&callingFrom=FLASH' % (tmp_param, ts, code, quality)    
        else:
            url = 'http://api.tving.com/v1/media/stream/info?info=y%s&noCache=%s&mediaCode=%s&streamCode=%s&callingFrom=FLASH' % (config['default_param'], ts, code, quality)

        url += '&deviceId=%s' % SystemModelSetting.get('site_tving_deviceid')
        headers['Cookie'] = SystemModelSetting.get('site_tving_token')
        r = requests.get(url, headers=headers, proxies=get_proxies())
        data = r.json()
        
        #logger.debug(data)
        #logger.debug('json message : %s', data['body']['result']['message'])
        data['ret'] = {}
        if data['body']['result']['code'] == "000":
            if '4k_nondrm_url' in data['body']['stream']['broadcast']:
                decrypted_url = decrypt(code, ts, data['body']['stream']['broadcast']['4k_nondrm_url'])
                #logger.debug(decrypted_url)
                if decrypted_url.find('5000k_PC.mp4') != -1:
                    data['ret']['ret'] = 'ok'
                    data['ret']['decrypted_url'] = decrypted_url
                    data['ret']['filename'] = Util.change_text_for_use_filename('%s.%s.%s.2160p-ST.mp4' % (data['body']['content']['info']['movie']['name']['ko'], str(data['body']['content']['info']['movie']['release_date'])[:4], data['body']['content']['info']['movie']['name']['en']))
                else:
                    data['ret']['ret'] = 'no_4k'
                    data['ret']['decrypted_url'] = decrypted_url
        else:
            data['ret']['ret'] = 'need_pay'

        return data
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def get_prefer_url(url):
    try:
        response = requests.get(url, headers=config['headers'])
        data = response.text.strip()
        last_url = None
        for t in reversed(data.split('\n')):
            if t.strip().find('chunklist.m3u8') != -1:
                last_url = t
                break
        if last_url is not None and last_url != '':
            last_url = url.split('chunklist')[0] + last_url
            return last_url
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
    return url



def get_vod_list2(param=None, page=1, genre='all'):
    try:
        url = 'https://api.tving.com/v2/media/episodes?pageNo=%s&pageSize=24&order=new&adult=all&free=all&guest=all&scope=all&lastFrequency=n&personal=N' % (page)
        if genre != 'all':
            url += '&categoryCode=%s' % genre
        if param is not None: 
            url += param
        url += config['default_param']
        res = requests.get(url)
        return res.json()
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


# 방송정보
def get_program_programid(programid):
    try:
        url = 'https://api.tving.com/v2/media/program/%s?pageNo=1&pageSize=10&order=name' % programid
        url += config['default_param']
        res = requests.get(url)
        #logger.debug(url)
        return res.json()
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def get_frequency_programid(programid, page=1):
    try:
        url = 'https://api.tving.com/v2/media/frequency/program/%s?pageNo=%s&pageSize=10&order=new&free=all&adult=all&scope=all' % (programid, page)
        url += config['default_param']
        res = requests.get(url)
        #logger.debug(url)
        return res.json()
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def get_movies(page=1, category='all'):
    try:
        url = 'https://api.tving.com/v2/media/movies?pageNo=%s&pageSize=24&order=viewDay&free=all&adult=all&guest=all&scope=all&productPackageCode=338723&personal=N&diversityYn=N' % (page)
        if category != 'all':
            url += '&multiCategoryCode=%s' % category
        url += config['default_param']
        res = requests.get(url)
        return res.json()
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())



def get_movie_json2(code, quality='stream50'):
    ts = '%d' % time.time()
    try:
        url = 'http://api.tving.com/v1/media/stream/info?info=y%s&noCache=%s&mediaCode=%s&streamCode=%s&callingFrom=FLASH' % (config['default_param'], ts, code, quality)
        url += '&deviceId=%s' % SystemModelSetting.get('site_tving_deviceid')
        headers['Cookie'] = SystemModelSetting.get('site_tving_token')
        r = requests.get(url, headers=headers, proxies=get_proxies())
        data = r.json()
        return data
        
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def get_schedules(code, date, start_time, end_time):
    try:
        url = 'https://api.tving.com/v2/media/schedules?pageNo=1&pageSize=20&order=chno&scope=all&adult=n&free=all&broadDate=%s&broadcastDate=%s&startBroadTime=%s&endBroadTime=%s&channelCode=%s' % (date, date, start_time, end_time, ','.join(code))
        url += config['default_param']
        res = requests.get(url)
        return res.json()
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())



#2020-11-10
def get_device_id(token):
    try:
        url = "http://api.tving.com/v1/user/device/list?"
        url += config['default_param'][1:]
        headers['Cookie'] = token
        r = requests.get(url, headers=headers)
        data = r.json()
        if data['header']['message'] != 'OK':
            return
        for tmp in data['body']:
            if tmp['model'] == 'PC':
                return tmp['uuid']
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def get_device_list(token):
    try:
        url = "http://api.tving.com/v1/user/device/list?"
        url += config['default_param'][1:]
        headers['Cookie'] = token
        r = requests.get(url, headers=headers)
        data = r.json()
        return data
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def search(keyword):
    # gubun VODBC, VODMV
    try:
        url = 'https://search.tving.com/search/common/module/getAkc.jsp?kwd=' + py_urllib.quote(str(keyword))
        data = requests.get(url).json()
        if 'dataList' in data['akcRsb']:
            return data['akcRsb']['dataList']
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
