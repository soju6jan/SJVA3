# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import time
import threading

# third-party
from flask import request
from flask_socketio import SocketIO, emit

# sjva 공용
from framework import app, socketio, path_data, logger
from framework.logger import get_logger
from framework.util import SingletonClass


# 패키지

# 로그

#########################################################

namespace = 'log'

@socketio.on('connect', namespace='/%s' % namespace)
def socket_connect():
    logger.debug('log connect')

@socketio.on('start', namespace='/%s' % namespace)
def socket_file(data):
    try:
        package = filename = None
        if 'package' in data:
            package = data['package']
        else:
            filename = data['filename']
        LogViewer.instance().start(package, filename, request.sid)
        logger.debug('start package:%s filename:%s sid:%s', package, filename, request.sid)
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

@socketio.on('disconnect', namespace='/%s' % namespace)
def disconnect():
    try:
        LogViewer.instance().disconnect(request.sid)
        logger.debug('disconnect sid:%s', request.sid)
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())



class WatchThread(threading.Thread):

    def __init__(self, package, filename):
        super(WatchThread, self).__init__()
        self.stop_flag = False
        self.package = package
        self.filename = filename
        self.daemon = True

    def stop(self):
        self.stop_flag = True

    def run(self):
        logger.debug('WatchThread.. Start %s', self.package)
        if self.package is not None:
            logfile = os.path.join(path_data, 'log', '%s.log' % self.package)
            key = 'package'
            value = self.package
        else:
            logfile = os.path.join(path_data, 'log', self.filename)
            key = 'filename'
            value = self.filename
        if os.path.exists(logfile):
            with open(logfile, 'r') as f:
                f.seek(0, os.SEEK_END)
                while not self.stop_flag:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1) # Sleep briefly
                        continue
                    socketio.emit("add", {key : value, 'data': line}, namespace='/log', broadcast=True)
            logger.debug('WatchThread.. End %s', value)
        else:
            socketio.emit("add", {key : value, 'data': 'not exist logfile'}, namespace='/log', broadcast=True)



class LogViewer(SingletonClass):
           
    watch_list = {} 

    @classmethod
    def start(cls, package, filename, sid):
        # 2019-04-02 간만에 봤더니 헷깔려서 적는다
        # 이 쓰레드는 오픈시 이전 데이타만을 보내는 쓰레드다. 실시간보는거 아님.
        
        def thread_function():
            if package is not None:
                logfile = os.path.join(path_data, 'log', '%s.log' % package)
            else:
                logfile = os.path.join(path_data, 'log', filename)
            if os.path.exists(logfile):
                ins_file = open(logfile, 'r')  ## 3)
                line = ins_file.read()
                socketio.emit("on_start", {'data': line}, namespace='/log')
                logger.debug('on_start end')
            else:
                socketio.emit("on_start", {'data': 'not exist logfile'}, namespace='/log')
        
        if package is not None:
            key = package
        else:
            key = filename
        thread = threading.Thread(target=thread_function, args=())
        thread.daemon = True
        thread.start()
      

        if key not in cls.watch_list:
            cls.watch_list[key] = {}
            cls.watch_list[key]['sid'] = []
            cls.watch_list[key]['thread'] = WatchThread(package, filename)
            cls.watch_list[key]['thread'].start()
        cls.watch_list[key]['sid'].append(sid)

    @classmethod
    def disconnect(cls, sid):
        find = False
        find_key = None
        for key, value in cls.watch_list.items():
            logger.debug('key:%s value:%s', key, value)
            for s in value['sid']:
                if sid == s:
                    find = True
                    find_key = key
                    value['sid'].remove(s)
                    break
            if find:
                break
        if not find:
            return
        if not cls.watch_list[find_key]['sid']:
            logger.debug('thread kill')
            cls.watch_list[find_key]['thread'].stop()
            del cls.watch_list[find_key]
