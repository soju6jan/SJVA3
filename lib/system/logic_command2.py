# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import logging
import platform
import subprocess
import threading
import sys
import io
import time
import json
# third-party

# sjva 공용
from framework.logger import get_logger
from framework import path_app_root, socketio, logger, py_queue, app

# 패키지

# 로그
package_name = __name__.split('.')[0]
#logger = get_logger(package_name)
#########################################################

class SystemLogicCommand2(object):
    instance_list = []

    def __init__(self, title, commands, clear=True, wait=False, show_modal=True):
        self.title = title
        self.commands = commands
        self.clear = clear
        self.wait = wait
        self.show_modal = show_modal

        self.process = None
        self.stdout_queue = None
        self.thread = None
        self.send_to_ui_thread = None
        self.return_log = []
        SystemLogicCommand2.instance_list.append(self)


    def start(self):
        try:
            if self.show_modal:
                if self.clear:
                    socketio.emit("command_modal_clear", None, namespace='/framework', broadcast=True)
                
            self.thread = threading.Thread(target=self.execute_thread_function, args=())
            self.thread.setDaemon(True)
            self.thread.start()
            if self.wait:
                time.sleep(1)
                self.thread.join()
                return self.return_log
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    def execute_thread_function(self):
        try:
            #if wait:
            if self.show_modal:
                socketio.emit("command_modal_show", self.title, namespace='/framework', broadcast=True)
                socketio.emit("loading_hide", None, namespace='/framework', broadcast=True)
                
            for command in self.commands:
                if command[0] == 'msg':
                    if self.show_modal:
                        socketio.emit("command_modal_add_text", '%s\n\n' % command[1], namespace='/framework', broadcast=True)
                elif command[0] == 'system':
                    if self.show_modal:
                        socketio.emit("command_modal_add_text", '$ %s\n\n' % command[1], namespace='/framework', broadcast=True)
                    os.system(command[1])
                else:
                    show_command = True
                    if command[0] == 'hide':
                        show_command = False
                        command = command[1:]
                    #self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                    self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf8')
                    self.start_communicate(command, show_command=show_command)
                    self.send_queue_start()
                    if self.process is not None:
                        self.process.wait()
                time.sleep(1)
        except Exception as exception: 
            if self.show_modal:
                socketio.emit("command_modal_show", self.title, namespace='/framework', broadcast=True)
                socketio.emit("command_modal_add_text", str(exception), namespace='/framework', broadcast=True)
                socketio.emit("command_modal_add_text", str(traceback.format_exc()), namespace='/framework', broadcast=True)


    def start_communicate(self, current_command, show_command=True):
        self.stdout_queue = py_queue.Queue()
        if show_command:
            self.stdout_queue.put('$ %s\n' % ' '.join(current_command))
        sout = io.open(self.process.stdout.fileno(), 'rb', closefd=False)
        #serr = io.open(process.stderr.fileno(), 'rb', closefd=False)
        
        def Pump(stream):
            queue = py_queue.Queue()
            
            def rdr():
                #logger.debug('START RDR')
                while True:
                    buf = self.process.stdout.read(1)
                    if buf:
                        queue.put( buf )
                    else: 
                        queue.put( None )
                        break
                #logger.debug('END RDR')
                queue.put( None )
                time.sleep(1)
                
                #Logic.command_close()
            def clct():
                active = True
                #logger.debug('START clct')
                while active:
                    r = queue.get()
                    if r is None:
                        break
                    try:
                        while True:
                            r1 = queue.get(timeout=0.005)
                            if r1 is None:
                                active = False
                                break
                            else:
                                r += r1
                    except:
                        pass
                    if r is not None:
                        if app.config['config']['is_py2']:
                            try:
                                r = r.decode('utf-8')
                            except Exception as exception: 
                                #logger.error('Exception:%s', e)
                                #logger.error(traceback.format_exc())
                                try:
                                    r = r.decode('cp949')
                                except Exception as exception: 
                                    logger.error('Exception:%s', exception)
                                    logger.error(traceback.format_exc())
                                    try:
                                        r = r.decode('euc-kr')
                                    except:
                                        pass
                        
                        self.stdout_queue.put(r)
                        self.return_log += r.split('\n')
                        #logger.debug('IN:%s', r)
                self.stdout_queue.put('<END>')
                #logger.debug('END clct')
                #Logic.command_close()
            for tgt in [rdr, clct]:
                th = threading.Thread(target=tgt)
                th.setDaemon(True)
                th.start()
        Pump(sout)
        #Pump(serr, 'stderr')

    def send_queue_start(self):
        def send_to_ui_thread_function():
            #logger.debug('send_queue_thread_function START')
            if self.show_modal:
                socketio.emit("command_modal_show", self.title, namespace='/framework', broadcast=True)
            while self.stdout_queue:
                line = self.stdout_queue.get()
                #logger.debug('Send to UI :%s', line)
                if line == '<END>':
                    if self.show_modal:
                        socketio.emit("command_modal_add_text", "\n", namespace='/framework', broadcast=True)
                        break
                else:
                    if self.show_modal:
                        socketio.emit("command_modal_add_text", line, namespace='/framework', broadcast=True)
            self.send_to_ui_thread = None
            self.stdout_queue = None
            self.process = None
            #logger.debug('send_to_ui_thread_function END')
            
        if self.send_to_ui_thread is None:
            self.send_to_ui_thread = threading.Thread(target=send_to_ui_thread_function, args=())
            self.send_to_ui_thread.start()


    @classmethod
    def plugin_unload(cls):
        for instance in cls.instance_list:
            try:
                if instance.process is not None and instance.process.poll() is None:
                    import psutil
                    process = psutil.Process(instance.process.pid)
                    for proc in instance.process.children(recursive=True):
                        proc.kill()
                    instance.process.kill()
            except Exception as exception: 
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())           
            finally:
                try: instance.process.kill()
                except: pass