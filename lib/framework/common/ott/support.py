# -*- coding: utf-8 -*-
import os
import io
import traceback
import requests
import re
import json

from framework import logger
from tool_base import d

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}


class OTTSupport(object):
    
    @staticmethod
    def get_naver_url(target_url, quality):
        try:
            if target_url.startswith('SPORTS_'):
                target_ch = target_url.split('_')[1]
                if not target_ch.startswith('ad') and not target_ch.startswith('ch'):
                    target_ch = 'ch' + target_ch
                qua = '5000'
                tmp = {'480':'800', '720':'2000', '1080':'5000'}
                qua = tmp[quality] if quality in tmp else qua
                tmp = 'https://apis.naver.com/pcLive/livePlatform/sUrl?ch=%s&q=%s&p=hls&cc=KR&env=pc' % (target_ch, qua)
                url = requests.get(tmp, headers=headers).json()['secUrl']
            else:
                data = requests.get(target_url).text
                match = re.compile(r"sApiF:\s'(?P<url>.*?)',").search(data)
                if match is not None:
                    json_url = match.group('url')
                    data = requests.get(json_url, headers=headers).json()
                    url = None
                    for tmp in data['streams']:
                        if tmp['qualityId'] == quality:
                            url = tmp['url']
                            break
            return url
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def get_kakao_url(target):
        try:
            tmp = "https://tv.kakao.com/api/v5/ft/livelinks/impress?player=monet_html5&service=kakao_tv&section=kakao_tv&dteType=PC&profile=BASE&liveLinkId={liveid}&withRaw=true&contentType=HLS".format(liveid=target)
            url = requests.get(tmp, headers=headers).json()['raw']['videoLocation']['url']
            return url
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @staticmethod
    def get_kbs_url(source_id):
        try:
            tmp = 'http://onair.kbs.co.kr/index.html?sname=onair&stype=live&ch_code=%s' % source_id
            data = requests.get(tmp, headers=headers).text
            idx1 = data.find('var channel = JSON.parse') + 26
            idx2 = data.find(');', idx1)-1
            data = data[idx1:idx2].replace('\\', '')
            data = json.loads(data)
            max = 0
            url = None
            for item in data['channel_item']:
                #logger.debug(item)
                tmp = int(item['bitrate'].replace('Kbps', ''))
                if tmp > max:
                    url = item['service_url']
                    max = tmp
            return url
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_sbs_url(source_id):
        try:
            prefix = '' if source_id != 'SBS' and int(source_id[1:]) < 20 else 'virtual/'
            tmp = 'http://apis.sbs.co.kr/play-api/1.0/onair/%schannel/%s?v_type=2&platform=pcweb&protocol=hls&ssl=N&jwt-token=%s&rnd=462' % (prefix, source_id, '')
            data = requests.get(tmp, headers=headers).json()
            url = data['onair']['source']['mediasource']['mediaurl']
            return url
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())