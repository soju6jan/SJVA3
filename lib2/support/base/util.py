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
    

    