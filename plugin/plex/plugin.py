# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import time
from datetime import datetime
import urllib
import json
# third-party
import requests
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify, session, send_from_directory 
from flask_socketio import SocketIO, emit, send
from flask_login import login_user, logout_user, current_user, login_required

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, path_data, socketio, SystemModelSetting
from framework.util import Util
from system.logic import SystemLogic

# 패키지
package_name = __name__.split('.')[0]
logger = get_logger(package_name)

from .model import ModelSetting
from .logic import Logic

#########################################################


#########################################################
# 플러그인 공용                                       
#########################################################
blueprint = Blueprint(package_name, package_name, url_prefix='/%s' % package_name, template_folder='templates')
menu = {
    'main' : [package_name, u'PLEX'],
    'sub' : [
        ['setting', u'설정'], ['plugin', u'플러그인'], ['tool', u'툴'], ['tivimate', u'Tivimate'], ['lc', u'Live Channels'], ['log', u'로그']
    ]
}
#['setting', '설정'], ['log', '로그']
#['setting', '설정'], ['tool', '툴'], ['log', '로그']
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
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


last_data = {}
#########################################################
# WEB Menu                                                                                      
#########################################################
@blueprint.route('/')
def home():
    return redirect('/%s/setting' % package_name)

@blueprint.route('/<sub>')
@login_required
def detail(sub): 
    logger.debug('DETAIL %s %s', package_name, sub)
    if sub == 'setting':
        setting_list = db.session.query(ModelSetting).all()
        arg = Util.db_list_to_dict(setting_list)
        return render_template('plex_setting.html', sub=sub, arg=arg)
    elif sub == 'plugin':
        setting_list = db.session.query(ModelSetting).all()
        arg = Util.db_list_to_dict(setting_list)
        return render_template('plex_plugin.html', sub=sub, arg=arg)
    elif sub == 'tool':
        return render_template('plex_tool.html')
    elif sub == 'lc':
        setting_list = db.session.query(ModelSetting).all()
        arg = Util.db_list_to_dict(setting_list)
        try:
            if arg['lc_json'] == '':
                arg['lc_json'] = "[]"
            #logger.debug(arg['lc_json'])
            tmp = json.loads(arg['lc_json'])
            #logger.debug(tmp)
            arg['lc_json'] = json.dumps(tmp, indent=4)
            #logger.debug(arg['lc_json'])
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            arg['lc_json'] = Logic.db_default['lc_json']
            tmp = json.loads(arg['lc_json'])
            arg['lc_json'] = json.dumps(tmp, indent=4)
        return render_template('plex_lc.html', arg=arg)
    elif sub == 'tivimate':
        setting_list = db.session.query(ModelSetting).all()
        arg = Util.db_list_to_dict(setting_list)
        try:
            if arg['tivimate_json'] == '':
                arg['tivimate_json'] = "[]"
            tmp = json.loads(arg['tivimate_json'])
            arg['tivimate_json'] = json.dumps(tmp, indent=4)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            arg['tivimate_json'] = Logic.db_default['tivimate_json']
            tmp = json.loads(arg['tivimate_json'])
            arg['tivimate_json'] = json.dumps(tmp, indent=4)
        return render_template('plex_tivimate.html', arg=arg)      
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
    if sub == 'server_list':
        try:
            ret = Logic.get_plex_server_list(request)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    # 설정 저장
    elif sub == 'setting_save':
        try:
            ret = Logic.setting_save(request)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    # 로그인->서버목록으로 연결
    elif sub == 'connect_by_name':
        try:
            ret = Logic.connect_plex_server_by_name(request)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    # Url 로 연결
    elif sub == 'connect_by_url':
        try:
            ret = Logic.connect_plex_server_by_url(request)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    # Url 로 연결
    elif sub == 'get_sjva_version':
        try:
            ret = Logic.get_sjva_plugin_version(request)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())       
    elif sub == 'get_sj_daum_version':
        try:
            ret = Logic.get_sj_daum_version(request)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())         


    ## 툴
    elif sub == 'analyze_show':
        try:
            ret = Logic.analyze_show(request)
            #마지막 데이터에 저장해놓음.
            last_data['analyze_show'] = ret
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    elif sub == 'analyze_show_event':
        try:
            key = request.args.get('key')
            return Response(Logic.analyze_show(key), mimetype="text/event-stream")
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    elif sub == 'load_tool':
        try:
            last_data['sections'] = Logic.load_section_list()
            last_data['plex_server_hash'] = Logic.get_server_hash()
            last_data['analyze_show'] = Logic.analyze_show_data
            return jsonify(last_data)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    #플러그인
    elif sub == 'send_command':
        try:
            ret = Logic.plungin_command(request)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

#########################################################
# API
#########################################################
@blueprint.route('/api/<sub>', methods=['GET', 'POST'])
def api(sub):
    if sub == 'm3u' or sub == 'get.php':
        try:
            from .logic_m3u import LogicM3U
            return LogicM3U.make_m3u()[0]
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    elif sub == 'xml' or sub == 'xmltv.php':
        try:
            from .logic_m3u import LogicM3U
            data = LogicM3U.make_m3u()[1]
            return Response(data, mimetype='application/xml')
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

@blueprint.route('/get.php')
def get_php():
    logger.debug('xtream codes server')
    logger.debug(request.args)
    return redirect('/plex/api/m3u')
    #return jsonify(user_ip)

@blueprint.route('/xmltv.php')
def xmltv_php():
    logger.debug('xtream codes server xmltv')
    logger.debug(request.args)
    return redirect('/plex/api/xml')

@blueprint.route('/player_api.php')
def player_api():
    pass

@blueprint.route('/login')
def login():
    logger.debug('xtream codes login')
    logger.debug(request.args)
    return jsonify('')

