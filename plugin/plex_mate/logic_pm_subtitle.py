from .plugin import P, logger, package_name, ModelSetting, os, sys, traceback, re, datetime, timedelta, render_template, jsonify, redirect, app, path_data, path_app_root, db, scheduler, SystemModelSetting, socketio, celery, LogicModuleBase, PluginUtil
import threading, time
from plugin import default_route_socketio
name = 'subtitle'
from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
from .logic_pm_base import LogicPMBase

from .task_pm_subtitle import Task

class LogicPMSubtitle(LogicModuleBase):
    db_default = {
        f'{name}_db_version' : '1',
        f'{name}_use_smi_to_srt' : 'False',
        f'{name}_task_stop_flag' : 'False',
    }

    def __init__(self, P):
        super(LogicPMSubtitle, self).__init__(P, 'task')
        self.name = name
        default_route_socketio(P, self)
        self.data = {
            'list' : [],
            'status' : {'is_working':'wait'}
        }
        self.list_max = 3000

    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        arg['sub'] = self.name
        arg['sub2'] = sub 
        try:
            arg['scheduler'] = str(scheduler.is_include(self.get_scheduler_name()))
            arg['is_running'] = str(scheduler.is_running(self.get_scheduler_name()))
            arg['library_list'] = PlexDBHandle.library_sections()
            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"{package_name}/{name}/{sub}")


    def process_ajax(self, sub, req):
        try:
            ret = {}
            if sub == 'command':
                command = req.form['command']
                if command.startswith('start'):
                    if self.data['status']['is_working'] == 'run':
                        ret = {'ret':'warning', 'msg':'실행중입니다.'}
                    else:
                        self.task_interface(command, req.form['arg1'], req.form['arg2'])
                        ret = {'ret':'success', 'msg':'작업을 시작합니다.'}
                elif command == 'stop':
                    if self.data['status']['is_working'] == 'run':
                        ModelSetting.set(f'{self.name}_task_stop_flag', 'True')
                        ret = {'ret':'success', 'msg':'잠시 후 중지됩니다.'}
                    else:
                        ret = {'ret':'warning', 'msg':'대기중입니다.'}
                elif command == 'refresh':
                    self.refresh_data()
                elif command == 'section_location':
                    ret['data'] = PlexDBHandle.section_location(library_id=req.form['arg1'])
            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})

    def task_interface(self, *args):
        logger.warning(args)
        def func():
            time.sleep(1)
            self.task_interface2(*args)
        th = threading.Thread(target=func, args=())
        th.setDaemon(True)
        th.start()


    def task_interface2(self, *args):
        logger.warning(args)
        #if sub == 'movie':
        library_section = PlexDBHandle.library_section(args[1])
        #logger.warning(d(library_section))
        self.data['list'] = []
        self.data['status']['is_working'] = 'run'
        self.refresh_data()
        ModelSetting.set(f'{self.name}_task_stop_flag', 'False')
        try:
            config = LogicPMBase.load_config()
            func = Task.start
            if app.config['config']['use_celery']:
                result = func.apply_async(args)
                ret = result.get(on_message=self.receive_from_task, propagate=True)
            else:
                ret = func(self, *args)
            self.data['status']['is_working'] = ret
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            self.data['status']['is_working'] = 'wait'
        self.refresh_data()


    def refresh_data(self, index=-1):
        #logger.error(f"refresh_data : {index}")
        #logger.debug(self.data)
        if index == -1:
            self.socketio_callback('refresh_all', self.data)
        else:
            self.socketio_callback('refresh_one', {'one' : self.data['list'][index], 'status' : self.data['status']})
        
        

    def receive_from_task(self, arg, celery=True):
        try:
            result = None
            if celery:
                if arg['status'] == 'PROGRESS':
                    result = arg['result']
            else:
                result = arg
            if result is not None:
                self.data['status'] = result['status']
                #logger.warning(result)
                del result['status']
                #logger.warning(result)
                if self.list_max != 0:
                    if len(self.data['list']) == self.list_max:
                        self.data['list'] = []
                if result['ret']['find_meta'] == False or ('smi2srt' in result['ret']):
                    result['index'] = len(self.data['list'])
                    self.data['list'].append(result)
                    self.refresh_data(index=result['index'])
                else:
                    self.socketio_callback('refresh_status', self.data['status'])
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())