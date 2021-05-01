# -*- coding: utf-8 -*-
#########################################################
# python
import os, re
import traceback
import time
import threading
import shutil

from framework import app
from . import logger

EXTENSION = 'mp4|avi|mkv|ts|wmv|m2ts|smi|srt|ass|m4v|flv|asf|mpg|ogm'

class ToolExpandFileProcess(object):

    @classmethod
    def remove_extension(cls, filename):
        ret = filename
        regex = r'(.*?)\.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).match(filename)
        if match:
            ret = filename.replace('.' + match.group('ext'), '')
        return ret
    


    @classmethod
    def remove_small_file_and_move_target(cls, path, size, target=None, except_ext=None, small_move_path=None):
        ''' path 안의 폴더들을 재귀탐색하여 기준 크기보다 작은 것은 삭제하고 크기보다 큰 것은 target 경로로 이동한다. 결론적으로 모든 폴더들은 삭제된다.

        target이 None경우 path 로 이동한다. 이동할때 파일이 이미 존재하는 경우 파일을 삭제한다. 크기 체크 안함.

        Argument
        path : 정리할 폴더
        size : 파일 크기. 메가단위
        target : 이동할 폴더. None경우 path
        except_exe : 삭제하지 않을 확장자. 기본 : ['.smi', '.srt', 'ass']
        no_remove_path : None인 경우 삭제. 값이 있는 경우 삭제가 아닌 이동

        Return
        True : 성공
        False : 실패
        '''
        try:
            if target is None: 
                target = path
            if except_ext is None:
                except_ext = ['.smi', '.srt', 'ass']
            lists = os.listdir(path)
            for f in lists:
                try:
                    file_path = os.path.join(path, f)
                    except_file = False
                    if os.path.splitext(file_path.lower())[1] in except_ext:
                        except_file = True
                    if os.path.isdir(file_path): 
                        cls.remove_small_file_and_move_target(file_path, size, target=target, except_ext=except_ext)
                        if not os.listdir(file_path):
                            logger.info('REMOVE DIR : %s', file_path)
                            os.rmdir(file_path)
                    else:
                        if os.stat(file_path).st_size > 1024 * 1024 * size or  except_file:
                            if path == target: 
                                continue
                            try: 
                                logger.info('MOVE : %s', os.path.join(target, f))
                            except: 
                                logger.info('MOVE')
                            if os.path.exists(os.path.join(target, f)):
                                logger.info(u'ALREADY in Target : %s', os.path.join(target, f))
                                os.remove(file_path)
                            else:
                                shutil.move(file_path, os.path.join(target, f))
                        else:
                            if small_move_path is None or small_move_path == '':
                                try: 
                                    logger.info(u'FILE REMOVE : %s %s', file_path, os.stat(file_path).st_size)
                                except: 
                                    logger.info(u'FILE REMOVE')
                                os.remove(file_path)
                            else:
                                logger.info(u'SNALL FILE MOVE : %s', file_path)
                                shutil.move(file_path, os.path.join(small_move_path, f))

                except UnicodeDecodeError:
                    pass
                except Exception as exception:
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @classmethod
    def change_filename_censored(cls, filename):
        #24id
        match = re.compile('\d{2}id', re.I).search(filename.lower())
        id_before = None
        if match:
            id_before = match.group(0)
            filename = filename.lower().replace(id_before, 'zzid')
        
        try:
            filename = cls.change_filename_censored_old(filename)
            if filename is not None:
                if id_before is not None:
                    filename = filename.replace('zzid', id_before)
                base, ext = os.path.splitext(filename)
                tmps = base.split('-')
                tmp2 = tmps[1].split('cd')
                if len(tmp2) == 1:
                    tmp = '%s-%s%s' % (tmps[0], str(int(tmps[1])).zfill(3), ext)
                elif len(tmp2) == 2:
                    tmp = '%s-%scd%s%s' % (tmps[0], str(int(tmp2[0])).zfill(3), tmp2[1], ext)
                return tmp
        except Exception as exception:
            logger.debug('filename : %s', filename)
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return filename

    
    @classmethod
    def change_filename_censored_old(cls, filename):
 
        #logger.debug('get_plex_filename:%s', file)
        original_filename = filename
        #return file
        filename = filename.lower()
        
        #-h264 제거
        filename = filename.replace('-h264', '')
        filename = filename.replace('-264', '')
        #2019-10-06 -■-IBW-670Z_1080p.mkv => ibw-6701080 [-■-IBW-670Z_1080p].mkv
        filename = filename.replace('z_1080p', '').replace('z_720p', '')
        filename = filename.replace('z_', '')
        filename = filename.replace('-c', '')
        
        #if file.find('@') != -1:
        #    file = file.split('@')[1]

        # 1080p
        regex = r'^(?P<code>.*?)\.1080p\.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).match(filename)
        if match:
            filename = '%s.%s' % (match.group('code'), match.group('ext'))
        # fhd
        #regex = r'^(?P<code>.*?)fhd\.(?P<ext>%s)$' % EXTENSION
        #2019-10-06
        # sdmu-676_FHD.mp4 => sdmu-676cd-1 [sdmu-676_FHD].mp4
        regex = r'^(?P<code>.*?)(\_|\-)fhd\.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).match(filename)
        if match:
            filename = '%s.%s' % (match.group('code'), match.group('ext'))

        # [ ]숫자 제거
        regex = r'^\[.*?\]\d+(?P<code>.*?)\.(?P<ext>%s)$'
        match = re.compile(regex).match(filename)
        if match:
            filename = '%s.%s' % (match.group('code'), match.group('ext'))

        # [ ] 제거
        regex = r'^\[.*?\](?P<code>.*?)\.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).match(filename)
        if match:
            filename = '%s.%s' % (match.group('code'), match.group('ext'))

        # ( ) 제거
        regex = r'^\(.*?\)(?P<code>.*?)\.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).match(filename)
        if match:
            filename = '%s.%s' % (match.group('code'), match.group('ext'))

        
        # 3,4자리 숫자
        regex = r'^\d{3,4}(?P<code>.*?)\.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).match(filename)
        if match:
            filename = '%s.%s' % (match.group('code'), match.group('ext'))

        regex = r'^.*\.com\-?\d*\-?\d*@?(?P<code>.*?)(\-h264)??\.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).match(filename)
        if match:
            filename = '%s.%s' % (match.group('code'), match.group('ext'))
        
        regex = r'^(?P<dummy>.*\.com.*?)(?P<code>[a-z]+)'
        match = re.compile(regex).match(filename)
        if match:
            filename = filename.replace(match.group('dummy'), '')
        
        # -5 제거
        regex = r'^(?P<code>.*?)\-5.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).match(filename)
        if match:
            filename = '%s.%s' % (match.group('code'), match.group('ext'))

        
        # dhd1080.com@1fset00597hhb.mp4
        #regex = r'^.*?com@(\d)?(?P<code>[a-z]+\d+)\w+.(?P<ext>%s)$' % EXTENSION
        #match = re.compile(regex).match(file)
        #if match:
        #    file = '%s.%s' % (match.group('code'), match.group('ext'))


        # s-cute
        regex = r'^s-cute\s(?P<code>\d{3}).*?.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).match(filename)
        if match:
            ret = 'scute-%s.%s' % (match.group('code'), match.group('ext'))
            return ret.lower()

        logger.debug('5. %s', filename)
        regex_list = [
            r'^(?P<name>[a-zA-Z]+)[-_]?(?P<no>\d+)(([-_]?(cd|part)?(?P<part_no>\d))|[-_]?(?P<part_char>\w))?\.(?P<ext>%s)$' % EXTENSION,
            r'^\w+.\w+@(?P<name>[a-zA-Z]+)[-_]?(?P<no>\d+)(([-_\.]?(cd|part)?(?P<part_no>\d))|[-_\.]?(?P<part_char>\w))?\.(?P<ext>%s)$' % EXTENSION
        ]
        for regex in regex_list:
            match = re.compile(regex).match(filename)
            if match:
                ret = filename
                part = None
                if match.group('part_no') is not None:
                    part = 'cd%s' % match.group('part_no')
                elif match.group('part_char') is not None:
                    part = 'cd%s' % (ord(match.group('part_char').lower()) - ord('a') + 1)
                if part is None:
                    ret = '%s-%s.%s' % (match.group('name').lower(), match.group('no'), match.group('ext'))
                else:
                    ret = '%s-%s%s.%s' % (match.group('name').lower(), match.group('no'), part, match.group('ext'))
                #logger.debug('%s -> %s' % (file, ret))
                return ret.lower()
        
        # T28 - 매치여야함.
        #logger.debug('N2 before:%s', file)
        regex = r'(?P<name>[a-zA-Z]+\d+)\-(?P<no>\d+).*?\.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).match(filename)
        if match:
            ret = '%s-%s.%s' % (match.group('name'), match.group('no'), match.group('ext'))
            #logger.debug('N2. %s -> %s' % (file, ret))
            return ret.lower()

        # 오리지널로 ABC123 매치여야함.
        # hjd2048.com-0113meyd466-264.mp4
        #logger.debug('N3 before:%s', original_filename)

        regex = r'^(?P<name>[a-zA-Z]{3,})\-?(?P<no>\d+).*?\.(?P<ext>%s)$' % EXTENSION
        #logger.debug(file)
        match = re.compile(regex).match(filename)
        if match:
            ret = '%s-%s.%s' % (match.group('name'), match.group('no'), match.group('ext'))
            #logger.debug('N3. %s -> %s' % (file, ret))]
            #logger.debug('match 00')
            return ret.lower()

        regex = r'^(?P<name>[a-zA-Z]{3,})\-?(?P<no>\d+).*?\.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).match(original_filename)
        if match:
            ret = '%s-%s.%s' % (match.group('name'), match.group('no'), match.group('ext'))
            #logger.debug('N3. %s -> %s' % (file, ret))]
            #logger.debug('match 11')
            return ret.lower()

        # 서치
        #logger.debug('N1 before:%s', file)
        regex = r'(?P<name>[a-zA-Z]+)\-(?P<no>\d+).*?\.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).search(filename)
        if match:
            ret = '%s-%s.%s' % (match.group('name'), match.group('no'), match.group('ext'))
            #logger.debug('N1. %s -> %s' % (file, ret))
            #logger.debug('match 22')
            return ret.lower()
        
        # 서치
        #logger.debug('N1 before:%s', file)
        regex = r'(?P<name>[a-zA-Z]+)\-(?P<no>\d+).*?\.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).search(original_filename)
        if match:
            ret = '%s-%s.%s' % (match.group('name'), match.group('no'), match.group('ext'))
            #logger.debug('N1. %s -> %s' % (file, ret))
            #logger.debug('match 33')
            return ret.lower()
        
        #21-01-08 fbfb.me@sivr00103.part1.mp4
        regex = r'\w+.\w+@(?P<name>[a-zA-Z]+)(?P<no>\d{5})\.(cd|part)(?P<part_no>\d+)\.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).match(original_filename)
        if match:
            ret = filename
            part = None
            if match.group('part_no') is not None:
                part = 'cd%s' % match.group('part_no')
            if part is None:
                ret = '%s-%s.%s' % (match.group('name').lower(), match.group('no'), match.group('ext'))
            else:
                ret = '%s-%s%s.%s' % (match.group('name').lower(), match.group('no'), part, match.group('ext'))
            #logger.debug('%s -> %s' % (file, ret))
            return ret.lower()

        #20-02-02
        regex = r'\w+.\w+@(?P<name>[a-zA-Z]+)(?P<no>\d{5}).*?.(?P<ext>%s)$' % EXTENSION
        match = re.compile(regex).search(original_filename)
        if match:
            no = match.group('no').replace('0', '').zfill(3)
            ret = '%s-%s.%s' % (match.group('name'), no, match.group('ext'))
            #logger.debug('match 44')
            return ret.lower()


        #logger.debug('%s -> %s' % (file, None))
        return None

