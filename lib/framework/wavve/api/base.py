# -*- coding: utf-8 -*-
import sys
import requests
from framework.logger import get_logger
logger = get_logger('wavve')

session = requests.session()

config = {
    'base_url': 'https://apis.pooq.co.kr',
    'base_parameter' : {
        'apikey' : 'E5F3E0D30947AA5440556471321BB6D9',
        'credential' : 'none',
        'device' : 'pc',
        'partner' : 'pooq',
        'pooqzone' : 'none',
        'region' : 'kor',
        'drm' : 'wm',
        'targetage' : 'auto'
    },
    'headers' : {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
    }, 
    
}





# https://api35-docs.pooq.co.kr/


#https://apis.pooq.co.kr/login?apikey=E5F3E0D30947AA5440556471321BB6D9&credential=none&device=pc&drm=wm&partner=pooq&pooqzone=none&region=kor&targetage=auto

