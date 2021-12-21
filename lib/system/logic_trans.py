# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys
import traceback
import json

# third-party
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify


# sjva 공용
from framework.logger import get_logger
from framework import path_app_root, py_urllib2, py_urllib, app
from framework.util import Util

# 패키지
from .plugin import package_name, logger
from .model import ModelSetting


class SystemLogicTrans(object):
    @staticmethod
    def process_ajax(sub, req):
        try:
            if sub == 'trans_test':
                ret = SystemLogicTrans.trans_test(req)
                return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def process_api(sub, req):
        ret = {}
        try:
            if sub == 'do':
                text = req.args.get('text')
                source = req.args.get('source')
                target = req.args.get('target')
                if source is None:
                    source = 'ja'
                if target is None:
                    target = 'ko'
                tmp = SystemLogicTrans.trans(text, source=source, target=target)
                if tmp is not None:
                    ret['ret'] = 'success'
                    ret['data'] = tmp
                else:
                    ret['ret'] = 'fail'
                    ret['data'] = ''
                
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
            ret['ret'] = 'exception'
            ret['data'] = str(exception)
        return jsonify(ret)
    ##########################################################################

    @staticmethod
    def trans_test(req):
        try:
            source = req.form['source']
            try:
                trans_type = req.form['trans_type']
            except:
                trans_type = '5'
                
            logger.debug('trans_type:%s source:%s', trans_type, source)
            if trans_type == '0':
                return source
            elif trans_type == '1':
                return SystemLogicTrans.trans_google(source) 
            elif trans_type == '2':
                return SystemLogicTrans.trans_papago(source)
            elif trans_type == '3':
                return SystemLogicTrans.trans_google_web(source)
            elif trans_type == '4':
                return SystemLogicTrans.trans_google_web2(source)
            elif trans_type == '5':
                return SystemLogicTrans.trans_papago_web(source)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False

    @staticmethod
    def trans(text, source='ja', target='ko'):
        try:
            trans_type = ModelSetting.get('trans_type')
            if trans_type == '0':
                return text
            elif trans_type == '1':
                return SystemLogicTrans.trans_google(text, source, target) 
            elif trans_type == '2':
                return SystemLogicTrans.trans_papago(text, source, target) 
            elif trans_type == '3':
                return SystemLogicTrans.trans_google_web(text, source, target) 
            elif trans_type == '4':
                return SystemLogicTrans.trans_google_web2(text, source, target) 
            elif trans_type == '5':
                return SystemLogicTrans.trans_papago_web(text, source, target)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            


    @staticmethod
    def trans_papago(text, source='ja', target='ko'):
        trans_papago_key = ModelSetting.get_list('trans_papago_key')
        
        for tmp in trans_papago_key:
            client_id, client_secret = tmp.split(',')
            try:
                if client_id == '' or client_id is None or client_secret == '' or client_secret is None: 
                    return text
                data = "source=%s&target=%s&text=%s" % (source, target, text)
                url = "https://openapi.naver.com/v1/papago/n2mt"
                requesturl = py_urllib2.Request(url)
                requesturl.add_header("X-Naver-Client-Id", client_id)
                requesturl.add_header("X-Naver-Client-Secret", client_secret)
                response = py_urllib2.urlopen(requesturl, data = data.encode("utf-8"))
                if sys.version_info[0] == 2:
                    data = json.load(response, encoding='utf8')
                else:
                    data = json.load(response)
                rescode = response.getcode()
                if rescode == 200:
                    return data['message']['result']['translatedText']
                else:
                    continue
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())                
        return text
    
    
    '''
    source 값은 필요 없지만 호환성을 위해서 남겨 놓음.
    '''
    @staticmethod
    def trans_papago_web(text, source='ja', target='ko'):
        if app.config['config']['is_py2']:
            return u'Python >=3 '
        try:
            from papagopy import Papagopy
            translator = Papagopy()
            translate_text = translator.translate(text, sourceCode=source, targetCode=target)
            logger.error("파파고 웹은 사용 중지 되었습니다. 다른 번역으로 변경하세요.")
            return translate_text
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return text


    @staticmethod
    def trans_name(name):
        trans_papago_key = ModelSetting.get_list('trans_papago_key')
        
        for tmp in trans_papago_key:
            client_id, client_secret = tmp.split(',')
            try:
                if client_id == '' or client_id is None or client_secret == '' or client_secret is None: 
                    return
                logger.debug(name)
                encText = py_urllib.quote(str(name))
                logger.debug(encText)
                url = "https://openapi.naver.com/v1/krdict/romanization?query=" + encText
                requesturl = py_urllib2.Request(url)
                requesturl.add_header("X-Naver-Client-Id", client_id)
                requesturl.add_header("X-Naver-Client-Secret", client_secret)
                response = py_urllib2.urlopen(requesturl)
                if sys.version_info[0] == 2:
                    data = json.load(response, encoding='utf8')
                else:
                    data = json.load(response)
                rescode = response.getcode()
                logger.debug(data)
                if rescode == 200:
                    return data
                else:
                    continue
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())                
        return        



    @staticmethod
    def trans_google(text, source='ja', target='ko'):
        try:
            google_api_key = ModelSetting.get('trans_google_api_key')
            if google_api_key == '' or google_api_key is None:
                return text
            data = "key=%s&source=%s&target=%s&q=%s" % (google_api_key, source, target, text)
            url = "https://www.googleapis.com/language/translate/v2"
            requesturl = py_urllib2.Request(url)
            requesturl.add_header("X-HTTP-Method-Override", "GET")

            response = py_urllib2.urlopen(requesturl, data = data.encode("utf-8"))
            if sys.version_info[0] == 2:
                data = json.load(response, encoding='utf8')
            else:
                data = json.load(response)
            rescode = response.getcode()
            if rescode == 200:
                return data['data']['translations'][0]['translatedText']
            else:
                return text
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return text


    @staticmethod
    def trans_google_web(text, source='ja', target='ko'):
        if app.config['config']['is_py2']:
            return u'Python >=3.6'
        """
        try:
            from google_trans_new import google_translator
        except:
            try: os.system("{} install google_trans_new".format(app.config['config']['pip']))
            except: pass
            from google_trans_new import google_translator
        """
        from google_trans_new_embed import google_translator
        try:
            translator = google_translator()  
            translate_text = translator.translate(text, lang_src=source, lang_tgt=target)
            return translate_text
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return text

    @staticmethod
    def trans_google_web2(text, source='ja', target='ko'):
        try:
            import requests
            url = 'https://translate.google.com/translate_a/single'
            headers = {'User-Agent': 'GoogleTranslate/6.27.0.08.415126308 (Linux; U; Android 7.1.2; PIXEL 2 XL)'}
            params = {'q': text, 'sl': source, 'tl': target,
                    'hl': 'ko-KR', 'ie': 'UTF-8', 'oe': 'UTF-8', 'client': 'at',
                    'dt': ('t', 'ld', 'qca', 'rm', 'bd', 'md', 'ss', 'ex', 'sos')}
            
            response = requests.get(url, params=params, headers=headers).json()
            translated_text = ''
            for sentence in response[0][:-1]:
                translated_text += sentence[0].strip() + ' '
            return translated_text
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return text

    

    @staticmethod
    def get_trans_func(index):
        index = str(index)
        if index == '1':
            return SystemLogicTrans.trans_google
        elif index == '2':
            return SystemLogicTrans.trans_papago
        elif index == '3':
            return SystemLogicTrans.trans_google_web
        elif index == '4':
            return SystemLogicTrans.trans_google_web2
        elif index == '5':
            return SystemLogicTrans.trans_papago_web
        