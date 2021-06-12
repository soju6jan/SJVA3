import os, sys, traceback, json

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
            ofp = codecs.open(filepath, 'w', encoding='utf8')
            ofp.write(data)
            ofp.close()
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())


    @classmethod
    def dump(cls, data):
        if type(data) in [type({}), type([])]:
            import json
            return '\n' + json.dumps(data, indent=4, ensure_ascii=False)
        else:
            return str(data)
