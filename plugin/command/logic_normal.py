# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
from datetime import datetime
import traceback
import logging
import subprocess
import threading
import time
import io

# third-party
from sqlalchemy import desc
from sqlalchemy import or_, and_, func, not_

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, path_data, socketio, py_queue, py_reload
from framework.job import Job
from framework.util import Util

# 패키지
from .plugin import package_name, logger
from .model import ModelCommand
#########################################################

#from io import StringIO 
from io import BytesIO as StringIO
import sys

class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout
    def get_log(self):
        try:
            ret = self._stringio.getvalue().splitlines()
            self._stringio.truncate(0)
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

            return self


class LogicNormal(object):
    foreground_process = None
    command_queue = None
    send_queue_thread = None
    process_list = {}
    load_log_list = None
    
    @staticmethod
    def plugin_load():
        def plugin_load_thread():
            try:
                db_list = db.session.query(ModelCommand).filter().all()
                for item in db_list:
                    if '%s' % item.schedule_type == '1':
                        #import multiprocessing
                        th = threading.Thread(target=LogicNormal.execute_thread_function, args=(item.command,item.id))
                        #th = multiprocessing.Proces(target=LogicNormal.execute_thread_function, args=(item.command,))
                        th.setDaemon(True)
                        th.start()
                    elif '%s' % item.schedule_type == '2' and item.schedule_auto_start:
                        LogicNormal.scheduler_switch(item.id, True)

            except Exception as exception: 
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())        
        try:
            th = threading.Thread(target=plugin_load_thread)
            th.setDaemon(True)
            th.start()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def plugin_unload():
        try:
            LogicNormal.foreground_command_close()
            for key, p in LogicNormal.process_list.items():
                LogicNormal.process_close(p)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @staticmethod
    def foreground_command(command, job_id=None):
        try:
            command = command.split(' ')
            if command[0] == 'LOAD':
                def func():
                    LogicNormal.load_log_list = []
                    with Capturing() as LogicNormal.load_log_list:  # note the constructor argument
                        LogicNormal.start_communicate_load()
                        if job_id is not None:
                            command_logger = get_logger('%s_%s' % (package_name, job_id))
                            LogicNormal.module_load(command, logger=command_logger)
                        else:
                            LogicNormal.module_load(command)
                    for t in LogicNormal.load_log_list:
                        LogicNormal.command_queue.put(t + '\n')
                    LogicNormal.command_queue.put('<END>')
                th = threading.Thread(target=func, args=())
                th.setDaemon(True)
                th.start()
                return 'success'
            else:
                if LogicNormal.foreground_process is not None:
                    LogicNormal.foreground_command_close()
                    time.sleep(0.5)
                process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                LogicNormal.foreground_process = process
                LogicNormal.start_communicate2(process)
            return 'success'
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'


    # 외부에서만 호출한다.
    # 자동적으로 끝날경우 호출하지 않음.
    @staticmethod
    def foreground_command_close():
        LogicNormal.process_close(LogicNormal.foreground_process)
            
    
    @staticmethod
    def process_close(process):
        try:
            if process is None:
                return
            try:
                import psutil
                ps_process = psutil.Process(process.pid)
                for proc in ps_process.children(recursive=True):
                    proc.kill()
                ps_process.kill()
                return True
            except:
                pass
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        return False


    @staticmethod
    def scheduler_switch0(request):
        try:
            switch = request.form['switch']
            job_id = request.form['job_id']
            LogicNormal.scheduler_switch(job_id, (switch=='true'))
            return 'success'
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'

    # 작업을 저장하면 스케쥴러에서 뺀다
    @staticmethod
    def scheduler_switch(id, switch):
        try:
            job = ModelCommand.get_job_by_id(id)
            s_id = 'command_%s' % id
            if switch:
                job_instance = Job(package_name, s_id, job.schedule_info, LogicNormal.execute_thread_function_by_scheduler, u"%s %s : %s" % (package_name, job.id, job.description), True, args=job.id)
                scheduler.add_job_instance(job_instance)
            else:
                if scheduler.is_include(s_id):
                    scheduler.remove_job(s_id)
            return 'success'
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'


    @staticmethod
    def job_background(job_id):
        try:
            th = threading.Thread(target=LogicNormal.execute_thread_function_job, args=(job_id,))
            th.setDaemon(True)
            th.start()
            return True
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False


    @staticmethod
    def execute_thread_function_job(job_id, **kwargs):
        job = ModelCommand.get_job_by_id(job_id)
        kwargs['command_id'] = job.id
        return LogicNormal.execute_thread_function(job.command, **kwargs)

    # 외부에서 호출할수 있다.
    @staticmethod
    def execute_thread_function(command, command_id=-1, **kwargs):
        try:
            logger.debug('COMMAND RUN START : %s %s', command, command_id)
            ret = []
            import platform
            if platform.system() == 'Windows':
                command = command.encode('cp949')
            command = command.split(' ')
            new_command = []
            flag = False
            tmp = None
            for c in command:
                if c.startswith('"') and c.endswith('"'):
                    new_command.append(c[1:-1])
                elif c.startswith('"'):
                    flag = True
                    tmp = c[1:]
                elif flag and c.endswith('"'):
                    flag = False
                    tmp = tmp + ' ' + c[:-1]
                    new_command.append(tmp)
                elif flag:
                    tmp = tmp + ' ' + c
                else:
                    new_command.append(c)
            command = new_command
            

            if command[0] == 'LOAD':
                command_logger = get_logger('%s_%s' % (package_name, command_id))
                kwargs['logger'] = command_logger
                return LogicNormal.module_load(command, **kwargs)
            else:
                if app.config['config']['is_py2']:
                    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                else:
                    p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

                command_logger = None
                logger.debug(LogicNormal.process_list)
                if command_id != -1:
                    command_logger = get_logger('%s_%s' % (package_name, command_id))
                    if command_id in LogicNormal.process_list and LogicNormal.process_list[command_id] is not None:
                        LogicNormal.process_close(LogicNormal.process_list[command_id])
                    LogicNormal.process_list[command_id] = p
                logger.debug(LogicNormal.process_list)
                with p.stdout:
                    iter_arg =  b'' if app.config['config']['is_py2'] else ''
                    for line in iter(p.stdout.readline, iter_arg):
                        try:
                            line = line.decode('utf-8')
                        except Exception as exception: 
                            try:
                                line = line.decode('cp949')
                            except Exception as exception: 
                                pass
                        if command_logger is not None:
                            command_logger.debug(line.strip())
                        ret.append(line.strip())
                    p.wait()
                logger.debug('COMMAND RUN END : %s', command)
                p = None
                if command_id in LogicNormal.process_list:
                    del LogicNormal.process_list[command_id]
                return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())        


    @staticmethod
    def execute_thread_function_by_scheduler(*args, **kwargs):
        try:
            logger.debug('COMMAND RUN START BY SCHEDULE :%s', args[0])
            job = db.session.query(ModelCommand).filter_by(id=int(args[0])).first()
            #LogicNormal.execute_thread_function(job.command, log='%s_%s' % (package_name, job.id))
            LogicNormal.execute_thread_function(job.command, command_id=job.id)
            
            logger.debug('COMMAND RUN END BY SCHEDULE :%s', args[0])
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())  



    @staticmethod
    def start_communicate2(process):
        LogicNormal.command_queue = py_queue.Queue()
        sout = io.open(process.stdout.fileno(), 'rb', closefd=False)
        #serr = io.open(process.stderr.fileno(), 'rb', closefd=False)
        def Pump(stream):
            queue = py_queue.Queue()
            
            def rdr():
                logger.debug('START RDR')
                while True:
                    buf = process.stdout.read(1)
                    if buf:
                        queue.put( buf )
                    else: 
                        queue.put( None )
                        break
                logger.debug('END RDR')
                queue.put( None )
                time.sleep(1)
                
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
                        if app.config['config']['is_py2']:
                            try:
                                r = r.decode('utf-8')
                            except Exception as exception: 
                                #logger.error('Exception:%s', exception)
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
                        #logger.debug('IN:%s', r)
                        #logger.debug('IN2:%s', r.replace('\x00', ''))
                        LogicNormal.command_queue.put(r.replace('\x00', ''))
                        

                LogicNormal.command_queue.put('<END>')
                logger.debug('END clct')
            for tgt in [rdr, clct]:
                th = threading.Thread(target=tgt)
                th.setDaemon(True)
                th.start()
        Pump(sout)
        #Pump(serr, 'stderr')


    @staticmethod
    def start_communicate_load():
        LogicNormal.command_queue = py_queue.Queue()
        def func():
            position = 0
            flag = True
            while LogicNormal.command_queue is not None:
                #logger.debug('index: %s %s', position, len(LogicNormal.load_log_list))
                logs = LogicNormal.load_log_list.get_log()
                #logger.debug(logs)
                
                if logs:
                    for log in logs:
                        LogicNormal.command_queue.put(log.strip() + '\n')
                time.sleep(1)
        th = threading.Thread(target=func)
        th.setDaemon(True)
        th.start()


    @staticmethod
    def send_queue_start():
        def send_queue_thread_function():
            logger.debug('send_queue_thread_function START')
            while LogicNormal.command_queue:
                line = LogicNormal.command_queue.get()
                if line == '<END>':
                    socketio.emit("end", None, namespace='/%s' % package_name, broadcast=True)
                    break
                else:
                    socketio.emit("add", line, namespace='/%s' % package_name, broadcast=True)
            LogicNormal.send_queue_thread = None
            LogicNormal.command_queue = None
            LogicNormal.foreground_process = None
            logger.debug('send_queue_thread_function END')
            
        if LogicNormal.send_queue_thread is None:
            LogicNormal.send_queue_thread = threading.Thread(target=send_queue_thread_function, args=())
            LogicNormal.send_queue_thread.start()
    

    

    @staticmethod
    def send_process_command(req):
        try:
            command = req.form['command']
            if app.config['config']['is_py2']:
                LogicNormal.foreground_process.stdin.write(b'%s\n' % command)
            else:
                LogicNormal.foreground_process.stdin.write('%s\n' % command)
            LogicNormal.foreground_process.stdin.flush()
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False
    


    
    ########################################################################
    @staticmethod
    def command_file_list():
        try:
            command_path = os.path.join(path_data, 'command')
            file_list = os.listdir(command_path)
            ret = []
            for f in file_list:
                c = os.path.join(command_path, f)
                if f.endswith('.py'):
                    c = 'python %s' % c
                #ret.append({'filename':f, 'command':c})
                ret.append({'text':f, 'value':c})
            return ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())



    ########################################################################
    @staticmethod
    def module_load(command, **kwargs):
        try:
            python_filename = command[1]
            python_sys_path = os.path.dirname(python_filename)
            if python_sys_path not in sys.path:
                sys.path.insert(0, python_sys_path)
            logger.debug(sys.path)
            module_name = os.path.basename(python_filename).split('.py')[0]
            
            if sys.version_info[0] == 2:
                mod = __import__(module_name, fromlist=[])
                py_reload(mod)
            else:
                import importlib
                mod = importlib.import_module(module_name)
                importlib.reload(mod)

            args = command
            mod_command_load = getattr(mod, 'main')
            if mod_command_load:
                ret = mod_command_load(*args, **kwargs)
            return ret
            #return 'success'
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'


    