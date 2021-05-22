# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
from datetime  import datetime, timedelta
import json
import traceback

# third-party
from flask import redirect, render_template, Response, request, jsonify, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required

# sjva 공용
from framework import app, db, version, USERS, login_manager, logger, path_data, check_api
import system


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = (request.form['remember'] == 'True')
        if username not in USERS:
            return jsonify('no_id')
        elif not USERS[username].can_login(password):
            return jsonify('wrong_password')
        else:
            USERS[username].authenticated = True
            login_user(USERS[username], remember=remember)
            return jsonify('redirect')
    else:
        if db.session.query(system.ModelSetting).filter_by(key='use_login').first().value == 'False':
            username = db.session.query(system.ModelSetting).filter_by(key='id').first().value
            USERS[username].authenticated = True
            login_user(USERS[username], remember=True)
            #current_user = USERS[username]
            return redirect(request.args.get("next"))

        return render_template('login.html', next=request.args.get("next"))


@app.errorhandler(401)
def custom_401(error):
    
    #return Response('<Why access is denied string goes here...>', 401, {'WWW-Authenticate':'Basic realm="Login Required"'})
    return 'login_required'
              
@login_manager.user_loader
def user_loader(user_id):
    return USERS[user_id]

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    user = current_user
    user.authenticated = False
    json_res = {'ok': True, 'msg': 'user <%s> logout' % user.user_id}
    logout_user()
    return redirect('/login')
    #return jsonify(json_res)

###############################################################
#  API
###############################################################
@app.route("/")
@app.route("/None")
@app.route("/home")
def home():
    logger.warning(request.host_url)
    return redirect('/system/home')

@app.route("/version")
def get_version():
    #return jsonify(version)
    return version

@app.route("/open_file/<path:path>")
@login_required
def open_file(path):
    logger.debug('open_file :%s', path)
    return send_from_directory('/', path)

@app.route("/file/<path:path>")
@check_api
def file2(path):
    logger.debug('file2 :%s', path)
    return send_from_directory('/', path)

@app.route("/download_file/<path:path>")
@login_required
def download_file(path):
    logger.debug('download_file :%s', path)
    return send_from_directory('/', path, as_attachment=True)

@app.route("/hls")
def hls_play():
    url = request.args.get('url')
    logger.debug('hls url : %s', url)
    return render_template('hls_player3.html', url=url)

@app.route("/iframe/<sub>")
@login_required
def iframe(sub):
    if sub == 'file_manager':
        if app.config['config']['is_debug'] or current_user.is_authenticated:
            logger.debug(request.base_url)
            logger.debug(request.path)
            from system.logic import SystemLogic
            site = SystemLogic.get_setting_value('ddns')
            if site == 'http://localhost:9999':
                site = 'flaskfilemanager'
            else:
                site += '/flaskfilemanager'
            logger.debug(site)
            return render_template('iframe.html', site=site)

        else:
            return redirect('/login?next=' + request.path)
    elif sub == 'file_manager2':
        if current_user.is_authenticated:
            return redirect('/flaskfilemanager')
        else:
            return redirect('/login?next=/flaskfilemanager' + request.path)



@app.route("/upload", methods=['GET', 'POST'])
def upload():
    try:
        if request.method == 'POST':
            f = request.files['file']
            from werkzeug import secure_filename
            tmp = secure_filename(f.filename)
            logger.debug('upload : %s', tmp)
            f.save(os.path.join(path_data, 'upload', tmp))
            return jsonify('success')
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
        return jsonify('fail')

@app.route('/robots.txt')
def robot_to_root():
    return send_from_directory('', 'static/file/robots.txt')
    #return send_from_directory('', path)


#####################################
@app.route('/static/<path:path>')
def rc():
    try:
        logger.debug('XXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        logger.debug(path)
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
        return jsonify('fail')


@app.route('/get_ip')
def get_ip():
    if system.SystemLogic.get_setting_value('ddns').find('soju6jan.com') != -1:
        headers_list = request.headers.getlist("X-Forwarded-For")
        user_ip = headers_list[0] if headers_list else request.remote_addr
        logger.debug('IIIIIIIIIIIIIIIIIIPPPPPPPPPPPPPPPPPP : %s', user_ip)
        return jsonify(user_ip)



@app.route('/global/ajax/<sub>', methods=['GET', 'POST'])
@login_required
def global_ajax(sub):
    #logger.debug('/global/ajax/%s', sub)
    if sub == 'listdir':
        if 'path' in request.form:
            if os.path.isfile(request.form['path']):
                return jsonify('')
            if 'only_dir' in request.form and request.form['only_dir'].lower() == 'true':
                result_list = [name for name in os.listdir(request.form['path']) if os.path.isdir(os.path.join(request.form['path'],name))]
            else:
                result_list = os.listdir(request.form['path'])
            result_list.sort()
            result_list = ['..'] + result_list
            return jsonify(result_list)
        else:
            return jsonify(None)    