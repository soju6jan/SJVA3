# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys
import traceback
import json

# third-party
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify

# sjva 공용
from framework import app, path_app_root, py_urllib2, py_urllib, Util

# 패키지
from .plugin import package_name, logger
from .model import ModelSetting

class SystemLogicToolDecrypt(object):
    @staticmethod
    def process_ajax(sub, req):
        try:
            if sub == 'crypt_test':
                ret = SystemLogicToolDecrypt.crypt_test(req)
                return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    ##########################################################################

    @staticmethod
    def crypt_test(req):
        try:
            mode = req.form['mode']
            word = req.form['word']
            if app.config['config']['is_py2']:
                word = word.encode('utf8')
            
            logger.debug(mode)
            logger.debug(word)
            from tool_base import ToolAESCipher
            mykey = None
            if ModelSetting.get_bool('tool_crypt_use_user_key'):
                mykey = ModelSetting.get('tool_crypt_user_key').lower().zfill(32)
                if app.config['config']['is_py2']:
                    mykey = mykey.encode('utf8')
                if len(mykey) > 32:
                    mykey = mykey[:32]
            logger.debug(mykey)
            
            if mode == 'encrypt':
                ModelSetting.set('tool_crypt_encrypt_word', u'%s' % word)
                ret = {'ret':'success', 'data':ToolAESCipher.encrypt(word, mykey=mykey)}
            elif mode == 'decrypt':
                ModelSetting.set('tool_crypt_decrypt_word',  u'%s' % word)
                ret = {'ret':'success', 'data':ToolAESCipher.decrypt(word, mykey=mykey)}
            logger.debug(ret)
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return {'ret':'exception', 'data':str(exception)}
