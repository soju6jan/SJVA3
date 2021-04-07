# -*- coding: utf-8 -*-
#########################################################
# python
import traceback
import threading

from datetime import datetime
from pytz import timezone
from random import randint
# third-party

# sjva 공용
from framework import scheduler, app
from framework.logger import get_logger

# 패키지

# 로그
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
#########################################################

def multiprocessing_target(*a, **b):
    job_id = a[0]
    job = scheduler.get_job_instance(job_id)
    if job.args is None:
        job.target_function()
    else:
        job.target_function(job.args)

class Job(object):
    def __init__(self, plugin, job_id, interval, target_function, description, can_remove_by_framework, args=None):
        self.plugin = plugin
        self.job_id = job_id
        self.interval = '%s' % interval
        self.interval_seconds = randint(1, 59)
        self.target_function = target_function
        self.description = description
        self.can_remove_by_framework = can_remove_by_framework
        self.is_running = False
        self.thread = None
        self.start_time = None
        self.end_time = None
        self.running_timedelta = None
        self.status = None
        self.count = 0
        self.make_time = datetime.now(timezone('Asia/Seoul'))
        if len(self.interval.strip().split(' ')) == 5:
            self.is_cron = True
            self.is_interval = False
        else:
            self.is_cron = False
            self.is_interval = True
        if self.is_interval:
            if app.config['config']['is_py2']:
                #if isinstance(self.interval, unicode) or isinstance(self.interval, str):
                #    self.interval = int(self.interval)
                if type(self.interval) == type(u'') or type(self.interval) == type(''):
                    self.interval = int(self.interval)
            else:
                if isinstance(self.interval, str):
                    self.interval = int(self.interval)

        self.args = args
        self.run = True

    def job_function(self):
        try:
            #if self.count > 1:
            #    logger.debug(hm.check('JOB START %s' % self.job_id))
            #    logger.debug(hm.getHeap())
            self.is_running = True
            self.start_time = datetime.now(timezone('Asia/Seoul'))
            #import gipc
            #from multiprocessing import Process
            if self.args is None:
                self.thread = threading.Thread(target=self.target_function, args=())
                #self.thread = Process(target=multiprocessing_target, args=(self.job_id,))
                #self.thread = gipc.start_process(target=multiprocessing_target, args=(self.job_id,), daemon=True)
                #self.target_function()
            else:
                self.thread = threading.Thread(target=self.target_function, args=(self.args,))
                #self.thread = Process(target=multiprocessing_target, args=(self.job_id,))
                #self.thread = gipc.start_process(target=multiprocessing_target, args=(self.job_id,), daemon=True)
                #self.target_function(self.args)
            self.thread.daemon = True
            self.thread.start()
            self.thread.join()
            self.end_time = datetime.now(timezone('Asia/Seoul'))
            self.running_timedelta = self.end_time - self.start_time
            self.status = 'success'
            if not scheduler.is_include(self.job_id):
                scheduler.remove_job_instance(self.job_id)
            self.count += 1
        except Exception as exception: 
            self.status = 'exception'
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        finally:
            self.is_running = False
            #if self.count > 1:
            #    logger.debug(hm.check('JOB END %s' % self.job_id))
            #    logger.debug(hm.getHeap())


        
