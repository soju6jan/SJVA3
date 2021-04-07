# -*- coding: utf-8 -*-
#########################################################
# python
import traceback
from pytz import timezone
from datetime import datetime, timedelta
from random import randint
import threading
import time
import sys
# third-party
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.gevent import GeventScheduler
#from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.triggers.cron import CronTrigger

jobstores = {
    #'mongo': MongoDBJobStore(),
    'default': SQLAlchemyJobStore(url='sqlite:///data/db/sjva.db')
}
executors = {
    'default': ThreadPoolExecutor(20),
    
}
#'processpool': ProcessPoolExecutor(5)   
#

job_defaults = {
    'coalesce': False,
    'max_instances': 1
}
# sjva 공용
from framework.logger import get_logger

# 패키지
#########################################################
package_name = __name__.split('.')[0]
logger = get_logger(package_name)

class Scheduler(object):
    job_list = []
    first_run_check_thread = None
    def __init__(self):
        #(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)
        #self.sched = GeventScheduler( executors=executors)
        self.sched = GeventScheduler(timezone='Asia/Seoul')
        #jobstores=jobstores,  에러 pickle 직렬화 할수없다
        #self.sched.configure(executors=executors, job_defaults=job_defaults, timezone='Asia/Seoul')
        #self.sched.configure(executors=executors, timezone='Asia/Seoul')
        self.sched.start()
        logger.debug('SCHEDULER..')
        """
        if sys.argv[0] == 'sjva.py':
            first_run_check_thread = threading.Thread(target=self.first_run_check_thread_function, args=())
            first_run_check_thread.start()
        """


    def first_run_check_thread_function(self):
        logger.warning('XX first_run_check_thread_function')
        try:
            #time.sleep(60)
            #for i in range(5):
            flag_exit = True
            for job_instance in self.job_list:
                if not job_instance.run:
                    continue
                if job_instance.count == 0 and not job_instance.is_running and job_instance.is_interval:
                #if job_instance.count == 0 and not job_instance.is_running:
                    job = self.sched.get_job(job_instance.job_id) 
                    if job is not None:
                        logger.warning('job_instance : %s', job_instance.plugin)
                        logger.warning('XX job re-sched:%s', job)
                        flag_exit = False
                        tmp = randint(1, 20)
                        job.modify(next_run_time=datetime.now(timezone('Asia/Seoul')) + timedelta(seconds=tmp))
                        #break
                    else:
                        pass
            if flag_exit:
                self.remove_job("scheduler_check")
            #time.sleep(30)
            logger.warning('first_run_check_thread_function end!!')
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    def shutdown(self):
        self.sched.shutdown()

    def kill_scheduler(self, job_id):
        try:
            self.sched.remove_job(job_id)
        except JobLookupError as err:
            logger.debug("fail to stop Scheduler: {err}".format(err=err))
            logger.debug(traceback.format_exc())
        
    """
    def add_job(self, function, minutes, job_id):
        from framework import app
        if app.config['config']['run_by_real']:
            self.sched.add_job(function, 'interval', minutes=minutes, id=job_id, args=(None))
            job = self.sched.get_job(job_id) 
            job.modify(next_run_time=datetime.now(timezone('Asia/Seoul')) + timedelta(seconds=5))
    """
    
    def add_job_instance(self, job_instance, run=True):
        from framework import app
        if app.config['config']['run_by_real'] and app.config['config']['auth_status']:
            if not self.is_include(job_instance.job_id):
                job_instance.run = run
                Scheduler.job_list.append(job_instance)
                if job_instance.is_interval:
                    self.sched.add_job(job_instance.job_function, 'interval', minutes=job_instance.interval, seconds=job_instance.interval_seconds, id=job_instance.job_id, args=(None))
                elif job_instance.is_cron:
                    self.sched.add_job(job_instance.job_function, CronTrigger.from_crontab(job_instance.interval), id=job_instance.job_id, args=(None))
                #self.sched.add_job(job_instance.job_function, 'interval', minutes=job_instance.interval, id=job_instance.job_id, args=(None))
                job = self.sched.get_job(job_instance.job_id) 
                if run and job_instance.is_interval:
                    tmp = randint(5, 20)
                    job.modify(next_run_time=datetime.now(timezone('Asia/Seoul')) + timedelta(seconds=tmp))

    def execute_job(self, job_id):
        logger.debug('execute_job:%s', job_id)
        job = self.sched.get_job(job_id) 
        tmp = randint(5, 20)
        job.modify(next_run_time=datetime.now(timezone('Asia/Seoul')) + timedelta(seconds=tmp))
         
    
    def is_include(self, job_id):
        job = self.sched.get_job(job_id) 
        return (job is not None)
    
    def remove_job(self, job_id):
        try:
            if self.is_include(job_id):
                self.sched.remove_job(job_id)
                job = self.get_job_instance(job_id)
                if not job.is_running:
                    self.remove_job_instance(job_id)
                logger.debug('remove job_id:%s', job_id)
            return True
        except JobLookupError as err:
            logger.debug("fail to remove Scheduler: {err}".format(err=err))
            logger.debug(traceback.format_exc())
            return False

     
    def get_job_instance(self, job_id):
        for job in Scheduler.job_list:
            if job.job_id == job_id:
                return job
    
    def is_running(self, job_id):
        job = self.get_job_instance(job_id)
        if job is None:
            return False
        else:
            return job.is_running

    # job에서만 호출한다..
    def remove_job_instance(self, job_id):
        # function이 실행중일때 제거하면..
        # 실행중이나 목록에서 빠져버린다..
        for job in Scheduler.job_list:
            if job.job_id == job_id:
                Scheduler.job_list.remove(job)
                logger.debug('remove_job_instance : %s', job_id)
                break


    def get_job_list_info(self):
        
        ret = []
        idx = 0
        job_list = self.sched.get_jobs()
        #logger.debug('len jobs %s %s', len(jobs), len(Scheduler.job_list))
        for j in job_list:
            idx += 1
            entity = {}
            entity['no'] = idx
            entity['id'] = j.id
            entity['next_run_time'] = j.next_run_time.strftime('%m-%d %H:%M:%S')
            remain = (j.next_run_time - datetime.now(timezone('Asia/Seoul')))
            tmp = ''
            if remain.days > 0:
                tmp += '%s일 ' % (remain.days)
            remain = remain.seconds
            if remain//3600 > 0:
                tmp += '%s시간 ' % (remain//3600)
            remain = remain % 3600
            if remain // 60 > 0:
                tmp += '%s분 ' % (remain//60)
            tmp += '%s초' % (remain%60)
            #entity['remain_time'] = (j.next_run_time - datetime.now(timezone('Asia/Seoul'))).seconds
            entity['remain_time'] = tmp
            job = self.get_job_instance(j.id)
            if job is not None:
                entity['count'] = job.count
                entity['plugin'] = job.plugin
                if job.is_cron:
                    entity['interval'] = job.interval
                elif job.interval == 9999:
                    entity['interval'] = '항상 실행'
                    entity['remain_time'] = ''
                else:
                    entity['interval'] = '%s분 %s초' % (job.interval, job.interval_seconds)
                entity['is_running'] = job.is_running
                entity['description'] = job.description
                entity['running_timedelta'] = job.running_timedelta.seconds if job.running_timedelta is not None else '-'
                entity['make_time'] = job.make_time.strftime('%m-%d %H:%M:%S')
                entity['run'] = job.run
            else:
                entity['count'] = ''
                entity['plugin'] = ''
                entity['interval'] = ''
                entity['is_running'] = ''
                entity['description'] = ''
                entity['running_timedelta'] = ''
                entity['make_time'] = ''
                entity['run'] = True
            
            ret.append(entity)
        return ret


"""
#########################################################
# python
import traceback
# third-party
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler

# sjva 공용
from framework.logger import get_logger

# 패키지
#########################################################
package_name = __name__.split('.')[0]
logger = get_logger(package_name)

class Scheduler(object):
    def __init__(self):
        self.sched = BackgroundScheduler()
        self.sched.start()
    
    #def __del__(self):
    #    self.shutdown()
    
    def shutdown(self):
        self.sched.shutdown()

    def kill_scheduler(self, job_id):
        try:
            self.sched.remove_job(job_id)
        except JobLookupError as err:
            logger.debug("fail to stop Scheduler: {err}".format(err=err))
            logger.debug(traceback.format_exc())
    
    def add_job(self, function, minutes, job_id):
        self.sched.add_job(function, 'interval', minutes=minutes, id=job_id, args=(None))
"""


    