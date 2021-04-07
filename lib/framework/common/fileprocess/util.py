# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import time
import threading
import shutil

from framework.common.fileprocess import logger


def remove_small_file_and_move_target(path, size, target=None, except_ext=None):
    ''' path 안의 폴더들을 재귀탐색하여 기준 크기보다 작은 것은 삭제하고 크기보다 큰 것은 target 경로로 이동한다. 결론적으로 모든 폴더들은 삭제된다.

    target이 None경우 path 로 이동한다. 이동할때 파일이 이미 존재하는 경우 파일을 삭제한다. 크기 체크 안함.

    Argument
    path : 정리할 폴더
    size : 파일 크기. 메가단위
    target : 이동할 폴더. None경우 path
    except_exe : 삭제하지 않을 확장자. 기본 : ['.smi', '.srt', 'ass']

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
                    remove_small_file_and_move_target(file_path, size, target=target, except_ext=except_ext)
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
                        try: 
                            logger.info(u'FILE REMOVE : %s %s', file_path, os.stat(file_path).st_size)
                        except: 
                            logger.info(u'FILE REMOVE')
                        os.remove(file_path)
            except UnicodeDecodeError:
                pass
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def remove_match_ext(path, ext_list):
    ''' 
    '''
    try:
        lists = os.listdir(path)
        for f in lists:
            try:
                file_path = os.path.join(path, f)
                if os.path.isdir(file_path): 
                    remove_match_ext(file_path, ext_list)
                else:
                    if os.path.splitext(file_path.lower())[1][1:] in ext_list:
                        logger.info(u'REMOVE : %s', file_path)
                        os.remove(file_path)
            except UnicodeDecodeError:
                pass
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())