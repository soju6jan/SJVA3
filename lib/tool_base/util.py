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
            return '\n' + json.dumps(data, indent=4, ensure_ascii=False)
        else:
            return str(data)



    @classmethod
    def sizeof_fmt(cls, num, suffix='B'):
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.2f%s%s" % (num, 'Y', suffix)

    @classmethod
    def sizeof_fmt(cls, num, suffix='B'):
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.2f%s%s" % (num, 'Y', suffix)

    @classmethod
    def timestamp_to_datestr(cls, stamp, format='%Y-%m-%d %H:%M:%S'):
        from datetime import datetime
        tmp = datetime.fromtimestamp(stamp)
        return tmp.strftime(format)
    
    
    @classmethod
    def get_cate_char_by_first(cls, title):
        value = ord(title[0].upper())
        if value >= ord('0') and value <= ord('9'): return '0Z'
        elif value >= ord('A') and value <= ord('Z'): return '0Z'
        elif value >= ord('가') and value < ord('나'): return '가'
        elif value < ord('다'): return '나'
        elif value < ord('라'): return '다'
        elif value < ord('마'): return '라'
        elif value < ord('바'): return '마'
        elif value < ord('사'): return '바'
        elif value < ord('아'): return '사'
        elif value < ord('자'): return '아'
        elif value < ord('차'): return '자'
        elif value < ord('카'): return '차'
        elif value < ord('타'): return '카'
        elif value < ord('파'): return '타'
        elif value < ord('하'): return '파'
        elif value <= ord('힣'): return '하'
        else: return '0Z'