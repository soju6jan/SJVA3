# -*- coding: utf-8 -*-
#########################################################
import os, traceback, io, re
from . import logger

class ToolBaseFile(object):

    @classmethod
    def read(cls, filepath, mode='r'):
        try:
            import codecs
            ifp = codecs.open(filepath, mode, encoding='utf8')
            data = ifp.read()
            ifp.close()
            if isinstance(data, bytes):
                data = data.decode('utf-8') 
            return data
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @classmethod
    def download(cls, url, filepath):
        try:
            import requests
            with open(filepath, "wb") as file_is:   # open in binary mode
                response = requests.get(url)               # get request
                file_is.write(response.content)      # write to file
                return True
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())   
        return False


    @classmethod
    def write(cls, data, filepath, mode='w'):
        try:
            import codecs
            ofp = codecs.open(filepath, mode, encoding='utf8')
            if isinstance(data, bytes) and mode == 'w':
                data = data.decode('utf-8') 
            ofp.write(data)
            ofp.close()
            return True
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())
        return False


    @classmethod
    def text_for_filename(cls, text):
        text = text.replace('/', '')
        text = re.sub('[\\/:*?\"<>|]', '', text).strip()
        text = re.sub("\s{2,}", ' ', text)
        return text


    @classmethod
    def size(self, start_path = '.'):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size

