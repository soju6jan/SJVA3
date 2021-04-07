# -*- coding: utf-8 -*-
import traceback
import requests
from framework import logger

def get_json_with_auth_session(referer, url, data):
    try:
        headers = {
            #'Accept' : 'application/json, text/plain, */*',
            #'Accept-Language':'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            #'Connection':'keep-alive',
            #'Content-Type':'application/x-www-form-urlencoded;charset=utf-8;',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
        }

        session = requests.Session()
        res = session.get(referer)
        text = res.text
        auth = text.split('$http.defaults.headers.common[\'Authorization\'] = "')[1].strip().split('"')[0]
        headers['Authorization'] = auth
    
        ci_session= res.headers['Set-Cookie'].split('ci_session=')[1].split(';')[0]
        headers['Cookie'] = 'ci_session=%s; USERCONTRY=kr; LANGU=kr;' % ci_session

        res = session.post(url, headers=headers, data=data)
        logger.debug('get_json_with_auth_session status_code : %s', res.status_code)
        return res.json(), headers
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
