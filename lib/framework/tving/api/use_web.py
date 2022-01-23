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
logger = get_logger('tving_api')

from .base import get_proxies

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36',
    'Accept' : 'application/json, text/plain, */*',
    'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'origin' : 'https://www.tving.com',
    'sec-fetch-dest' : 'empty',
    'sec-fetch-mode' : 'cors',
    'sec-fetch-site' : 'same-origin',
} 


def get_stream_info_by_web(content_type, media_code, quality):
    """
    logger.debug(content_type)
    logger.debug(media_code)
    logger.debug(quality)
    """

    ooc = 'isTrusted=false^type=oocCreate^eventPhase=0^bubbles=false^cancelable=false^defaultPrevented=false^composed=false^timeStamp=3336.340000038035^returnValue=true^cancelBubble=false^NONE=0^CAPTURING_PHASE=1^AT_TARGET=2^BUBBLING_PHASE=3^'

    try:
        data = {
            'apiKey' : '1e7952d0917d6aab1f0293a063697610',
            'info' : 'Y',
            'networkCode' : 'CSND0900',
            'osCode' : 'CSOD0900',
            'teleCode' : 'CSCD0900',
            'mediaCode' : media_code,
            'screenCode' : 'CSSD0100',
            'callingFrom' : 'HTML5',
            'streamCode' : quality,
            'deviceId' : SystemModelSetting.get('site_tving_deviceid'),
            'adReq' : 'adproxy',
            'ooc' : ooc,
            'wm': 'Y',
            'uuid' : SystemModelSetting.get('site_tving_uuid')
        }
        cookies = {
            '_tving_token': SystemModelSetting.get('site_tving_token').split('=')[1], 
            'onClickEvent2': py_urllib.quote(ooc),
            'TP2wgas1K9Q8F7B359108383':'Y', 
        }
        #https://jtbc2-mcdn.tving.com/jtbc2/live5000.smil/playlist.m3u8?dvr&Policy=eyJTdGF0ZW1lbnQiOiBbeyJSZXNvdXJjZSI6IioiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE2MTU1MDk5NDJ9LCJJcEFkZHJlc3MiOnsiQVdTOlNvdXJjZUlwIjoiMC4wLjAuMC8wIn19fV19&Signature=Bh4P1vsA~3M4JplXiSuR5tsj~o~hgrfpi2bPEvCob6NNwBoKOrTmqhXWVl9WiYZSo2NZzbVw8aRClwJaciG4ZDfFIV03uoi9NO779lisL8-J~lSbTWs5KKMfVfEe~SYo5S7vIJWcp9VjOjc5WARdmTpqedc3PtjBp0qP8hCfcQQ2MsCHlCqGvrIgZo4GDpo7kUBdMUHq88GCG3ew35X884qVN5NxDH3qq-5s1jSFlZQ0dY9aGGINBYRpH7q2pNCO0uwV8Bz9gPQEhylEid1Ef3N7YmqUEgOB~tQyNHUfNmKbnaj7hINOGswn3PVmyHAGgfuyLn7rPKsIrL~ZJ3chSg__&Key-Pair-Id=APKAIXCIJCFRGOUEZDWA

        #https://jtbc2-mcdn.tving.com/jtbc2/live5000.smil/playlist.m3u8?dvr&Policy=eyJTdGF0ZW1lbnQiOiBbeyJSZXNvdXJjZSI6IioiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE2MTU1MDk4NTF9LCJJcEFkZHJlc3MiOnsiQVdTOlNvdXJjZUlwIjoiMC4wLjAuMC8wIn19fV19&Signature=KhV3vX4-ZIZFrrzPwJjhaYtlf~7Ra1jq1i3DQWId2MsyCpGFXZFC5cOqV1R8FEtJEdpytC2GwywQHCRFVVbgkh~gLB8Af8wHNaRh6dc8Yse97Ea5ZANCjs9VwWjfvyfbnVVGiZnAcXsB~NUwSsmkmciQORSYSRCzbk3KfvTsCeGPY-0PR5zRj4CM0bP0RR5Mm2E-mcXxKhLLgbjun~gajZvX4iKk4lEa9WNLKPa27Xg13p~tuhUH8VLANECMKiXIcbkqgAlUgdj68loDxL4p6oCXvOMJkM7~-9DpqNZ6C~RBwDOY-7Kz-5lMCyBE1xx9iMk3aSM2CksNCWRFfW45HA__&Key-Pair-Id=APKAIXCIJCFRGOUEZDWA%27


        #http://jtbc2-mcdn.tving.com/jtbc2/live5000.smil/playlist.m3u8?dvr&Policy=eyJTdGF0ZW1lbnQiOiBbeyJSZXNvdXJjZSI6IioiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE2MTU1MDk4NTF9LCJJcEFkZHJlc3MiOnsiQVdTOlNvdXJjZUlwIjoiMC4wLjAuMC8wIn19fV19&Signature=KhV3vX4-ZIZFrrzPwJjhaYtlf~7Ra1jq1i3DQWId2MsyCpGFXZFC5cOqV1R8FEtJEdpytC2GwywQHCRFVVbgkh~gLB8Af8wHNaRh6dc8Yse97Ea5ZANCjs9VwWjfvyfbnVVGiZnAcXsB~NUwSsmkmciQORSYSRCzbk3KfvTsCeGPY-0PR5zRj4CM0bP0RR5Mm2E-mcXxKhLLgbjun~gajZvX4iKk4lEa9WNLKPa27Xg13p~tuhUH8VLANECMKiXIcbkqgAlUgdj68loDxL4p6oCXvOMJkM7~-9DpqNZ6C~RBwDOY-7Kz-5lMCyBE1xx9iMk3aSM2CksNCWRFfW45HA__&Key-Pair-Id=APKAIXCIJCFRGOUEZDWA


        if True or content_type == 'live':
            headers['referer'] = 'https://www.tving.com/%s/player/%s' % (content_type, media_code)
            url = 'https://www.tving.com/streaming/info'
            res = requests.post(url, data=data, headers=headers, cookies=cookies, proxies=get_proxies())
            logger.error(res.text)
            data = res.json()
            #logger.debug(json.dumps(data, indent=4))
             
            ret = {}
            if 'widevine' in data['stream']['broadcast']:
                ret['uri'] = data['stream']['broadcast']['widevine']['broad_url']
                ret['drm_scheme'] = 'widevine'
                ret['drm_license_uri'] = 'http://cj.drmkeyserver.com/widevine_license'
                #data['stream']['drm_license_server_list']
                ret['drm_key_request_properties'] = {
                    'origin' : 'https://www.tving.com',
                    'sec-fetch-site' : 'cross-site',
                    'sec-fetch-mode' : 'cors',
                    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
                    'Host' : 'cj.drmkeyserver.com',
                    'referer' : 'https://www.tving.com/',
                    'AcquireLicenseAssertion' : data['stream']['drm_license_assertion'],
                }
                data['play_info'] = ret
                return data
            else:
                data['play_info'] = {'hls':data['stream']['broadcast']['broad_url']}
                return data



            
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
