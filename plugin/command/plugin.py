# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import time
from datetime import datetime
import urllib
# third-party
import requests
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify, session, send_from_directory
from flask_socketio import SocketIO, emit, send
from flask_login import login_user, logout_user, current_user, login_required
# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, path_data, socketio, check_api
from framework.util import Util

# 패키지
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
from .logic_normal import LogicNormal
from .model import ModelCommand
#########################################################


#########################################################
# 플러그인 공용                                       
#########################################################
blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

menu = {
    'main' : [package_name, u'Command'],
    'sub' : [
        ['setting', u'작업설정'], ['log', u'로그']
    ], 
} 

plugin_info = {
    'version' : '1.0',
    'name' : 'command',
    'category_name' : 'system',
    'developer' : 'soju6jan',
    'description' : 'Command',
    'home' : 'https://github.com/soju6jan/command',
    'more' : '',
}


def plugin_load():
    LogicNormal.plugin_load()

def plugin_unload():
    LogicNormal.plugin_unload()
    
#########################################################
# WEB Menu                               
#########################################################
@blueprint.route('/')
def home():
    return redirect('/%s/setting' % package_name)

@blueprint.route('/<sub>', methods=['GET', 'POST'])
@login_required
def first_menu(sub): 
    try:
        if sub == 'setting':
            arg = {}
            arg['command_file_list'] = LogicNormal.command_file_list()
            arg['package_name'] = package_name
            arg['command_by_plugin'] = ''
            if 'command_by_plugin' in request.form:
                arg['command_by_plugin'] = request.form['command_by_plugin']
            return render_template('%s_setting.html' % package_name, arg=arg)
        elif sub == 'log':
            return render_template('log.html', package=package_name)
        return render_template('sample.html', title='%s - %s' % (package_name, sub))
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())    

#########################################################
# For UI                                                            
#########################################################
@blueprint.route('/ajax/<sub>', methods=['GET', 'POST'])
@login_required
def ajax(sub):
    logger.debug('AJAX %s %s', package_name, sub)
    try:
        if sub == 'foreground_command':
            command = request.form['command']
            ret = LogicNormal.foreground_command(command)
            return jsonify(ret)
        elif sub == 'foreground_command_close':
            ret = LogicNormal.foreground_command_close()
            return jsonify(ret)
        elif sub == 'job_new':
            ret = {}
            ret['ret'] = ModelCommand.job_new(request)
            ret['list'] = ModelCommand.job_list()
            return jsonify(ret)
        elif sub == 'job_save':
            ret = {}
            ret['ret'] = ModelCommand.job_save(request)
            ret['list'] = ModelCommand.job_list()
            return jsonify(ret)
        elif sub == 'scheduler_switch':
            ret = {}
            ret['ret'] = LogicNormal.scheduler_switch0(request)
            ret['list'] = ModelCommand.job_list()
            return jsonify(ret)
        elif sub == 'job_remove':
            ret = {}
            ret['ret'] = ModelCommand.job_remove(request)
            ret['list'] = ModelCommand.job_list()
            return jsonify(ret)
        elif sub == 'job_log_show':
            ret = {}
            job_id = request.form['job_id']
            ret['filename'] = '%s_%s.log' % (package_name, job_id)
            ret['ret'] = os.path.exists(os.path.join(path_data, 'log', ret['filename']))
            return jsonify(ret)
        elif sub == 'job_background':
            ret = {}
            job_id = request.form['job_id']
            ret['ret'] = LogicNormal.job_background(job_id)
            return jsonify(ret)
        elif sub == 'job_file_edit':
            ret = {}
            job_id = request.form['job_id']
            job = ModelCommand.get_job_by_id(job_id)
            import framework.common.util as CommonUtil
            ret['data'] = CommonUtil.read_file(job.filename) 
            ret['ret'] = True
            return jsonify(ret)
        elif sub == 'file_save':
            ret = {}
            job_id = request.form['file_job_id']
            logger.debug(job_id)
            data = request.form['file_textarea']
            job = ModelCommand.get_job_by_id(job_id)
            import framework.common.util as CommonUtil
            logger.debug(job.filename)
            CommonUtil.write_file(data, job.filename) 
            try:
                os.system('dos2unix %s' % job.filename)
            except Exception as exception: 
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())         
            ret['ret'] = True
            return jsonify(ret)
        elif sub == 'foreground_command_by_job':
            ret = {}
            job_id = request.form['job_id']
            job = ModelCommand.get_job_by_id(job_id)
            ret['ret'] = LogicNormal.foreground_command(job.command, job_id=job_id)
            return jsonify(ret)
        elif sub == 'process_close':
            ret = {'ret':'fail'}
            job_id = request.form['job_id']
            if LogicNormal.process_close(LogicNormal.process_list[int(job_id)]):
                ret['ret'] = 'success'
            return jsonify(ret)


        elif sub == 'send_process_command':
            ret = LogicNormal.send_process_command(request)
            return jsonify(ret)
        elif sub == 'command_list':
            ret = {}
            ret['list'] = ModelCommand.job_list()
            return jsonify(ret)
        elif sub == 'save':
            ret = {}
            ret['ret'] = LogicNormal.save(request)
            ret['list'] = ModelCommand.job_list()
            return jsonify(ret)
        
        
        
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc()) 


#########################################################
# API                                                          
#########################################################
"""
@blueprint.route('/api/<sub>', methods=['POST'])
def api(sub):
    logger.debug('API %s %s', package_name, sub)
    try:
        if sub == 'command':
            arg = {}
            command = request.form['command']
            arg['command_file_list'] = LogicNormal.command_file_list()
            arg['api_command'] = command
            return render_template('%s_setting.html' % package_name, arg=arg, mode="api")
        elif sub == 'command_return':
            command = request.form['command']
            logger.debug('command_return :%s', command)
            return jsonify(LogicNormal.execute_thread_function(command))
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
"""


#########################################################
# API
#########################################################
@blueprint.route('/api/<sub>', methods=['GET', 'POST'])
@check_api
def api(sub):
    ret = {}
    try:
        if sub == 'command_add':
            filename = request.form['filename']
            file_url = request.form['file_url']
            logger.debug(filename)
            logger.debug(file_url)
            r = requests.get(file_url)

            download_path = os.path.join(path_data, 'command', filename)
            update = False
            if os.path.exists(download_path):
                os.remove(download_path)
                update = True
            import framework.common.util as CommonUtil
            #open(download_path, 'wb').write(r.text)
            CommonUtil.write_file(r.text, download_path)
            try:
                os.system('dos2unix %s' % download_path)
            except Exception as exception: 
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc()) 
            try:
                os.system('chmod 777 %s' % download_path)
            except Exception as exception: 
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc()) 
            ret['ret'] = 'success'
            if update:
                ret['log'] = u'정상적으로 설치하였습니다.<br>파일을 업데이트 하였습니다.'
            else:
                ret['log'] = u'정상적으로 설치하였습니다.'
        elif sub == 'execute':
            command_id = request.args.get('id')
            mode = request.args.get('mode')
            if mode is None:
                mode = 'json'
            kwargs = {}
            for key, value in request.args.items():
                if key in ['apikey', 'mode']:
                    continue
                if key not in kwargs:
                    kwargs[key] = value
            ret = LogicNormal.execute_thread_function_job(int(command_id), **kwargs)
            if mode == 'json':
                return jsonify(ret)
            elif mode == 'return':
                return str(ret)
            elif mode == 'redirect':
                return redirect(ret)



    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())  
        ret['ret'] = 'exception'
        ret['log'] = str(exception)
    return jsonify(ret)


@socketio.on('connect', namespace='/%s' % package_name)
def connect():
    try:
        logger.debug('socket_connect')
        LogicNormal.send_queue_start()
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


@socketio.on('disconnect', namespace='/%s' % package_name)
def disconnect():
    try:
        logger.debug('socket_disconnect')
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

