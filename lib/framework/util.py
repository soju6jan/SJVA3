# -*- coding: utf-8 -*-
#########################################################
# python
import os
import json
import traceback
import platform
import subprocess
# third-party
from sqlalchemy.ext.declarative import DeclarativeMeta
# sjva 공용
from framework.logger import get_logger
from framework import app
# 패키지

# 로그
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
#########################################################

class Util(object):
    @staticmethod
    def sizeof_fmt(num, suffix='Bytes'):
        """
        파일크기, 다운로드 속도 표시시 사용        
        """
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Y', suffix)

    @staticmethod
    def db_list_to_dict(db_list):
        """
        세팅DB에서 사용, (key, value) dict로 변환
        """
        ret = {}
        for item in db_list:
            ret[item.key] = item.value
        return ret

    @staticmethod
    def db_to_dict(db_list):
        ret = []
        for item in db_list:
            ret.append(item.as_dict())
        return ret

    @staticmethod
    def get_paging_info(count, current_page, page_size):
        try:
            paging = {}
            paging['prev_page'] = True
            paging['next_page'] = True
            if current_page <= 10:
                paging['prev_page'] = False
            
            paging['total_page'] = int(count / page_size) + 1
            if count % page_size == 0:
                paging['total_page'] -= 1
            paging['start_page'] = int((current_page-1)/10) * 10 + 1
            paging['last_page'] = paging['total_page'] if paging['start_page'] + 9 > paging['total_page'] else paging['start_page'] + 9
            if paging['last_page'] == paging['total_page']:
                paging['next_page'] = False
            paging['current_page'] = current_page
            paging['count'] = count
            logger.debug('paging : c:%s %s %s %s %s %s', count, paging['total_page'], paging['prev_page'], paging['next_page'] , paging['start_page'], paging['last_page'])
            return paging
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())
    
    @staticmethod
    def get_list_except_empty(source):
        tmp = []
        for _ in source:
            if _.strip().startswith('#'):
                continue
            if _.strip() != '':
                tmp.append(_.strip())
        return tmp

    @staticmethod
    def save_from_dict_to_json(d, filename):
        try:
            import codecs
            s = json.dumps(d)
            ofp = codecs.open(filename, 'w', encoding='utf8')
            ofp.write(s)
            ofp.close()
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())


    # list형태
    @staticmethod
    def execute_command(command):
        from tool_base import ToolSubprocess
        return ToolSubprocess.execute_command_return(command)
        

    
    @staticmethod
    def change_text_for_use_filename(text):
        from tool_base import ToolBaseFile
        return ToolBaseFile.text_for_filename(text)


    # 토렌트 인포에서 최대 크기 파일과 폴더명을 리턴한다
    @staticmethod
    def get_max_size_fileinfo(torrent_info):
        try:
            ret = {}
            max_size = -1
            max_filename = None
            for t in torrent_info['files']:
                if t['size'] > max_size:
                    max_size = t['size']
                    max_filename = str(t['path'])
            t = max_filename.split('/')
            ret['filename'] = t[-1]
            if len(t) == 1:
                ret['dirname'] = ''
            elif len(t) == 2:
                ret['dirname'] = t[0]
            else:
                ret['dirname'] = max_filename.replace('/%s' % ret['filename'], '')
            ret['max_size'] = max_size
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    # 압축할 폴더 경로를 인자로 받음. 폴더명.zip 생성
    @staticmethod
    def makezip(zip_path, zip_extension='zip'):
        import zipfile
        try:
            if os.path.isdir(zip_path):
                zipfilename = os.path.join(os.path.dirname(zip_path), '%s.%s' % (os.path.basename(zip_path), zip_extension))
                fantasy_zip = zipfile.ZipFile(zipfilename, 'w')
                for f in os.listdir(zip_path):
                    #if f.endswith('.jpg') or f.endswith('.png'):
                        src = os.path.join(zip_path, f)
                        fantasy_zip.write(src, os.path.basename(src), compress_type = zipfile.ZIP_DEFLATED)
                fantasy_zip.close()
            import shutil
            shutil.rmtree(zip_path)
            return True
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        return False



    @staticmethod
    def make_apikey(url):
        from framework import SystemModelSetting
        url = url.format(ddns=SystemModelSetting.get('ddns'))
        if SystemModelSetting.get_bool('auth_use_apikey'):
            if url.find('?') == -1:
                url += '?'
            else:
                url += '&'
            url += 'apikey=%s' % SystemModelSetting.get('auth_apikey')
        return url






class SingletonClass(object):
    __instance = None
    
    @classmethod
    def __getInstance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls.__getInstance
        return cls.__instance



class AlchemyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)