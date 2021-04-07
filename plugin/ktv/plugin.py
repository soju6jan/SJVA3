# -*- coding: utf-8 -*-
#########################################################
# python
import traceback
import logging

# third-party
import requests
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify
from flask_login import login_user, logout_user, current_user, login_required
# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler
from framework.util import Util

# 패키지
from .logic import Logic
from .model import ModelSetting
#########################################################


#########################################################
# 플러그인 공용      
#########################################################
package_name = __name__.split('.')[0]
logger = get_logger(package_name)

blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder='templates')
menu = {
    'main' : [package_name, u'국내TV'],
    'sub' : [
        ['setting', u'설정'], ['list', u'목록'], ['log', u'로그']
    ]
} 
# SJVA 에서 호출
def plugin_load():
    Logic.plugin_load()
    

def plugin_unload():
    pass


#########################################################
# WEB Menu   
#########################################################
@blueprint.route('/')
def home():
    return redirect('/%s/list' % package_name)

@blueprint.route('/<sub>')
@login_required
def detail(sub): 
    if sub == 'setting':
        setting_list = db.session.query(ModelSetting).all()
        arg = Util.db_list_to_dict(setting_list)
        arg['is_include'] = str(scheduler.is_include('ktv_process'))
        arg['is_running'] = str(scheduler.is_running('ktv_process'))
        return render_template('ktv_setting.html', sub=sub, arg=arg)
    elif sub == 'list':
        return render_template('ktv_list.html')
    elif sub == 'log':
        return render_template('log.html', package=package_name)
    return render_template('sample.html', title='%s - %s' % (package_name, sub))

#########################################################
# For UI                                                            
#########################################################
@blueprint.route('/ajax/<sub>', methods=['GET', 'POST'])
@login_required
def ajax(sub):
    logger.debug('AJAX %s %s', package_name, sub)
    # 설정 저장
    if sub == 'setting_save':
        try:
            ret = Logic.setting_save(request)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    elif sub == 'filelist':
        try:
            ret = Logic.filelist(request)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    # 스케쥴링 on / off
    elif sub == 'scheduler':
        try:
            go = request.form['scheduler']
            logger.debug('scheduler :%s', go)
            if go == 'true':
                Logic.scheduler_start()
            else:
                Logic.scheduler_stop()
            return jsonify(go)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return jsonify('fail')
    elif sub == 'library_save':
        try:
            ret = {}
            ret['ret'] = Logic.library_save(request)
            ret['library_list'] = [item.as_dict() for item in Logic.library_list()]
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return jsonify('fail')
    elif sub == 'library_list':
        try:
            ret = {}
            ret['library_list'] = [item.as_dict() for item in Logic.library_list()]
            
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return jsonify('fail')
    elif sub == 'library_remove':
        try:
            ret = {}
            ret['ret'] = Logic.library_remove(request)
            ret['library_list'] = [item.as_dict() for item in Logic.library_list()]
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return jsonify('fail')
    elif sub == 'reset_db':
        try:
            ret = Logic.reset_db()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return jsonify('fail')
            


#########################################################
# API - 외부
#########################################################
@blueprint.route('/api/<sub>', methods=['GET', 'POST'])
def api(sub):
    if sub == 'scan_completed':
        try:
            filename = request.form['filename']
            db_id = request.form['id']
            logger.debug('SCAN COMPLETED:%s %s', filename, db_id)
            Logic.receive_scan_result(db_id, filename)
            return 'ok'
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())