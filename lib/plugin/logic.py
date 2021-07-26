# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import time
import threading
import platform
# third-party

# sjva 공용
from framework import db, scheduler
from framework.job import Job
from framework.util import Util

#########################################################


class Logic(object):
    db_default = {
        'recent_menu_plugin' : '',
    }

    def __init__(self, P):
        self.P = P

    def plugin_load(self):
        try:
            self.P.logger.debug('%s plugin_load', self.P.package_name)
            self.db_init()
            for module in self.P.module_list:
                module.migration()
            for module in self.P.module_list:
                module.plugin_load()
                if module.sub_list is not None:
                    for sub_name, sub_instance in module.sub_list.items():
                        sub_instance.plugin_load()
            if self.P.ModelSetting is not None:
                for module in self.P.module_list:
                    key = f'{module.name}_auto_start'
                    if self.P.ModelSetting.has_key(key) and self.P.ModelSetting.get_bool(key):
                        self.scheduler_start(module.name)
                    if module.sub_list is not None:
                        for sub_name, sub_instance in module.sub_list.items():
                            key = f'{module.name}_{sub_name}_auto_start'
                            if self.P.ModelSetting.has_key(key) and self.P.ModelSetting.get_bool(key):
                                self.scheduler_start_sub(module.name, sub_name)

        except Exception as exception:
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())

    def db_init(self):
        try:
            if self.P.ModelSetting is None:
                return

            for key, value in Logic.db_default.items():
                if db.session.query(self.P.ModelSetting).filter_by(key=key).count() == 0:
                    db.session.add(self.P.ModelSetting(key, value))

            for module in self.P.module_list:
                if module.sub_list is not None:
                    for name, sub_instance in module.sub_list.items():
                        if sub_instance.db_default is not None:
                            for key, value in sub_instance.db_default.items():
                                if db.session.query(self.P.ModelSetting).filter_by(key=key).count() == 0:
                                    db.session.add(self.P.ModelSetting(key, value))        
                if module.db_default is not None:
                    for key, value in module.db_default.items():
                        if db.session.query(self.P.ModelSetting).filter_by(key=key).count() == 0:
                            db.session.add(self.P.ModelSetting(key, value))
            db.session.commit()
        except Exception as exception:
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())


    def plugin_unload(self):
        try:
            self.P.logger.debug('%s plugin_unload', self.P.package_name)
            for module in self.P.module_list:
                module.plugin_unload()
                if module.sub_list is not None:
                    for sub_name, sub_instance in module.sub_list.items():
                        sub_instance.plugin_unload()
        except Exception as exception:
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())


    def scheduler_start(self, sub):
        try:
            job_id = '%s_%s' % (self.P.package_name, sub)
            module = self.get_module(sub)
            job = Job(self.P.package_name, job_id, module.get_scheduler_interval(), self.scheduler_function, module.get_scheduler_desc(), False, args=sub)
            scheduler.add_job_instance(job)
        except Exception as exception: 
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())

    
    def scheduler_stop(self, sub):
        try:
            job_id = '%s_%s' % (self.P.package_name, sub)
            scheduler.remove_job(job_id)
        except Exception as exception: 
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())


    def scheduler_function(self, sub):
        try:
            module = self.get_module(sub)
            module.scheduler_function()
        except Exception as exception: 
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())

    def reset_db(self,sub):
        try:
            module = self.get_module(sub)
            return module.reset_db()
        except Exception as exception: 
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())


    def one_execute(self, sub):
        self.P.logger.debug('one_execute :%s', sub)
        try:
            job_id = '%s_%s' % (self.P.package_name, sub)
            if scheduler.is_include(job_id):
                if scheduler.is_running(job_id):
                    ret = 'is_running'
                else:
                    scheduler.execute_job(job_id)
                    ret = 'scheduler'
            else:
                def func():
                    time.sleep(2)
                    self.scheduler_function(sub)
                threading.Thread(target=func, args=()).start()
                ret = 'thread'
        except Exception as exception: 
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())
            ret = 'fail'
        return ret
    
    def immediately_execute(self, sub):
        self.P.logger.debug('immediately_execute :%s', sub)
        try:
            def func():
                time.sleep(1)
                self.scheduler_function(sub)
            threading.Thread(target=func, args=()).start()
            ret = {'ret':'success', 'msg':'실행합니다.'}
        except Exception as exception: 
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())
            ret = {'ret' : 'danger', 'msg':str(exception)}
        return ret

    def get_module(self, sub):
        try:
            for module in self.P.module_list:
                if module.name == sub:
                    return module
        except Exception as exception:
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())

    def process_telegram_data(self, data, target=None):
        try:
            for module in self.P.module_list:
                if target is None or target.startswith(module.name):
                    module.process_telegram_data(data, target=target)
        except Exception as exception:
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())

    #######################################################
    # 플러그인 - 모듈 - 서브  구조하에서 서브 관련 함수

    def scheduler_start_sub(self, module_name, sub_name):
        try:
            #self.P.logger.warning('scheduler_start_sub')
            job_id = f'{self.P.package_name}_{module_name}_{sub_name}'
            ins_module = self.get_module(module_name)
            ins_sub = ins_module.sub_list[sub_name]
            job = Job(self.P.package_name, job_id, ins_sub.get_scheduler_interval(), ins_sub.scheduler_function, ins_sub.get_scheduler_desc(), False, args=None)
            scheduler.add_job_instance(job)
        except Exception as exception: 
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())

    def scheduler_stop_sub(self, module_name, sub_name):
        try:
            job_id = f'{self.P.package_name}_{module_name}_{sub_name}'
            scheduler.remove_job(job_id)
        except Exception as exception: 
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())

    def scheduler_function_sub(self, module_name, sub_name):
        try:
            ins_module = self.get_module(module_name)
            ins_sub = ins_module.sub_list[sub_name]
            ins_sub.scheduler_function()
        except Exception as exception: 
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())

    def one_execute_sub(self, module_name, sub_name):
        try:
            job_id = f'{self.P.package_name}_{module_name}_{sub_name}'
            if scheduler.is_include(job_id):
                if scheduler.is_running(job_id):
                    ret = 'is_running'
                else:
                    scheduler.execute_job(job_id)
                    ret = 'scheduler'
            else:
                def func():
                    time.sleep(2)
                    self.scheduler_function_sub(module_name, sub_name)
                threading.Thread(target=func, args=()).start()
                ret = 'thread'
        except Exception as exception: 
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())
            ret = 'fail'
        return ret
    
    def immediately_execute_sub(self, module_name, sub_name):
        self.P.logger.debug(f'immediately_execute : {module_name} {sub_name}')
        try:
            def func():
                time.sleep(1)
                self.scheduler_function_sub(module_name, sub_name)
            threading.Thread(target=func, args=()).start()
            ret = {'ret':'success', 'msg':'실행합니다.'}
        except Exception as exception: 
            self.P.logger.error('Exception:%s', exception)
            self.P.logger.error(traceback.format_exc())
            ret = {'ret' : 'danger', 'msg':str(exception)}
        return ret