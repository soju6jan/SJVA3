# -*- coding: utf-8 -*-
#########################################################
# python
import os
from datetime import datetime
import traceback
import logging
import subprocess
import time
import re
import threading
import json
import platform

# third-party
import sqlalchemy
from sqlalchemy import desc
from sqlalchemy import or_, and_, func, not_

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, path_app_root, path_data
from framework.job import Job
from framework.util import Util
from system.logic import SystemLogic
from system.logic_command import SystemLogicCommand

# 패키지
from .model import ModelSetting, ModelRcloneJob, ModelRcloneFile, ModelRcloneMount, ModelRcloneServe

# 로그
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
#########################################################
 
class Logic(object):
    db_default = { 
        'auto_start' : 'False',
        'interval' : '10',
        'web_page_size' : '30',
        'auro_start_rcd' : 'False',
        'rclone_bin_path' : 'rclone' if platform.system() != 'Windows' else os.path.join(path_data, 'bin', 'rclone.exe'),
        'rclone_config_path' : os.path.join(path_app_root, 'data', 'db', 'rclone.conf')
    }
    
    path_bin = path_rclone = path_config = None

    default_rclone_setting = {
        'static' : '--config %s --log-level INFO --stats 1s --stats-file-name-length 0',
        'user' : '--transfers=4 --checkers=8',
        'move' : '--delete-empty-src-dirs --create-empty-src-dirs --delete-after --drive-chunk-size=256M',
        'copy' : '--create-empty-src-dirs --delete-after --drive-chunk-size=256M',
        'sync' : '--create-empty-src-dirs --delete-after --drive-chunk-size=256M',
    }



    @staticmethod
    def db_init():
        try:
            for key, value in Logic.db_default.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    db.session.add(ModelSetting(key, value))
            db.session.commit()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def plugin_load():
        try:
            
            import platform
            Logic.path_bin = os.path.join(path_app_root, 'bin', platform.system())
            if platform.system() == 'Linux':
                if platform.platform().find('86') == -1 and platform.platform().find('64') == -1:
                    Logic.path_bin = os.path.join(path_app_root, 'bin', 'LinuxArm')
                if platform.platform().find('arch') != -1:
                    Logic.path_bin = os.path.join(path_app_root, 'bin', 'LinuxArm')
                if platform.platform().find('arm') != -1:
                    Logic.path_bin = os.path.join(path_app_root, 'bin', 'LinuxArm')                         
            Logic.path_rclone = os.path.join(Logic.path_bin, 'rclone')
            Logic.path_config = os.path.join(path_app_root, 'data', 'db', 'rclone.conf')
            Logic.default_rclone_setting['static'] = Logic.default_rclone_setting['static'] % Logic.path_config
            if platform.system() == 'Windows':
                Logic.path_rclone += '.exe'
            Logic.db_init()

            if ModelSetting.get('rclone_bin_path') == '':
                ModelSetting.set('rclone_bin_path', Logic.path_rclone)
            else:
                Logic.path_rclone = ModelSetting.get('rclone_bin_path')
            if ModelSetting.get('rclone_config_path') == '':
                ModelSetting.set('rclone_config_path', Logic.path_config)
            else:
                Logic.path_config = ModelSetting.get('rclone_config_path')
            
            # 사이트 목록 로딩
            if ModelSetting.query.filter_by(key='auto_start').first().value == 'True':
                Logic.scheduler_start()

            mount_list = db.session.query(ModelRcloneMount).filter_by().all()
            for m in mount_list:
                if m.auto_start:
                    Logic.mount_execute(str(m.id))

            serve_list = db.session.query(ModelRcloneServe).filter_by().all()
            from .logic_serve import LogicServe
            for s in serve_list:
                if s.auto_start:
                    LogicServe.serve_execute(str(s.id))

        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def plugin_unload():
        try:
            for key, value in Logic.mount_process.items():
                if value is not None:
                    Logic.mount_kill(key)
            from .logic_serve import LogicServe
            for key, value in LogicServe.serve_process.items():
                if value is not None:
                    LogicServe.serve_kill(key)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())



    @staticmethod
    def rclone_version():
        try:
            command = [u'%s' % Logic.path_rclone,  'version']
            ret = SystemLogicCommand.execute_command_return(command)
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    

    @staticmethod
    def load_remotes():
        try:
            f = open(Logic.path_config, 'r')
            ret = []
            entity = None
            while True:
                line = f.readline()
                if not line: 
                    break
                line = line.strip()
                if line == '':
                    continue
                match = re.compile(r'\[(?P<name>.*?)\]').search(line)
                if match:
                    if entity is not None:
                        ret.append(entity)
                        entity = None
                    entity = {}
                    entity['name'] = match.group('name')

                match = re.compile(r'(?P<key>.*?)\s\=\s(?P<value>.*?)$').search(line)
                if match:
                    if entity is not None:
                        entity[match.group('key')] = match.group('value')
            f.close()
            if entity is not None:
                ret.append(entity)
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @staticmethod
    def job_save(req):
        try:
            job_id = req.form['id']
            logger.debug('job_save id:%s', job_id)
            if job_id == '-1':
                job = ModelRcloneJob()
            else:
                job = db.session.query(ModelRcloneJob).filter_by(id=job_id).with_for_update().first()
            job.job_type = req.form['job_type']
            job.name = req.form['job_name']
            job.command = req.form['job_command']
            job.remote = req.form['job_remote']
            job.remote_path = req.form['job_remote_path'].strip()
            job.local_path = req.form['job_local_path'].strip()
            job.option_user = req.form['job_option_user'].strip()
            job.option_static = req.form['job_option_static'].strip()
            job.is_scheduling = (req.form['is_scheduling']=='True')
            db.session.add(job)
            db.session.commit()
            return 'success'
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'

    
    
    @staticmethod
    def setting_save(req):
        try:
            for key, value in req.form.items():
                logger.debug('Key:%s Value:%s', key, value)
                entity = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
                entity.value = value
            db.session.commit()
            return True                  
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def get_setting_value(key):
        try:
            return db.session.query(ModelSetting).filter_by(key=key).first().value
        except Exception as exception: 
            logger.error('Exception:%s %s',key, exception)
            logger.error(traceback.format_exc())
    

    @staticmethod
    def scheduler_start():
        try:
            interval = ModelSetting.query.filter_by(key='interval').first().value
            job = Job(package_name, package_name, interval, Logic.scheduler_function, u"Rclone 스케쥴링", True)
            scheduler.add_job_instance(job)
            logger.debug('Rclone scheduler_start %s', interval)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def scheduler_stop():
        try:
            logger.debug('auto scheduler_stop')
            Logic.kill()            
            scheduler.remove_job(package_name)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_jobs():
        try:
            job_list = db.session.query(ModelRcloneJob).filter_by().all()
            ret = [x.as_dict() for x in job_list]
            return ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    ######################################################################
    
    current_process = None
    current_log_thread = None
    current_data = None
    running_status = False #이전 스케쥴링이 돌고있는가?
    @staticmethod
    def scheduler_function():
        try:
            logger.debug('rclone scheduler_function')
            if not scheduler.is_include(package_name):
                logger.debug('not in scheduler')
                return
            if Logic.running_status:
                logger.debug('Logic.running_status is TRUE!!!!')
                return
            else:
                logger.debug('Logic.running_status is FALSE!!!!')
            job_list = db.session.query(ModelRcloneJob).filter_by(is_scheduling=True).with_for_update().all()
            Logic.running_status = True
            for job in job_list:
                Logic.execute(job)
                if not scheduler.is_include(package_name):
                    logger.debug('scheduler is stopped by user button')
                    break
            Logic.current_process = None   
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        finally:
            Logic.running_status = False

    @staticmethod
    def get_user_command_list(data):
        ret = []
        one = ''
        flag = False
        for d in data:
            if d == ' ':
                if flag == False:
                    ret.append(one)
                    one = ''
                    continue
            elif d == '"':
                flag = not flag
                logger.debug(flag)
                continue
            one += d
        ret.append(one)


        return ret

            

    @staticmethod   
    def execute(job):
        try:
            logger.debug(job)
            command = '%s %s %s %s:%s %s %s' % (Logic.path_rclone, job.command, job.local_path, job.remote, job.remote_path, job.option_static, job.option_user)
            import platform
            if platform.system() == 'Windows':
                tmp = command
                tmp = command.encode('cp949')
            else:
                #tmp = [Logic.path_rclone, job.command, job.local_path, '%s:%s' % (job.remote, job.remote_path)] + job.option_static.split(' ') + job.option_user.split(' ')
                tmp = [Logic.path_rclone, job.command, job.local_path, '%s:%s' % (job.remote, job.remote_path)] + job.option_static.split(' ') + Logic.get_user_command_list(job.option_user)
                


            logger.debug('type : %s', type(tmp))
            logger.debug('tmp : %s', tmp)
            if app.config['config']['is_py2']:
                Logic.current_process = subprocess.Popen(tmp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
            else:
                Logic.current_process = subprocess.Popen(tmp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            Logic.current_data = {}
            Logic.current_data['job'] = job.as_dict()
            Logic.current_data['command'] = command
            Logic.current_data['log'] = []
            Logic.current_data['files'] = []
            Logic.trans_callback('start')
            Logic.current_log_thread = threading.Thread(target=Logic.log_thread_fuction, args=())
            Logic.current_log_thread.start()
            logger.debug('normally process wait()')
            Logic.current_data['return_code'] = Logic.current_process.wait()
            Logic.trans_callback('finish')
            job.last_run_time = datetime.now()
            job.last_file_count = len(Logic.current_data['files'])
            db.session.commit()
        except sqlalchemy.exc.OperationalError  as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            db.session.rollback()
            logger.debug('ROLLBACK!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())



    @staticmethod
    def execute_job(req):
        try:
            job_id = req.form['id']
            return Logic.execute_by_job_id(job_id)
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())            
            return 'fail'
    
    @staticmethod
    def execute_by_job_id(job_id):
        try:
            job = db.session.query(ModelRcloneJob).filter_by(id=job_id).with_for_update().first()
            thread = threading.Thread(target=Logic.execute, args=(job,))
            thread.start()
            return 'success'
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())            
            return 'fail'


    @staticmethod
    def remove_job(req):
        try:
            job_id = req.form['id']
            logger.debug('remove_job id:%s', job_id)
            job = db.session.query(ModelRcloneJob).filter_by(id=job_id).first()
            db.session.delete(job)
            db.session.commit()
            return 'success'
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())            
            return 'fail'
    

    trans_regexes = [
        r'Transferred\:\s*(?P<trans_data_current>\d.*?)\s\/\s(?P<trans_total_size>\d.*?)\,\s*((?P<trans_percent>\d+)\%)?\-?\,\s*(?P<trans_speed>\d.*?)\,\sETA\s(((?P<rt_hour>\d+)h)*((?P<rt_min>\d+)m)*((?P<rt_sec>.*?)s)*)?\-?',
        r'Errors\:\s*(?P<error>\d+)',
        r'Checks\:\s*(?P<check_1>\d+)\s\/\s(?P<check_2>\d+)\,\s*(?P<check_percent>\d+)?\-?',
        r'Transferred\:\s*(?P<file_1>\d+)\s\/\s(?P<file_2>\d+)\,\s*((?P<file_percent>\d+)\%)?\-?',
        r'Elapsed\stime\:\s*((?P<r_hour>\d+)h)*((?P<r_min>\d+)m)*((?P<r_sec>.*?)s)*',
        r'\s*\*\s((?P<folder>.*)\/)?(?P<name>.*?)\:\s*(?P<percent>\d+)\%\s*\/(?P<size>\d.*?)\,\s*(?P<speed>\d.*?)\,\s*((?P<rt_hour>\d+)h)*((?P<rt_min>\d+)m)*((?P<rt_sec>.*?)s)*', 
        r'INFO\s*\:\s*((?P<folder>.*)\/)?(?P<name>.*?)\:\s*(?P<status>.*)'
    ]

    
    @staticmethod
    def log_thread_fuction():
        with Logic.current_process.stdout:
            ts = None
            iter_arg =  b'' if app.config['config']['is_py2'] else ''
            for line in iter(Logic.current_process.stdout.readline, iter_arg):
                line = line.strip()
                try:
                    try:
                        line = line.decode('utf-8')
                    except Exception as exception: 
                        try:
                            line = line.decode('cp949')
                        except Exception as exception: 
                            pass
                    #logger.debug('>>%s', line)
                    if line == '' or  line.startswith('Checking'):
                        continue
                    if line.endswith('INFO  :'):
                        continue
                    if line.startswith('Deleted:'):
                        continue
                    if line.startswith('Transferring:'):
                        ts.files = []
                        continue
                    match = re.compile(Logic.trans_regexes[0]).search(line)
                    if match:
                        if ts is not None:
                            Logic.trans_callback('status', ts)
                        ts = TransStatus()
                        ts.trans_data_current = match.group('trans_data_current')
                        ts.trans_total_size = match.group('trans_total_size')
                        ts.trans_percent = match.group('trans_percent') if 'trans_percent' in match.groupdict() else '0'
                        ts.trans_speed = match.group('trans_speed')
                        ts.rt_hour = match.group('rt_hour') if 'rt_hour' in match.groupdict() else '0'
                        ts.rt_min = match.group('rt_min') if 'rt_min' in match.groupdict() else '0'
                        ts.rt_sec = match.group('rt_sec') if 'rt_sec' in match.groupdict() else '0'
                        continue
                    match = re.compile(Logic.trans_regexes[1]).search(line)
                    if match:
                        ts.error = match.group('error')
                        continue
                    match = re.compile(Logic.trans_regexes[2]).search(line)
                    if match:
                        ts.check_1 = match.group('check_1')
                        ts.check_2 = match.group('check_2')
                        ts.check_percent = match.group('check_percent') if 'check_percent' in match.groupdict() else '0'
                        continue
                    match = re.compile(Logic.trans_regexes[3]).search(line)
                    if match:
                        ts.file_1 = match.group('file_1')
                        ts.file_2 = match.group('file_2')
                        ts.file_percent = match.group('file_percent') if 'file_percent' in match.groupdict() else '0'
                        continue
                    match = re.compile(Logic.trans_regexes[4]).search(line)
                    if match:
                        ts.r_hour = match.group('r_hour') if 'r_hour' in match.groupdict() else '0'
                        ts.r_min = match.group('r_min') if 'r_min' in match.groupdict() else '0'
                        ts.r_sec = match.group('r_sec') if 'r_sec' in match.groupdict() else '0'
                        continue
                    
                    
                    match = re.compile(Logic.trans_regexes[5]).search(line)
                    if match:
                        #ts.files.append(TransFile.get(match).__dict__)
                        Logic.set_file(match)
                        continue
                    if line.startswith('Renamed:'):
                        continue
                    if line.find('INFO :') == -1:
                        Logic.current_data['log'].append(line)
                        Logic.trans_callback('log')
                    match = re.compile(Logic.trans_regexes[6]).search(line)
                    if match:
                        Logic.trans_callback('files', FileFinished(match))
                        continue
                    logger.debug('NOT PROCESS : %s', line)       
                except Exception as exception:
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())
            logger.debug('rclone log thread end')
        Logic.trans_callback('status', ts)

    @staticmethod
    def kill():
        try:
            if Logic.current_process is not None and Logic.current_process.poll() is None:
                import psutil
                process = psutil.Process(Logic.current_process.pid)
                for proc in process.children(recursive=True):
                    proc.kill()
                process.kill()
                return 'success'
            return 'not_running'
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'


    #start, finish, status, info, last_status
    @staticmethod
    def trans_callback(cmd, data=None):
        try:
            if data is not None:
                if isinstance(data, FileFinished):
                    f = Logic.get_by_name(data.folder, data.name)
                    if f is not None:
                        if f.log != '':
                            f.log = '%s,%s' % (f.log, data.status)
                        else:
                            f.log = data.status
                        f.finish_time = datetime.now() if f.finish_time is None else f.finish_time
                        db.session.add(f)
                        db.session.commit()
                    # DB .....
                    #if 'files' not in Logic.current_data:
                    #    Logic.current_data['files'] = []
                    #Logic.current_data['info'].append(data.__dict__)
                    #for i in Logic.current_data.files
                    #if data.folder ==
                    #data = Logic.current_data
                    pass
                elif isinstance(data, TransStatus):
                    Logic.current_data['ts'] = data.__dict__
            from . import plugin
            plugin.socketio_callback(cmd, Logic.current_data)
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def set_file(match):
        folder = match.group('folder') if 'folder' in match.groupdict() else ''
        name = match.group('name')
        instance = Logic.get_by_name(folder, name)
        if instance is None:
            instance = ModelRcloneFile(Logic.current_data['job']['id'] , folder, name)
            Logic.current_data['files'].append(instance)
        instance.percent = int(match.group('percent'))
        instance.size = match.group('size')
        instance.speed = match.group('speed')
        instance.rt_hour = match.group('rt_hour') if 'rt_hour' in match.groupdict() else '0'
        instance.rt_min = match.group('rt_min') if 'rt_min' in match.groupdict() else '0'
        instance.rt_sec = match.group('rt_sec') if 'rt_sec' in match.groupdict() else '0'
        return instance
    
    @staticmethod
    def get_by_name(folder, name):
        instance = None
        for item in Logic.current_data['files']:
            if item.folder == folder and item.name == name:
                instance = item
                break
        return instance

    @staticmethod
    def filelist(req):
        try:
            ret = {}
            page = 1
            page_size = int(db.session.query(ModelSetting).filter_by(key='web_page_size').first().value)
            job_id = ''
            search = ''
            if 'page' in req.form:
                page = int(req.form['page'])
            if 'job_select' in req.form:
                if req.form['job_select'] != 'all':
                    job_id = int(req.form['job_select'])
            if 'search_word' in req.form:
                search = req.form['search_word']

            query = db.session.query(ModelRcloneFile)
            if job_id != '':
                query = query.filter(ModelRcloneFile.job_id==job_id)
            if search != '':
                query = query.filter(ModelRcloneFile.name.like('%'+search+'%'))
            count = query.count()
            query = (query.order_by(desc(ModelRcloneFile.id))
                        .limit(page_size)
                        .offset((page-1)*page_size)
                )
            logger.debug('ModelRcloneFile count:%s', count)

            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            #ret['paging'] = paging
            ret['paging'] = Util.get_paging_info(count, page, page_size)
            
            return ret
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())
    
    @staticmethod
    def rclone_job_by_ktv(local, remote, remove=False):
        try:
            logger.debug('job_save_by_ktv:%s %s %s', local, remote, remove)

            job = db.session.query(ModelRcloneJob) \
                .filter(ModelRcloneJob.local_path==local) \
                .filter(ModelRcloneJob.remote==remote.split(':')[0]) \
                .filter(ModelRcloneJob.remote_path==remote.split(':')[1]).first()

            if job:
                if remove:
                    db.session.delete(job)
                    db.session.commit()
                else:
                    pass
            else:
                if remove:
                    #오면 안됨
                    pass
                else:
                    job = ModelRcloneJob()
                    job.job_type = 1
                    job.name = 'ktv_%s' % remote.split(':')[0]
                    job.command = 'move'
                    job.remote = remote.split(':')[0]
                    job.remote_path = remote.split(':')[1]
                    job.local_path = local
                    job.option_user = Logic.default_rclone_setting['user'] + ' ' + Logic.default_rclone_setting['move']
                    job.option_static = Logic.default_rclone_setting['static']
                    job.is_scheduling = True
                    db.session.add(job)
                    db.session.commit()
            return 'success'
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'

    @staticmethod
    def reset_db():
        try:
            db.session.query(ModelRcloneFile).delete()
            db.session.commit()
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False
    
    #
    @staticmethod
    def get_log(req):
        try:
            ret = {}
            ret['ret'] = False
            where = req.form['type']
            db_id = req.form['id']
            log_filename = None
            if where == 'serve':
                item = db.session.query(ModelRcloneServe).filter_by(id=db_id).first()
                if item is not None:
                    if item.name == '':
                        log_filename = 'serve_%s' % item.id
                    else:
                        log_filename = 'serve_%s' % item.name
                    log_filename = os.path.join(path_app_root, 'data', 'log', '%s.log' % log_filename)
                else:
                    ret['ret'] = 'fail'
            elif where == 'mount':
                item = db.session.query(ModelRcloneMount).filter_by(id=db_id).first()
                if item is not None:
                    if item.name == '':
                        log_filename = 'mount_%s' % item.id
                    else:
                        log_filename = 'mount_%s' % item.name
                    log_filename = os.path.join(path_app_root, 'data', 'log', '%s.log' % log_filename)
                else:
                    ret['ret'] = 'fail'
            if log_filename is not None:
                logger.debug(log_filename)
                import codecs
                f = codecs.open(log_filename, 'r', encoding='utf8')
                ret['data'] = []
                for line in f:
                    ret['data'].append(line)
                f.close()
                ret['ret'] = 'success'

        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            ret['data'] = str(exception)
        return ret


    # 마운트
    mount_process = {}
    @staticmethod
    def mount_save(req):
        try:
            mount_id = req.form['id']
            if mount_id == '-1':
                item = ModelRcloneMount()
            else:
                item = db.session.query(ModelRcloneMount).filter_by(id=int(mount_id)).with_for_update().first()
            #item.job_type = req.form['job_type']
            item.name = req.form['mount_name'].strip()
            item.remote = req.form['mount_remote']
            item.remote_path = req.form['mount_remote_path'].strip()
            item.local_path = req.form['mount_local_path'].strip()
            item.option = req.form['mount_option'].strip()
            item.auto_start = (req.form['auto_start'] == 'True')
            db.session.add(item)
            db.session.commit()
            return 'success'
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'
    
    @staticmethod
    def mount_list():
        try:
            job_list = db.session.query(ModelRcloneMount).filter_by().all()
            ret = [x.as_dict() for x in job_list]
            for t in ret:
                t['current_status'] = (str(t['id']) in Logic.mount_process and Logic.mount_process[str(t['id'])] is not None)
            return ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def mount_execute(mount_id):
        try:
            item = db.session.query(ModelRcloneMount).filter_by(id=int(mount_id)).with_for_update().first()
            remote_path = '%s:%s' % (item.remote, item.remote_path)
            local_path = item.local_path

            if platform.system() == 'Windows':
                remote_path = remote_path.encode('cp949')
                local_path = local_path.encode('cp949')

            options = item.option.replace(' --daemon', '').strip().split(' ')
            #options = item.option.split(' ')
            command = [Logic.path_rclone, '--config', Logic.path_config, 'mount', remote_path, local_path]
            command += options
            command.append('--log-file')
            if item.name == '':
                log_filename = 'mount_%s' % item.id
            else:
                log_filename = 'mount_%s' % item.name
            log_filename = os.path.join(path_app_root, 'data', 'log', '%s.log' % log_filename)
            command.append(log_filename)
            try:
                if platform.system() == 'Linux':
                    fuse_unmount_command = ['fusermount', '-uz', local_path]
                    p1 = subprocess.Popen(fuse_unmount_command)
                    p1.wait()
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())

            process = subprocess.Popen(command)
            logger.debug('process.pid:%s', process)
            Logic.mount_process[mount_id] = process
            return 'success'
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'
    
    @staticmethod
    def mount_stop(req):
        mount_id = req.form['id']
        logger.debug('mount stop:%s' % mount_id)
        return Logic.mount_kill(mount_id)

    @staticmethod
    def mount_kill(mount_id):
        try:
            if mount_id in Logic.mount_process:
                process = Logic.mount_process[mount_id]
                logger.debug('process:%s,%s', process, process.poll())
                if process is not None and process.poll() is None:
                    import psutil
                    p = psutil.Process(process.pid)
                    for proc in p.children(recursive=True):
                        proc.kill()
                    p.kill()
                    try:
                        job = db.session.query(ModelRcloneMount).filter_by(id=int(mount_id)).first()
                        import platform
                        if platform.system() != 'Windows':
                            tmp = ['fusermount', '-uz', job.local_path]
                            subprocess.Popen(tmp)
                            logger.debug('execute fusermount -uz')
                    except:
                        logger.debug('fusermount error')
                    return 'success'
                else:
                    return 'already_stop'
            else:
                return 'not_running'
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'
        finally:
            Logic.mount_process[mount_id] = None

    @staticmethod
    def mount_remove(mount_id):
        try:
            logger.debug('remove_job id:%s', mount_id)
            job = db.session.query(ModelRcloneMount).filter_by(id=int(mount_id)).first()
            db.session.delete(job)
            db.session.commit()
            return 'success'
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())            
            return 'fail'



class TransStatus(object):
    def __init__(self):
        self.trans_data_current = \
        self.trans_total_size = \
        self.trans_percent = \
        self.trans_speed = \
        self.rt_hour = self.rt_min = self.rt_sec = \
        self.error = \
        self.check_1 = \
        self.check_2 = \
        self.check_percent = \
        self.file_1 = \
        self.file_2 = \
        self.file_percent = \
        self.r_hour = self.r_min = self.r_sec = ""
        #self.files = []
  


class FileFinished(object):
    def __init__(self, match):
        self.folder = match.group('folder') if 'folder' in match.groupdict() else ''
        self.name = match.group('name')
        self.status = match.group('status')
       
