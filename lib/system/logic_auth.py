# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import random
import json
import string
import codecs

# third-party
import requests
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify

# sjva 공용
from framework.logger import get_logger
from framework import path_app_root, app
from framework.util import Util

# 패키지
from .plugin import package_name, logger
from .model import ModelSetting

class SystemLogicAuth(object):
    @staticmethod
    def process_ajax(sub, req):
        logger.debug(sub)
        try:
            if sub == 'apikey_generate':
                ret = SystemLogicAuth.apikey_generate()
                return jsonify(ret)
            elif sub == 'do_auth':
                ret = SystemLogicAuth.do_auth()
                return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    
    ##########################################################################

    @staticmethod
    def apikey_generate():
        try:
            value = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
            return value
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @staticmethod
    def get_auth_status(retry=True):
        try:
            value = ModelSetting.get('auth_status')
            ret = {'ret' : False, 'desc' : '', 'level' : 0, 'point': 0}
            if value == '':
                ret['desc'] = '미인증'
            elif value == 'wrong_id':
                ret['desc'] = '미인증 - 홈페이지 아이디가 없습니다.'
            elif value == 'too_many_sjva':
                ret['desc'] = '미인증 - 너무 많은 SJVA를 사용중입니다.'
            elif value == 'wrong_apikey':
                ret['desc'] = '미인증 - 홈페이지에 등록된 APIKEY와 다릅니다.'
            else:
                status = SystemLogicAuth.check_auth_status(value)
                if status is not None and status['ret']:
                    ret['ret'] = status['ret']
                    ret['desc'] = '인증되었습니다. (회원등급:%s, 포인트:%s)' % (status['level'], status['point'])
                    ret['level'] = status['level']
                    ret['point'] = status['point']
                else:
                    if retry:
                        SystemLogicAuth.do_auth()
                        #ModelSetting.set('auth_status', SystemLogicAuth.make_auth_status())
                        return SystemLogicAuth.get_auth_status(retry=False)
                    else:
                        ret['desc'] = '잘못된 값입니다. 다시 인증하세요.'
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def check_auth_status(value=None):
        try:
            
            from framework.common.util import AESCipher
            if app.config['config']['is_py2']:
                tmp = AESCipher.decrypt(value, mykey=(SystemLogicAuth.get_ip().encode('hex') + ModelSetting.get('auth_apikey').encode("hex")).zfill(32)[:32]).split('_')
            else:
                mykey=(codecs.encode(SystemLogicAuth.get_ip().encode(), 'hex').decode() + codecs.encode(ModelSetting.get('auth_apikey').encode(), 'hex').decode()).zfill(32)[:32].encode()
                logger.debug(mykey)
                tmp = AESCipher.decrypt(value, mykey=mykey).decode()
                tmp = tmp.split('_')
            ret = {}
            ret['ret'] = (ModelSetting.get('sjva_id') == tmp[0])
            ret['level'] = int(tmp[1])
            ret['point'] = int(tmp[2])
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def make_auth_status(level, point):
        try:
            from framework.common.util import AESCipher
            if app.config['config']['is_py2']:
                ret = AESCipher.encrypt(str('%s_%s_%s' % (ModelSetting.get('sjva_id'), level, point)), mykey=(codecs.encode(SystemLogicAuth.get_ip().encode(), 'hex') + codecs.encode(ModelSetting.get('auth_apikey').encode(), 'hex')).zfill(32)[:32])
            else:
                mykey=(codecs.encode(SystemLogicAuth.get_ip().encode(), 'hex').decode() + codecs.encode(ModelSetting.get('auth_apikey').encode(), 'hex').decode()).zfill(32)[:32].encode()
                ret =  AESCipher.encrypt(str('%s_%s_%s' % (ModelSetting.get('sjva_id'), level, point)), mykey=mykey)
            logger.debug(ret)
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @staticmethod
    def get_ip():
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        logger.debug('IP:%s', IP)
        return IP

    @staticmethod
    def do_auth():
        try:
            ret = {'ret':False, 'msg':'', 'level':0, 'point':0}
            apikey = ModelSetting.get('auth_apikey')
            user_id = ModelSetting.get('sjva_me_user_id')
            if len(apikey) != 10:
                ret['msg'] = 'APIKEY 문자 길이는 10자리여야합니다.'
                return ret
            if user_id == '':
                ret['msg'] = '홈페이지 ID가 없습니다.'
                return ret
   
            data = requests.post('https://sjva.me/sjva/auth.php', data={'apikey':apikey,'user_id':user_id, 'sjva_id':ModelSetting.get('sjva_id')}).json()
            if data['result'] == 'success':
                ret['ret'] = True
                ret['msg'] = u'총 %s개 등록<br>회원등급:%s, 포인트:%s' % (data['count'], data['level'], data['point'])
                ret['level'] = int(data['level'])
                ret['point'] = int(data['point'])
                ModelSetting.set('auth_status', SystemLogicAuth.make_auth_status(ret['level'], ret['point']))
            else:
                ModelSetting.set('auth_status', data['result'])
                tmp = SystemLogicAuth.get_auth_status(retry=False)
                ret['ret'] = tmp['ret']
                ret['msg'] = tmp['desc']
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            ret['msg'] = '인증 실패'
            ret['level'] = -1
            ret['point'] = -1
            ModelSetting.set('auth_status', SystemLogicAuth.make_auth_status(ret['level'], ret['point']))
            
            return ret



