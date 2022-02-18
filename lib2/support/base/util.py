import os, traceback, io, re, json, codecs
from . import logger

from functools import wraps
import time
def pt(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        start = time.time()
        #logger.debug(f"FUNC START [{f.__name__}]")
        result = f(*args, **kwds)
        elapsed = time.time() - start
        logger.info(f"FUNC END [{f.__name__}] {elapsed}")
        return result
    return wrapper

default_headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
}


class SupportUtil(object):

    @classmethod
    def is_arm(cls):
        try:
            ret = False
            import platform
            if platform.system() == 'Linux':
                if platform.platform().find('86') == -1 and platform.platform().find('64') == -1:
                    ret = True
                if platform.platform().find('arch') != -1:
                    ret = True
                if platform.platform().find('arm') != -1:
                    ret = True
            return ret
        except Exception as e: 
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())
    


class celery(object):
    class task(object):
        def __init__(self, *args, **kwargs):
            if len(args) > 0:
                self.f = args[0]
    
        def __call__(self, *args, **kwargs):
            if len(args) > 0 and type(args[0]) == type(ffff):
                return args[0]
            self.f(*args, **kwargs)    