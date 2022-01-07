import os, traceback, io, re, json, codecs
from . import logger

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
      