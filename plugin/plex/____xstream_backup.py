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
from framework.util import Util, AlchemyEncoder
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
    'main' : [package_name, 'PLEX'],
    'sub' : [
        ['setting', '설정'], ['plugin', '플러그인'], ['tool', '툴'], ['tivimate', 'Tivimate'], ['lc', 'Live Channels'], ['log', '로그']
    ]
}
#['setting', '설정'], ['log', '로그']
#['setting', '설정'], ['tool', '툴'], ['log', '로그']
def plugin_load():
    try:
        logger.debug('plugin_load:%s', package_name)
        Logic.plugin_load()
    except Exception as e: 
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())

def plugin_unload():
    try:
        logger.debug('plugin_unload:%s', package_name)
        Logic.plugin_unload()
    except Exception as e: 
        logger.error('Exception:%s', e)
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
        except Exception as e: 
            logger.error('Exception:%s', e)
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
        except Exception as e: 
            logger.error('Exception:%s', e)
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
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    # 설정 저장
    elif sub == 'setting_save':
        try:
            ret = Logic.setting_save(request)
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    # 로그인->서버목록으로 연결
    elif sub == 'connect_by_name':
        try:
            ret = Logic.connect_plex_server_by_name(request)
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    # Url 로 연결
    elif sub == 'connect_by_url':
        try:
            ret = Logic.connect_plex_server_by_url(request)
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    # Url 로 연결
    elif sub == 'get_sjva_version':
        try:
            ret = Logic.get_sjva_plugin_version(request)
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())       
    elif sub == 'get_sj_daum_version':
        try:
            ret = Logic.get_sj_daum_version(request)
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())         


    ## 툴
    elif sub == 'analyze_show':
        try:
            ret = Logic.analyze_show(request)
            #마지막 데이터에 저장해놓음.
            last_data['analyze_show'] = ret
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    elif sub == 'analyze_show_event':
        try:
            key = request.args.get('key')
            return Response(Logic.analyze_show(key), mimetype="text/event-stream")
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    elif sub == 'load_tool':
        try:
            last_data['sections'] = Logic.load_section_list()
            last_data['plex_server_hash'] = Logic.get_server_hash()
            last_data['analyze_show'] = Logic.analyze_show_data
            return jsonify(last_data)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    #플러그인
    elif sub == 'send_command':
        try:
            ret = Logic.plungin_command(request)
            return jsonify(ret)
        except Exception as e: 
            logger.error('Exception:%s', e)
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
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    elif sub == 'xml' or sub == 'xmltv.php':
        try:
            from .logic_m3u import LogicM3U
            data = LogicM3U.make_m3u()[1]
            return Response(data, mimetype='application/xml')
        except Exception as e: 
            logger.error('Exception:%s', e)
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

    """
    // For Live Streams the main format is
	// http(s)://domain:port/live/username/password/streamID.ext ( In allowed_output_formats element you have the available ext )
	// For VOD Streams the format is:
	// http(s)://domain:port/movie/username/password/streamID.ext ( In target_container element you have the available ext )
	// For Series Streams the format is
	// http(s)://domain:port/series/username/password/streamID.ext ( In target_container element you have the available ext )
    """


    logger.debug('xtream codes player_api')
    logger.debug(request.args)
    if request.args.get('action') == 'get_live_categories':
        output = [{"category_id":"70","category_name":"A1 TV","parent_id":0},{"category_id":"64","category_name":"Afghanistan","parent_id":0},{"category_id":"43","category_name":"Africa","parent_id":0},{"category_id":"97","category_name":"Africa VIP","parent_id":0},{"category_id":"5","category_name":"Albania","parent_id":0},{"category_id":"3","category_name":"Arab Countries","parent_id":0},{"category_id":"342","category_name":"Armenia","parent_id":0},{"category_id":"26","category_name":"Australia","parent_id":0},{"category_id":"65","category_name":"Austria","parent_id":0},{"category_id":"63","category_name":"Azerbaijan","parent_id":0},{"category_id":"19","category_name":"Belgium","parent_id":0},{"category_id":"44","category_name":"Brazil","parent_id":0},{"category_id":"32","category_name":"Bulgaria","parent_id":0},{"category_id":"110","category_name":"Canada","parent_id":0},{"category_id":"23","category_name":"China","parent_id":0},{"category_id":"24","category_name":"Czech Republic","parent_id":0},{"category_id":"40","category_name":"Denmark","parent_id":0},{"category_id":"69","category_name":"Estonia","parent_id":0},{"category_id":"6","category_name":"ex-Yu","parent_id":0},{"category_id":"104","category_name":"ex-Yu VIP","parent_id":0},{"category_id":"42","category_name":"Finland","parent_id":0},{"category_id":"34","category_name":"For Adults","parent_id":0},{"category_id":"10","category_name":"France","parent_id":0},{"category_id":"4","category_name":"Germany","parent_id":0},{"category_id":"344","category_name":"24\/7 Germany","parent_id":0},{"category_id":"33","category_name":"Greece","parent_id":0},{"category_id":"46","category_name":"Hungary","parent_id":0},{"category_id":"139","category_name":"Iceland","parent_id":0},{"category_id":"27","category_name":"India","parent_id":0},{"category_id":"140","category_name":"India VIP","parent_id":0},{"category_id":"30","category_name":"Indonesia","parent_id":0},{"category_id":"13","category_name":"Iran","parent_id":0},{"category_id":"60","category_name":"Israel","parent_id":0},{"category_id":"8","category_name":"Italia","parent_id":0},{"category_id":"22","category_name":"Japan","parent_id":0},{"category_id":"21","category_name":"Korea","parent_id":0},{"category_id":"31","category_name":"Kurdistan","parent_id":0},{"category_id":"68","category_name":"Latin America","parent_id":0},{"category_id":"141","category_name":"Lithuania","parent_id":0},{"category_id":"35","category_name":"Macedonia","parent_id":0},{"category_id":"20","category_name":"Malaysia","parent_id":0},{"category_id":"39","category_name":"Malta","parent_id":0},{"category_id":"7","category_name":"Netherland","parent_id":0},{"category_id":"41","category_name":"Norway","parent_id":0},{"category_id":"25","category_name":"Pakistan","parent_id":0},{"category_id":"146","category_name":"Philippines","parent_id":0},{"category_id":"15","category_name":"Poland","parent_id":0},{"category_id":"36","category_name":"Portugal","parent_id":0},{"category_id":"346","category_name":"Portugal - Canais 24\/7","parent_id":0},{"category_id":"14","category_name":"Romania","parent_id":0},{"category_id":"62","category_name":"Russian","parent_id":0},{"category_id":"265","category_name":"Scandinavian","parent_id":0},{"category_id":"28","category_name":"Singapore","parent_id":0},{"category_id":"72","category_name":"Slovenia","parent_id":0},{"category_id":"16","category_name":"Spain","parent_id":0},{"category_id":"18","category_name":"Sweden","parent_id":0},{"category_id":"17","category_name":"Switzerland","parent_id":0},{"category_id":"38","category_name":"Thailand","parent_id":0},{"category_id":"11","category_name":"Turkey","parent_id":0},{"category_id":"343","category_name":"UHD 4K","parent_id":0},{"category_id":"9","category_name":"United Kingdom","parent_id":0},{"category_id":"105","category_name":"United Kingdom VIP","parent_id":0},{"category_id":"345","category_name":"24\/7 English","parent_id":0},{"category_id":"12","category_name":"United States","parent_id":0},{"category_id":"106","category_name":"United States VIP","parent_id":0},{"category_id":"37","category_name":"Viet Nam","parent_id":0},{"category_id":"71","category_name":"VIP","parent_id":0},{"category_id":"138","category_name":"VIP Sports","parent_id":0}]


        return jsonify(output)
    elif request.args.get('action') is None:
        output = {'user_info':{}}
        output['server_info'] = {'url' : SystemModelSetting.get('ddns') + '/plex', 'port':'', 'server_protocol':'http', 'timezone':'', 'timestamp_now':'', 'time_now':'', 'rtmp_port':'', 'https_port':''}
        output['user_info']['username'] = 'test'
        output['user_info']['password'] = 'test'
        output['user_info']['auth'] = 1
        output['user_info']['message'] = ''
        output['user_info']['status'] = 'Active'

        output['user_info']['exp_date'] = ''
        output['user_info']['is_trial'] = ''
        output['user_info']['active_cons'] = ''
        output['user_info']['created_at'] = ''
        output['user_info']['max_connections'] = ''
        output['user_info']['allowed_output_formats'] = ''
        #{"user_info":{"username":"zqcAXZEvlW","password":"ATiD6d7K3H","message":"","auth":1,"status":"Active","exp_date":"1632734599","is_trial":"0","active_cons":"1","created_at":"1585304571","max_connections":"1","allowed_output_formats":["m3u8","ts","rtmp"]},"server_info":{"url":"portal.geniptv.com","port":"8080","https_port":"25463","server_protocol":"http","rtmp_port":"25462","timezone":"UTC","timestamp_now":1602768143,"time_now":"2020-10-15 13:22:23","process":true}}
        #output = {"user_info":{"username":"zqcAXZEvlW","password":"ATiD6d7K3H","message":"","auth":1,"status":"Active","exp_date":"1632734599","is_trial":"0","active_cons":"1","created_at":"1585304571","max_connections":"1","allowed_output_formats":["m3u8","ts","rtmp"]},"server_info":{"url":"portal.geniptv.com","port":"8080","https_port":"25463","server_protocol":"http","rtmp_port":"25462","timezone":"UTC","timestamp_now":1602768143,"time_now":"2020-10-15 13:22:23","process":True}}
        output = {"user_info":{"username":"zqcAXZEvlW","password":"ATiD6d7K3H","message":"","auth":1,"status":"Active","exp_date":"1632734599","is_trial":"0","active_cons":"1","created_at":"1585304571","max_connections":"1","allowed_output_formats":["m3u8"]},"server_info":{"url":"sjva-dev.soju6jan.com","port":"443","https_port":"443","server_protocol":"https","rtmp_port":"443","timezone":"UTC","timestamp_now":1602768143,"time_now":"2020-10-15 13:22:23","process":True}}
        logger.debug(output)
        return jsonify(output)
    elif request.args.get('action') == 'get_live_streams':
        time.sleep(5)
        output = [{"num":1,"name":"##########   Arab Countries   ##########","stream_type":"live","stream_id":2519,"stream_icon":"","epg_channel_id":None,"added":"1492282762","is_adult":"0","category_id":"3","custom_sid":"","tv_archive":0,"direct_source":"","tv_archive_duration":0},{"num":2,"name":"Minbij TV ARB","stream_type":"live","stream_id":90930,"stream_icon":"","epg_channel_id":None,"added":"1598715027","is_adult":"0","category_id":"3","custom_sid":"","tv_archive":0,"direct_source":"","tv_archive_duration":0},{"num":3,"name":"Sham TV ARB","stream_type":"live","stream_id":90929,"stream_icon":"","epg_channel_id":None,"added":"1598714979","is_adult":"0","category_id":"3","custom_sid":"","tv_archive":0,"direct_source":"","tv_archive_duration":0},{"num":4,"name":"Chada TV ARB","stream_type":"live","stream_id":90914,"stream_icon":"","epg_channel_id":None,"added":"1598710250","is_adult":"0","category_id":"3","custom_sid":"","tv_archive":0,"direct_source":"","tv_archive_duration":0},{"num":5,"name":"2M Maroc ARB","stream_type":"live","stream_id":3555,"stream_icon":"","epg_channel_id":"2M Maroc ARB","added":"1492886137","is_adult":"0","category_id":"3","custom_sid":"","tv_archive":0,"direct_source":"","tv_archive_duration":0},{"num":6,"name":"4G Aflam ARB","stream_type":"live","stream_id":14341,"stream_icon":"","epg_channel_id":None,"added":"1527277548","is_adult":"0","category_id":"3","custom_sid":"","tv_archive":0,"direct_source":"","tv_archive_duration":0},{"num":7,"name":"4G Cima ARB","stream_type":"live","stream_id":14340,"stream_icon":"","epg_channel_id":None,"added":"1527277548","is_adult":"0","category_id":"3","custom_sid":"","tv_archive":0,"direct_source":"","tv_archive_duration":0},{"num":8,"name":"4G Classic ARB","stream_type":"live","stream_id":14339,"stream_icon":"","epg_channel_id":None,"added":"1527277548","is_adult":"0","category_id":"3","custom_sid":"","tv_archive":0,"direct_source":"","tv_archive_duration":0},{"num":9,"name":"4G Drama ARB","stream_type":"live","stream_id":14338,"stream_icon":"","epg_channel_id":None,"added":"1527277548","is_adult":"0","category_id":"3","custom_sid":"","tv_archive":0,"direct_source":"","tv_archive_duration":0},{"num":10,"name":"4G Film ARB","stream_type":"live","stream_id":14337,"stream_icon":"","epg_channel_id":None,"added":"1527277548","is_adult":"0","category_id":"3","custom_sid":"","tv_archive":0,"direct_source":"","tv_archive_duration":0},{"num":11,"name":"7Besha Cima ARB","stream_type":"live","stream_id":3526,"stream_icon":"","epg_channel_id":None,"added":"1492886134","is_adult":"0","category_id":"3","custom_sid":"","tv_archive":0,"direct_source":"","tv_archive_duration":0},{"num":12,"name":"ABN TV ARB","stream_type":"live","stream_id":8937,"stream_icon":"","epg_channel_id":None,"added":"1510324057","is_adult":"0","category_id":"3","custom_sid":"","tv_archive":0,"direct_source":"","tv_archive_duration":0}]
        return jsonify(output)
    elif request.args.get('action') == 'get_vod_categories':
        time.sleep(5)
        output = [{"category_id":"255","category_name":"VOD Netherlands","parent_id":0},{"category_id":"137","category_name":"VOD XXX","parent_id":0},{"category_id":"142","category_name":"VOD Portuguese","parent_id":0},{"category_id":"143","category_name":"VOD Poland","parent_id":0},{"category_id":"144","category_name":"VOD Russian","parent_id":0},{"category_id":"145","category_name":"VOD Albania","parent_id":0},{"category_id":"147","category_name":"VOD Arabic","parent_id":0},{"category_id":"148","category_name":"VOD Nordic Multi-Subs","parent_id":0},{"category_id":"149","category_name":"VOD Romania","parent_id":0},{"category_id":"152","category_name":"VOD Greek","parent_id":0},{"category_id":"154","category_name":"VOD Finland","parent_id":0},{"category_id":"155","category_name":"VOD Norway","parent_id":0},{"category_id":"159","category_name":"VOD 3D ENGLISH","parent_id":0},{"category_id":"210","category_name":"VOD Iran Dubbed","parent_id":0},{"category_id":"136","category_name":"VOD IMDB TOP250","parent_id":0},{"category_id":"83","category_name":"VOD EX-YU","parent_id":0},{"category_id":"67","category_name":"VOD France","parent_id":0},{"category_id":"50","category_name":"VOD Germany","parent_id":0},{"category_id":"115","category_name":"VOD Germany Kids HD","parent_id":0},{"category_id":"94","category_name":"VOD India","parent_id":0},{"category_id":"51","category_name":"VOD Italia","parent_id":0},{"category_id":"86","category_name":"VOD Multi-Subtitles","parent_id":0},{"category_id":"52","category_name":"VOD Denmark","parent_id":0},{"category_id":"134","category_name":"VOD: Spain","parent_id":0},{"category_id":"85","category_name":"VOD Swedish","parent_id":0},{"category_id":"122","category_name":"Vod Swedish Kids","parent_id":0},{"category_id":"74","category_name":"VOD Turkey","parent_id":0},{"category_id":"133","category_name":"VOD Turkey Series: S\u00f6z","parent_id":0},{"category_id":"53","category_name":"VOD United Kingdom","parent_id":0}]

        return jsonify(output)

    elif request.args.get('action') == 'get_vod_streams':
        time.sleep(5)
        return redirect('http://portal.geniptv.com:8080/player_api.php?username=zqcAXZEvlW&password=ATiD6d7K3H&action=get_vod_streams')
        output = [{"num":1,"name":"Fireproof (2008) [AL]","stream_type":"movie","stream_id":78946,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":2,"name":"Game of Assassins (2013) [AL]","stream_type":"movie","stream_id":78947,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":3,"name":"Give Me Liberty (2019) [AL]","stream_type":"movie","stream_id":78948,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":4,"name":"Harriet (2019) [AL]","stream_type":"movie","stream_id":78949,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":5,"name":"Heritage (2019) [AL]","stream_type":"movie","stream_id":78950,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":6,"name":"Hidden (Cache) (2005) [AL]","stream_type":"movie","stream_id":78951,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":7,"name":"Hit-and-Run Squad (2019) [AL]","stream_type":"movie","stream_id":78952,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":8,"name":"Honey Boy (2019) [AL]","stream_type":"movie","stream_id":78953,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":9,"name":"Hotwired in Suburbia (2020) [AL]","stream_type":"movie","stream_id":78954,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":10,"name":"I Lost My Body (2019) [AL]","stream_type":"movie","stream_id":78955,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":11,"name":"Inglourious Basterds (2009) [AL]","stream_type":"movie","stream_id":78956,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":12,"name":"Inherit the Viper (2019) [AL]","stream_type":"movie","stream_id":78957,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":13,"name":"Inner Ghosts (2018) [AL]","stream_type":"movie","stream_id":78958,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":14,"name":"Intrigo- Death of an Author (2018) [AL]","stream_type":"movie","stream_id":78959,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":15,"name":"Jay and Silent Bob Reboot (2019) [AL]","stream_type":"movie","stream_id":78960,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":16,"name":"Jay and Silent Bob Strike Back (2001) [AL]","stream_type":"movie","stream_id":78961,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":17,"name":"Just Mercy (2019) [AL]","stream_type":"movie","stream_id":78962,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":18,"name":"Kindred Spirits (2019) [AL]","stream_type":"movie","stream_id":78963,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":19,"name":"Koko- A Red Dog Story (2019) [AL]","stream_type":"movie","stream_id":78964,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":20,"name":"Last Christmas (2019) [AL]","stream_type":"movie","stream_id":78965,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":21,"name":"Legiony (2019) [AL]","stream_type":"movie","stream_id":78966,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":22,"name":"Little Women (2019) [AL]","stream_type":"movie","stream_id":78967,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":23,"name":"Made in China (2019) [AL]","stream_type":"movie","stream_id":78968,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":24,"name":"Martin Eden (2019) [AL]","stream_type":"movie","stream_id":78969,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":25,"name":"Midnight Special (2016) [AL]","stream_type":"movie","stream_id":78970,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":26,"name":"Midway (2019) [AL]","stream_type":"movie","stream_id":78971,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":27,"name":"Mine 9 (2019) [AL]","stream_type":"movie","stream_id":78972,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":28,"name":"Money (2019) [AL]","stream_type":"movie","stream_id":78973,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":29,"name":"Mongol- The Rise of Genghis Khan (2007) [AL]","stream_type":"movie","stream_id":78974,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":30,"name":"Monos (2019) [AL]","stream_type":"movie","stream_id":78975,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":31,"name":"Motherless Brooklyn (2019) [AL]","stream_type":"movie","stream_id":78976,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":32,"name":"Mrs. Doubtfire (1993) [AL]","stream_type":"movie","stream_id":78977,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":33,"name":"Nation's Fire (2019) [AL]","stream_type":"movie","stream_id":78978,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":34,"name":"One Piece- Stampede (2019) [AL]","stream_type":"movie","stream_id":78979,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""},{"num":35,"name":"Pain and Glory (2019) [AL]","stream_type":"movie","stream_id":78980,"stream_icon":None,"rating":None,"rating_5based":0,"added":"1581529315","is_adult":"0","category_id":"145","container_extension":"mp4","custom_sid":"","direct_source":""}]
    elif request.args.get('action') == 'get_vod_info':
        output = {"info":[]}
        return jsonify(output)

    elif request.args.get('action') == 'get_series_categories':
        output =  [{"category_id":"333","category_name":"VOD Series - French","parent_id":0},{"category_id":"334","category_name":"VOD Series - Anime","parent_id":0},{"category_id":"337","category_name":"VOD Series - English","parent_id":0},{"category_id":"338","category_name":"VOD Series - Multisubs","parent_id":0},{"category_id":"339","category_name":"VOD Series - Germany","parent_id":0},{"category_id":"340","category_name":"VOD Series - English 2","parent_id":0},{"category_id":"341","category_name":"VOD Series - Turkey","parent_id":0}]
        return jsonify(output)

    elif request.args.get('action') == 'get_series':
        return redirect('http://portal.geniptv.com:8080/player_api.php?username=zqcAXZEvlW&password=ATiD6d7K3H&action=get_series')
        output = [{"num":1,"name":"Manifest","series_id":10,"cover":"http:\/\/portal.geniptv.com:8080\/images\/moaCMoZYVifaQnNJGDr3M6rBglB_small.jpg","plot":"After landing from a turbulent but routine flight, the crew and passengers of Montego Air Flight 828 discover five years have passed in what seemed like a few hours. As their new realities become clear, a deeper mystery unfolds and some of the returned passengers soon realize they may be meant for something greater than they ever thought possible.","cast":"Melissa Roxburgh, Josh Dallas, Athena Karkanis, J.R. Ramirez, Luna Blaise, Jack Messina, Parveen Kaur, Tim Moriarty","director":"Jeff Rake","genre":"Mystery \/ Drama","releaseDate":"2018-09-24","last_modified":"1553135428","rating":"7","rating_5based":3.5,"backdrop_path":["http:\/\/portal.geniptv.com:8080\/images\/79696_tv_backdrop_0.jpg","http:\/\/portal.geniptv.com:8080\/images\/79696_tv_backdrop_1.jpg","http:\/\/portal.geniptv.com:8080\/images\/79696_tv_backdrop_2.jpg","http:\/\/portal.geniptv.com:8080\/images\/79696_tv_backdrop_3.jpg"],"youtube_trailer":"LjsFg7e-ffk","episode_run_time":"42","category_id":"338"},{"num":2,"name":"Magnum P.I. (2018)","series_id":11,"cover":"http:\/\/portal.geniptv.com:8080\/images\/son6AuCmsoPWmRgPP6fKQacV9wt_small.jpg","plot":"Thomas Magnum, a decorated former Navy SEAL who, upon returning home from Afghanistan, repurposes his military skills to become a private investigator in Hawaii taking jobs no one else will with the help of fellow vets T.C. Calvin and Rick Wright, and the former MI:6 agent Higgins.","cast":"Jay Hernandez, Perdita Weeks, Zachary Knighton, Stephen Hill","director":"","genre":"Drama","releaseDate":"2018-09-24","last_modified":"1553135258","rating":"7","rating_5based":3.5,"backdrop_path":["http:\/\/portal.geniptv.com:8080\/images\/79593_tv_backdrop_0.jpg","http:\/\/portal.geniptv.com:8080\/images\/79593_tv_backdrop_1.jpg","http:\/\/portal.geniptv.com:8080\/images\/79593_tv_backdrop_2.jpg","http:\/\/portal.geniptv.com:8080\/images\/79593_tv_backdrop_3.jpg","http:\/\/portal.geniptv.com:8080\/images\/79593_tv_backdrop_4.jpg"],"youtube_trailer":"qMmv9JFOEB0","episode_run_time":"43","category_id":"338"},{"num":3,"name":"All American","series_id":12,"cover":"http:\/\/portal.geniptv.com:8080\/images\/5WlAYpxS8MEXyY6LB2RiCD2KTDs_small.jpg","plot":"When a rising high school football player from South Central L.A. is recruited to play for Beverly Hills High, the wins, losses and struggles of two families from vastly different worlds - Compton and Beverly Hills - begin to collide. Inspired by the life of pro football player Spencer Paysinger.","cast":"Daniel Ezra, Taye Diggs, Samantha Logan, Michael Evans Behling, Greta Onieogou, Bre-Z, Cody Christian, Monet Mazur","director":"April Blair","genre":"Drama","releaseDate":"2018-10-10","last_modified":"1553133233","rating":"7","rating_5based":3.5,"backdrop_path":["http:\/\/portal.geniptv.com:8080\/images\/82428_tv_backdrop_0.jpg","http:\/\/portal.geniptv.com:8080\/images\/82428_tv_backdrop_1.jpg"],"youtube_trailer":"oIaujmoukqU","episode_run_time":"45","category_id":"338"}]


    
    elif request.args.get('action') == 'get_series_info':
        return redirect('http://portal.geniptv.com:8080/player_api.php?username=zqcAXZEvlW&password=ATiD6d7K3H&action=get_series_info&series_id=333')
        

        output =  [{"category_id":"333","category_name":"VOD Series - French","parent_id":0},{"category_id":"334","category_name":"VOD Series - Anime","parent_id":0},{"category_id":"337","category_name":"VOD Series - English","parent_id":0},{"category_id":"338","category_name":"VOD Series - Multisubs","parent_id":0},{"category_id":"339","category_name":"VOD Series - Germany","parent_id":0},{"category_id":"340","category_name":"VOD Series - English 2","parent_id":0},{"category_id":"341","category_name":"VOD Series - Turkey","parent_id":0}]
        return jsonify(output)

   
   



    return jsonify('')

@blueprint.route('/login')
def login():
    logger.debug('xtream codes login')
    logger.debug(request.args)
    return jsonify('')

@blueprint.route('/<sub>')
def sample():
    logger.debug('sub : %s', sub)
    logger.debug(request.args)
    return jsonify('')    