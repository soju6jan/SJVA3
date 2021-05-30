import os, sys, traceback

from . import logger

class ToolUtil(object):

    @classmethod
    def make_apikey_url(cls, url):
        from framework import SystemModelSetting
        if not url.startswith('http'):
            url = SystemModelSetting.get('ddns') + url
        if SystemModelSetting.get_bool('auth_use_apikey'):
            if url.find('?') == -1:
                url += '?'
            else:
                url += '&'
            url += 'apikey=%s' % SystemModelSetting.get('auth_apikey')
        return url
    
    @classmethod
    def save_dict(cls, data, filepath):
        try:
            import json, codecs
            data = json.dumps(data, indent=4, ensure_ascii=False)
            ofp = codecs.open(filename, 'w', encoding='utf8')
            ofp.write(s)
            ofp.close()
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())
