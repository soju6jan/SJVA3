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
from framework import path_app_root, socketio, py_queue, app

# 패키지

# 로그
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
#########################################################

class SystemLogicCommand(object):

    commands = None
    process = None
    stdout_queue = None
    thread = None
    send_to_ui_thread = None
    return_log = None
    @staticmethod
    def start(title, commands, clear=True, wait=False, show_modal=True):
        try:
            if show_modal:
                if clear:
                    socketio.emit("command_modal_clear", None, namespace='/framework', broadcast=True)
            SystemLogicCommand.return_log = []
            SystemLogicCommand.title = title
            SystemLogicCommand.commands = commands
            SystemLogicCommand.thread = threading.Thread(target=SystemLogicCommand.execute_thread_function, args=(show_modal,))
            SystemLogicCommand.thread.setDaemon(True)
            SystemLogicCommand.thread.start()
            if wait:
                time.sleep(1)
                SystemLogicCommand.thread.join()
                return SystemLogicCommand.return_log
           
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def execute_thread_function(show_modal):
        try:
            #if wait:
            if show_modal:
                socketio.emit("loading_hide", None, namespace='/framework', broadcast=True)
            for command in SystemLogicCommand.commands:
                #logger.debug('Command :%s', command)
                if command[0] == 'msg':
                    if show_modal:
                        socketio.emit("command_modal_add_text", '%s\n\n' % command[1], namespace='/framework', broadcast=True)
                elif command[0] == 'system':
                    if show_modal:
                        socketio.emit("command_modal_add_text", '$ %s\n\n' % command[1], namespace='/framework', broadcast=True)
                    os.system(command[1])
                else:
                    show_command = True
                    if command[0] == 'hide':
                        show_command = False
                        command = command[1:]
                    #SystemLogicCommand.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                    SystemLogicCommand.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf8')
                    SystemLogicCommand.start_communicate(command, show_command=show_command)
                    SystemLogicCommand.send_queue_start(show_modal)
                    if SystemLogicCommand.process is not None:
                        SystemLogicCommand.process.wait()
                time.sleep(1)
            
        except Exception as exception: 
            #logger.error('Exception:%s', exception)
            #logger.error(traceback.format_exc()) 
            if show_modal:
                socketio.emit("command_modal_show", SystemLogicCommand.title, namespace='/framework', broadcast=True)
                socketio.emit("command_modal_add_text", str(exception), namespace='/framework', broadcast=True)
                socketio.emit("command_modal_add_text", str(traceback.format_exc()), namespace='/framework', broadcast=True)



    @staticmethod
    def start_communicate(current_command, show_command=True):
        SystemLogicCommand.stdout_queue = py_queue.Queue()
        if show_command:
            SystemLogicCommand.stdout_queue.put('$ %s\n' % ' '.join(current_command))
        sout = io.open(SystemLogicCommand.process.stdout.fileno(), 'rb', closefd=False)
        #serr = io.open(process.stderr.fileno(), 'rb', closefd=False)
        
        def Pump(stream):
            queue = py_queue.Queue()
            
            def rdr():
                logger.debug('START RDR')
                while True:
                    buf = SystemLogicCommand.process.stdout.read(1)
                    if buf:
                        queue.put( buf )
                    else: 
                        queue.put( None )
                        break
                logger.debug('END RDR')
                queue.put( None )
                time.sleep(1)
                
                #Logic.command_close()
            def clct():
                active = True
                logger.debug('START clct')
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
                        
                        SystemLogicCommand.stdout_queue.put(r)
                        #SystemLogicCommand.return_log.append(r)
                        SystemLogicCommand.return_log += r.split('\n')
                        logger.debug('IN:%s', r)
                SystemLogicCommand.stdout_queue.put('<END>')
                logger.debug('END clct')
                #Logic.command_close()
            for tgt in [rdr, clct]:
                th = threading.Thread(target=tgt)
                th.setDaemon(True)
                th.start()
        Pump(sout)
        #Pump(serr, 'stderr')

    @staticmethod
    def send_queue_start(show_modal):
        def send_to_ui_thread_function():
            logger.debug('send_queue_thread_function START')
            if show_modal:
                socketio.emit("command_modal_show", SystemLogicCommand.title, namespace='/framework', broadcast=True)
            while SystemLogicCommand.stdout_queue:
                line = SystemLogicCommand.stdout_queue.get()
                logger.debug('Send to UI :%s', line)
                if line == '<END>':
                    if show_modal:
                        socketio.emit("command_modal_add_text", "\n", namespace='/framework', broadcast=True)
                        break
                else:
                    if show_modal:
                        socketio.emit("command_modal_add_text", line, namespace='/framework', broadcast=True)
            SystemLogicCommand.send_to_ui_thread = None
            SystemLogicCommand.stdout_queue = None
            SystemLogicCommand.process = None
            logger.debug('send_to_ui_thread_function END')
            
        if SystemLogicCommand.send_to_ui_thread is None:
            SystemLogicCommand.send_to_ui_thread = threading.Thread(target=send_to_ui_thread_function, args=())
            SystemLogicCommand.send_to_ui_thread.start()

    @staticmethod
    def plugin_unload():
        try:
            if SystemLogicCommand.process is not None and SystemLogicCommand.process.poll() is None:
                import psutil
                process = psutil.Process(SystemLogicCommand.process.pid)
                for proc in SystemLogicCommand.process.children(recursive=True):
                    proc.kill()
                SystemLogicCommand.process.kill()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())           


    ##################################
    # 외부 호출    
    @staticmethod
    def execute_command_return(command, format=None, force_log=False):
        from tool_base import ToolSubprocess
        return ToolSubprocess.execute_command_return(command, format=format, force_log=force_log)
        try:
            logger.debug('execute_command_return : %s', ' '.join(command))

            if app.config['config']['running_type'] == 'windows':
                command = ' '.join(command)
            
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf8')
            ret = []
            with process.stdout:
                for line in iter(process.stdout.readline, ''):
                    ret.append(line.strip())
                    if force_log:
                        logger.debug(ret[-1])
                process.wait() # wait for the subprocess to exit


            if format is None:
                ret2 = '\n'.join(ret)
            elif format == 'json':
                try:
                    index = 0
                    for idx, tmp in enumerate(ret):
                        #logger.debug(tmp)
                        if tmp.startswith('{') or tmp.startswith('['):
                            index = idx
                            break
                    ret2 = json.loads(''.join(ret[index:]))
                except:
                    ret2 = None

            return ret2
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            logger.error('command : %s', command)