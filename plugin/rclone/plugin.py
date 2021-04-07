# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import time
from datetime import datetime
import urllib
import json
import platform

# third-party
import requests
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify, session, send_from_directory 
from flask_socketio import SocketIO, emit, send
from flask_login import login_user, logout_user, current_user, login_required

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, path_data, socketio
from framework.util import Util, AlchemyEncoder
from system.model import ModelSetting as SystemModelSetting

# 로그
package_name = __name__.split('.')[0]
logger = get_logger(package_name)

# 패키지
from .model import ModelSetting
from .logic import Logic

#########################################################


#########################################################
# 플러그인 공용                                       
#########################################################
blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'build'), static_url_path='build')
menu = {
    'main' : [package_name, u'RClone'],
    'sub' : [
        ['setting', u'설정'], ['status', u'상태'], ['list', u'목록'], ['mount', u'Mount'], ['serve_setting', u'Serve'], ['log', u'로그']
    ]
}
 
#, 

def plugin_load():
    try:
        logger.debug('plugin_load:%s', package_name)
        Logic.plugin_load()
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def plugin_unload():
    try:
        logger.debug('plugin_unload:%s', package_name)
        Logic.plugin_unload()
        Logic.kill()
        
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

#########################################################
# WEB Menu                                                                                      
#########################################################
@blueprint.route('/')
def home():
    return redirect('/%s/list' % package_name)

@blueprint.route('/<sub>')
@login_required
def detail(sub): 
    logger.debug('DETAIL %s %s', package_name, sub)
    if sub == 'setting':
        setting_list = db.session.query(ModelSetting).all()
        arg = Util.db_list_to_dict(setting_list)
        arg['scheduler'] = str(scheduler.is_include(package_name))
        arg['is_running'] = str(scheduler.is_running(package_name))
        arg['path_rclone'] = Logic.path_rclone
        arg['default_rclone_setting'] = Logic.default_rclone_setting
        return render_template('rclone_setting.html', sub=sub, arg=arg)
    elif sub == 'status':
        return render_template('rclone_status.html')
    elif sub == 'list':
        return render_template('rclone_list.html')
    elif sub == 'log':
        return render_template('log.html', package=package_name)
    elif sub == 'mount':
        return redirect('/%s/mount_setting' % package_name)
    elif sub == 'mount_setting':
        arg = {}
        arg['option'] = '--allow-other --fast-list --drive-skip-gdocs --poll-interval=1m --buffer-size=32M --vfs-read-chunk-size=32M --vfs-read-chunk-size-limit 2048M --vfs-cache-mode writes --dir-cache-time=1m --log-level INFO'
        #if platform.system() != 'Windows':
        #    arg['option'] += ' --daemon'
        return render_template('%s_%s.html' % (package_name, sub), arg=arg)
    elif sub == 'serve_setting':
        arg = {}
        arg['option'] = '--user sjva --pass sjva --fast-list --drive-skip-gdocs --poll-interval=1m --buffer-size=32M --vfs-read-chunk-size=32M --vfs-read-chunk-size-limit 2048M --vfs-cache-mode writes --dir-cache-time=1m --log-level INFO'
        return render_template('%s_%s.html' % (package_name, sub), arg=arg)
    else:
        return blueprint.send_static_file(sub)
    return render_template('sample.html', title='%s - %s' % (package_name, sub))

HTTP_METHODS = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']

@blueprint.route('/<sub>/<path:path>', methods=HTTP_METHODS)
@login_required
def detail2(sub, path): 
    logger.debug('DETAIL2 %s %s', package_name, sub)
    if sub == 'static':
        return blueprint.send_static_file('static/' + path)
    else:
        if path is None:
            return blueprint.send_static_file(sub)
        else:
            url = 'http://127.0.0.1:5572/%s/%s' % (sub, path)
            #logger.debug(url)
            return proxy(request, url)
    return render_template('sample.html', title='%s - %s' % (package_name, sub))


def proxy(request, url):
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        #logger.debug(resp.status_code)
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                if name.lower() not in excluded_headers]
        response = Response(resp.text, resp.status_code, headers)
        return response

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
    if sub == 'rclone_version':
        try:
            ret = Logic.rclone_version()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    elif sub == 'send_to_command_plugin':
        try:
            c = request.form['command']
            ret = '%s --config %s %s' % (Logic.path_rclone, Logic.path_config, c)
            #ret = Logic.command(request)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    elif sub == 'load_remotes':
        try:
            ret = {}
            ret['remotes'] = Logic.load_remotes()
            ret['jobs'] = Logic.get_jobs()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    # 폴더목록
    elif sub == 'remote_ls':
        try:
            remote = request.form['remote']
            remote_path = request.form['remote_path']
            ret = '%s --config %s lsf "%s:%s" --max-depth 1' % (Logic.path_rclone, Logic.path_config, remote, remote_path)
            #import requests
            #data = {'command': ret}
            #logger.debug('remote_ls %s', ret)
            #url = request.host_url + '/command/api/command_return'
            
            #url = SystemModelSetting.get('ddns') + '/command/api/command_return'
            #logger.debug('url %s', url)
            #response = requests.post(url, data=data)
            #json = response.json()
            #return jsonify(response.json())
            import command 
            ret = command.LogicNormal.execute_thread_function(ret)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    # 로컬폴더목록
    elif sub == 'local_ls':
        try:
            local_path = request.form['local_path']
            logger.debug('local_path:%s', local_path)
            if not os.path.exists(local_path):
                ret = 'NOT EXIST'
            else:
                ret = os.listdir(local_path)
                if not ret:
                    ret = 'EMPTY'
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    # 작업 저장
    elif sub == 'job_save':
        try:
            ret = {}
            ret['ret'] = Logic.job_save(request)
            ret['remotes'] = Logic.load_remotes()
            ret['jobs'] = Logic.get_jobs()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    # 설정 저장(스케쥴링)
    elif sub == 'setting_save':
        ret = ModelSetting.setting_save(request)
        Logic.path_rclone = ModelSetting.get('rclone_bin_path')
        Logic.path_config = ModelSetting.get('rclone_config_path')
        return jsonify(ret)
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
    # 상태
    elif sub == 'status':
        try:
            pass
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    # 상태에서 stop
    elif sub == 'stop':
        try:
            ret = Logic.kill()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    # 상태에서 스케쥴러 stop
    elif sub == 'scheduler_stop':
        try:
            ret = Logic.kill()
            if scheduler.is_include(package_name):
                Logic.scheduler_stop()
                ret = 'success'
            else:
                ret = 'not_running'
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    # 설정 - 작업 탭 - 실행 버튼
    elif sub == 'execute_job':
        try:
            ret = Logic.execute_job(request)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    # 설정 - 작업 탭 - 모달 - 삭제 버튼
    elif sub == 'remove_job':
        try:
            ret = {}
            ret['ret'] = Logic.remove_job(request)
            ret['remotes'] = Logic.load_remotes()
            ret['jobs'] = Logic.get_jobs()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    # 설정 - 작업 탭 - 모달 - 삭제 버튼
    elif sub == 'filelist':
        try:
            ret = Logic.filelist(request)
            ret['jobs'] = Logic.get_jobs()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    elif sub == 'reset_db':
        try:
            ret = Logic.reset_db()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())  
    elif sub == 'get_log':
        try:
            return jsonify(Logic.get_log(request))
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
    #마운트
    elif sub == 'load_mounts':
        try:
            ret = {}
            ret['mounts'] = Logic.mount_list()
            ret['remotes'] = Logic.load_remotes()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    elif sub == 'mount_save':
        try:
            ret = {}
            ret['ret'] = Logic.mount_save(request)
            ret['remotes'] = Logic.load_remotes()
            ret['mounts'] = Logic.mount_list()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    elif sub == 'mount_execute':
        try:
            ret = {}
            #ret['ret'] = Logic.mount_execute(request)
            mount_id = request.form['id']
            ret['ret'] = Logic.mount_execute(mount_id)
            ret['remotes'] = Logic.load_remotes()
            ret['mounts'] = Logic.mount_list()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    elif sub == 'mount_stop':
        try:
            ret = {}
            ret['ret'] = Logic.mount_stop(request)
            ret['remotes'] = Logic.load_remotes()
            ret['mounts'] = Logic.mount_list()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    elif sub == 'mount_remove':
        try:
            ret = {}
            mount_id = request.form['id']
            Logic.mount_kill(mount_id)
            ret['ret'] = Logic.mount_remove(mount_id)
            ret['remotes'] = Logic.load_remotes()
            ret['mounts'] = Logic.mount_list()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    ####################################################
    # Serve
    ####################################################
    elif sub == 'load_serves':
        try:
            from .logic_serve import LogicServe
            ret = {}
            ret['serves'] = LogicServe.serve_list()
            ret['remotes'] = Logic.load_remotes()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    elif sub == 'serve_save':
        try:
            from .logic_serve import LogicServe
            ret = {}
            ret['ret'] = LogicServe.serve_save(request)
            ret['remotes'] = Logic.load_remotes()
            ret['serves'] = LogicServe.serve_list()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    elif sub == 'serve_execute':
        try:
            from .logic_serve import LogicServe
            ret = {}
            serve_id = request.form['id']
            ret['ret'] = LogicServe.serve_execute(serve_id)
            ret['remotes'] = Logic.load_remotes()
            ret['serves'] = LogicServe.serve_list()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    elif sub == 'serve_stop':
        try:
            from .logic_serve import LogicServe
            ret = {}
            ret['ret'] = LogicServe.serve_stop(request)
            ret['remotes'] = Logic.load_remotes()
            ret['serves'] = LogicServe.serve_list()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    elif sub == 'serve_remove':
        try:
            from .logic_serve import LogicServe
            ret = {}
            serve_id = request.form['id']
            LogicServe.serve_kill(serve_id)
            ret['ret'] = LogicServe.serve_remove(serve_id)
            ret['remotes'] = Logic.load_remotes()
            ret['serves'] = LogicServe.serve_list()
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())





sid_list = []
@socketio.on('connect', namespace='/%s' % package_name)
def connect():
    try:
        logger.debug('socket_connect')
        sid_list.append(request.sid)
        #emit('on_connect', Logic.current_data )
        tmp = None
        if Logic.current_data is not None:
            tmp = json.dumps(Logic.current_data, cls=AlchemyEncoder)
            tmp = json.loads(tmp)
        emit('on_connect', tmp, namespace='/%s' % package_name)

        #Logic.send_queue_start()
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


@socketio.on('disconnect', namespace='/%s' % package_name)
def disconnect():
    try:
        sid_list.remove(request.sid)
        logger.debug('socket_disconnect')
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def socketio_callback(cmd, data):
    if sid_list:
        tmp = json.dumps(data, cls=AlchemyEncoder)
        tmp = json.loads(tmp)
        socketio.emit(cmd, tmp , namespace='/%s' % package_name, broadcast=True)


"""

@blueprint.route('/rc/<path:path>',methods=['GET','POST','DELETE'])
def rc(path):
    url = 'http://127.0.0.1:5572/rc/' + path
    return proxy(request, url)

@blueprint.route('/core/<path:path>',methods=['GET','POST','DELETE'])
def core(path):
    url = 'http://127.0.0.1:5572/core/' + path
    return proxy(request, url)

def proxy(request, url):
    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.text, resp.status_code, headers)
    return response


# coding:utf-8
# Copyright 2011 litl, LLC. All Rights Reserved.
import httplib
import re
import urllib
import urlparse

from flask import Blueprint, request, Response, url_for
from werkzeug.datastructures import Headers
from werkzeug.exceptions import NotFound





HTML_REGEX = re.compile(r'((?:src|action|href)=["\'])/')
JQUERY_REGEX = re.compile(r'(\$\.(?:get|post)\(["\'])/')
JS_LOCATION_REGEX = re.compile(r'((?:window|document)\.location.*=.*["\'])/')
CSS_REGEX = re.compile(r'(url\(["\']?)/')

REGEXES = [HTML_REGEX, JQUERY_REGEX, JS_LOCATION_REGEX, CSS_REGEX]


def iterform(multidict):
    for key in multidict.keys():
        for value in multidict.getlist(key):
            yield (key.encode("utf8"), value.encode("utf8"))

def parse_host_port(h):
    host_port = h.split(":", 1)
    if len(host_port) == 1:
        return (h, 80)
    else:
        host_port[1] = int(host_port[1])
        return host_port


#@blueprint.route('/proxy/<host>/', methods=["GET", "POST"])
#@blueprint.route('/proxy/<host>/<path:file>', methods=["GET", "POST"])
@blueprint.route('/proxy/', methods=["GET", "POST"])
@blueprint.route('/proxy/<path:file>', methods=["GET", "POST"])
def proxy_request(file=""):
    #hostname, port = parse_host_port(host)
    hostname = 'http://sjva:sjva@127.0.0.1'
    host = 'http://sjva:sjva@127.0.0.1:9998'
    port = 9998

    # Whitelist a few headers to pass on
    request_headers = {}
    for h in ["Cookie", "Referer", "X-Csrf-Token"]:
        if h in request.headers:
            request_headers[h] = request.headers[h]

    if request.query_string:
        path = "/%s?%s" % (file, request.query_string)
    else:
        path = "/" + file

    if request.method == "POST":
        form_data = list(iterform(request.form))
        form_data = py_urllib.urlencode(form_data)
        request_headers["Content-Length"] = len(form_data)
    else:
        form_data = None

    conn = httplib.HTTPConnection(hostname, port)
    conn.request(request.method, path, body=form_data, headers=request_headers)
    resp = conn.getresponse()

    # Clean up response headers for forwarding
    response_headers = Headers()
    for key, value in resp.getheaders():
        if key in ["content-length", "connection", "content-type"]:
            continue

        if key == "set-cookie":
            cookies = value.split(",")
            [response_headers.add(key, c) for c in cookies]
        else:
            response_headers.add(key, value)

    # If this is a redirect, munge the Location URL
    if "location" in response_headers:
        redirect = response_headers["location"]
        parsed = urlparse.urlparse(request.url)
        redirect_parsed = urlparse.urlparse(redirect)

        redirect_host = redirect_parsed.netloc
        if not redirect_host:
            redirect_host = "%s:%d" % (hostname, port)

        redirect_path = redirect_parsed.path
        if redirect_parsed.query:
            redirect_path += "?" + redirect_parsed.query

        munged_path = url_for(".proxy_request",
                              host=redirect_host,
                              file=redirect_path[1:])

        url = "%s://%s%s" % (parsed.scheme, parsed.netloc, munged_path)
        response_headers["location"] = url

    # Rewrite URLs in the content to point to our URL scheme instead.
    # Ugly, but seems to mostly work.
    root = url_for(".proxy_request", host=host)
    contents = resp.read()
    for regex in REGEXES:
        contents = regex.sub(r'\1%s' % root, contents)

    flask_response = Response(response=contents,
                              status=resp.status,
                              headers=response_headers,
                              content_type=resp.getheader('content-type'))
    return flask_response
"""
