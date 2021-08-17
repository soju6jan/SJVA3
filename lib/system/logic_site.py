# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import logging
import platform
import time

# third-party
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify


# sjva 공용
from framework.logger import get_logger
from framework import path_app_root, path_data, socketio, scheduler
from framework.job import Job


# 패키지
from .plugin import logger, package_name
from .model import ModelSetting


class SystemLogicSite(object):
    # 매번 split 하기 머해서 
    daum_cookie = None

    @staticmethod
    def process_ajax(sub, req):
        try:
            ret = {}
            if sub == 'site_daum_test':
                site_daum_test = req.form['site_daum_test']
                ModelSetting.set('site_daum_test', site_daum_test)
                from framework.common.daum import DaumTV, MovieSearch
                ret['TV'] = DaumTV.get_daum_tv_info(site_daum_test)
                if ret['TV'] is not None and 'episode_list' in ret['TV']:
                    del ret['TV']['episode_list']
                ret['MOVIE'] = MovieSearch.search_movie(site_daum_test, -1)
                return jsonify(ret)
            elif sub == 'site_daum_cookie_refresh':
                ret = SystemLogicSite.get_daum_cookie_by_selenium(notify=True)
                return jsonify(ret)
            elif sub == 'scheduler':
                go = req.form['scheduler']
                if go == 'true':
                    SystemLogicSite.scheduler_start()
                else:
                    SystemLogicSite.scheduler_stop()
                return jsonify(go)
            elif sub == 'tving_login':
                try:
                    import framework.tving.api as Tving
                    token = Tving.do_login(req.form['tving_id'], req.form['tving_pw'], req.form['tving_login_type'])
                    if token is None:
                        ret['ret'] = False
                    else:
                        ret['ret'] = True
                        ret['token'] = token
                    return jsonify(ret)
                except Exception as e: 
                    logger.error('Exception:%s', e)
                    logger.error(traceback.format_exc())
            elif sub == 'tving_deviceid':
                try:
                    import framework.tving.api as Tving
                    device_list = Tving.get_device_list(req.form['tving_token'])
                    if device_list is None:
                        ret['ret'] = False
                    else:
                        ret['ret'] = True
                        ret['device_list'] = device_list
                    return jsonify(ret)
                except Exception as e: 
                    logger.error('Exception:%s', e)
                    logger.error(traceback.format_exc())
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            ret['ret'] = False
            ret['log'] = str(traceback.format_exc())
        return jsonify(ret)

    @staticmethod
    def process_api(sub, req):
        ret = {}
        try:
            if sub == 'daum_cookie':
                return ModelSetting.get('site_daum_cookie')
                
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
            ret['ret'] = 'exception'
            ret['data'] = str(exception)
        return jsonify(ret)
    ##########################################################################

    @staticmethod
    def plugin_load():
        return
        SystemLogicSite.get_daum_cookies(force=True)
        if ModelSetting.get_bool('site_daum_auto_start'):
            SystemLogicSite.scheduler_start()

    @staticmethod
    def scheduler_start():
        job = Job(package_name, '%s_site' % package_name, ModelSetting.get('site_daum_interval'), SystemLogicSite.scheduler_function, u"Daum cookie refresh", False)
        scheduler.add_job_instance(job)
    
    @staticmethod
    def scheduler_stop():
        scheduler.remove_job('%s_site' % package_name)
           

    @staticmethod
    def scheduler_function():
        try:
            data = SystemLogicSite.get_daum_cookie_by_selenium()
            if data['ret']:
                ModelSetting.set('site_daum_cookie', data['data'])
                SystemLogicSite.get_daum_cookies(force=True)
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())



    @staticmethod 
    def get_daum_cookie_by_selenium(notify=False):
        try:
            ret = {}
            ret['ret'] = False
            from .logic_selenium import SystemLogicSelenium
            if notify:
                data = {'type':'success', 'msg' : u'<strong>사이트 접속중입니다.</strong>'}
                socketio.emit("notify", data, namespace='/framework', broadcast=True)    
            SystemLogicSelenium.get_pagesoruce_by_selenium('https://www.daum.net', '//*[@id="daumFoot"]/div/a[1]/img')
            if notify:
                data = {'type':'success', 'msg' : u'쿠키 확인'}
                socketio.emit("notify", data, namespace='/framework', broadcast=True)    
            driver = SystemLogicSelenium.get_driver()
            cookies = driver.get_cookies()
            for tmp in cookies:
                if tmp['name'] == 'TIARA':
                    ret['ret'] = True
                    ret['data'] = 'TIARA=%s' % tmp['value']
                    return ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())    
        return ret



    @staticmethod
    def get_daum_cookies(force=False):
        try:
            if SystemLogicSite.daum_cookie is None or force:
                ret = {}
                tmp = ModelSetting.get('site_daum_cookie')
                tmps = tmp.split(';')
                for t in tmps:
                    t2 = t.split('=')
                    if len(t2) == 2:
                        ret[t2[0]] = t2[1]
                SystemLogicSite.daum_cookie = ret
            return SystemLogicSite.daum_cookie
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return {'TIARA':'gaXEIPluo-wWAFlwZN6l8gN3yzhkoo_piP.Kymhuy.6QBt4Q6.cRtxbKDaWpWajcyteRHzrlTVpJRxLjwLoMvyYLVi_7xJ1L'}


    daum_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cookie' : 'over18=1;age_check_done=1;',
    } 

    @classmethod 
    def get_tree_daum(cls, url, post_data=None):
        from lxml import html
        from framework import SystemModelSetting
        text = cls.get_text(url, proxy_url=SystemModelSetting.get('site_daum_proxy'), headers=SystemLogicSite.daum_headers, post_data=post_data, cookies=SystemLogicSite.get_daum_cookies())
        if text is None:
            return
        return html.fromstring(text)
    
    @classmethod 
    def get_text_daum(cls, url, post_data=None):
        from system.logic_site import SystemLogicSite
        from framework import SystemModelSetting
        res = cls.get_response(url, proxy_url=SystemModelSetting.get('site_daum_proxy'), headers=SystemLogicSite.daum_headers, post_data=post_data, cookies=SystemLogicSite.get_daum_cookies())
        return res.text


    @classmethod 
    def get_response_daum(cls, url, post_data=None):
        from system.logic_site import SystemLogicSite
        from framework import SystemModelSetting
        res = cls.get_response(url, proxy_url=SystemModelSetting.get('site_daum_proxy'), headers=SystemLogicSite.daum_headers, post_data=post_data, cookies=SystemLogicSite.get_daum_cookies())
        return res


    @classmethod 
    def get_response(cls, url, proxy_url=None, headers=None, post_data=None, cookies=None):
        import requests
        proxies = None
        if proxy_url is not None and proxy_url != '':
            proxies = {"http"  : proxy_url, "https" : proxy_url}
        if headers is None:
            headers = SystemLogicSite.default_headers
        if post_data is None:
            res = requests.get(url, headers=headers, proxies=proxies, cookies=cookies)
        else:
            res = requests.post(url, headers=headers, proxies=proxies, data=post_data, cookies=cookies)
        return res