# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import json
from datetime import datetime

# third-party
from sqlalchemy.orm.attributes import flag_modified

# sjva 공용
from framework import db, app, path_app_root, scheduler

# 패키지
from .plugin import logger, package_name

#########################################################


app.config['SQLALCHEMY_BINDS'][package_name] = 'sqlite:///%s' % (os.path.join(path_app_root, 'data', 'db', '%s.db' % package_name))

class ModelCommand(db.Model):
    __tablename__ = '%s_job' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String)  # 일반명령은 없다.
    command = db.Column(db.String) 
    description = db.Column(db.String)
    schedule_auto_start = db.Column(db.Boolean)  #시작시 자동스케쥴링 등록
    schedule_type = db.Column(db.String) #없음, 시작시 한번 실행, 스케쥴링
    schedule_info = db.Column(db.String)  #주시적실행은 주기, 
    

    def __init__(self, command):
        self.description = ''
        self.schedule_auto_start = False
        self.schedule_type = "0"
        self.schedule_info = ''
        self.set_command(command)

    def set_command(self, command):
        self.command = command
        #self.command_type = 0
        tmp = command.split(' ')
        for t in tmp:
            if t.endswith('.py'):
                #self.command_type = 2
                self.filename = t
                break
            elif t.endswith('.sh'):
                #self.command_type = 1
                self.filename = t
                break

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}


    @staticmethod
    def job_list():
        try:
            db_list = db.session.query(ModelCommand).filter().all()
            db_list = [x.as_dict() for x in db_list]
            from .logic_normal import LogicNormal
            for item in db_list:
                item['is_include'] = str(scheduler.is_include('command_%s' % item['id']))
                item['is_running'] = str(scheduler.is_running('command_%s' % item['id']))
                item['process_id'] = LogicNormal.process_list[item['id']].pid if item['id'] in LogicNormal.process_list and LogicNormal.process_list[item['id']] is not None else None
            return db_list
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @staticmethod
    def job_new(request):
        try:
            command = request.form['command']
            item = ModelCommand(command)
            db.session.add(item)
            db.session.commit()
            return 'success'
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'


    @staticmethod
    def job_save(request):
        try:
            id = request.form['job_id']
            entity = db.session.query(ModelCommand).filter_by(id=id).with_for_update().first()
            entity.set_command(request.form['job_command'])
            entity.description = request.form['job_description']         
            entity.schedule_type = request.form['job_schedule_type']
            entity.schedule_info = request.form['job_schedule_info'] if 'job_schedule_info' in request.form else ''
            entity.schedule_auto_start = (request.form['job_schedule_auto_start'] == 'True')
            db.session.commit()
            from .logic_normal import LogicNormal
            LogicNormal.scheduler_switch(id, False)
            return 'success'
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'

    @staticmethod
    def get_job_by_id(job_id):
        try:
            return db.session.query(ModelCommand).filter_by(id=int(job_id)).first()
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def job_remove(request):
        try:
            id = request.form['job_id']
            entity = db.session.query(ModelCommand).filter_by(id=id).first()
            db.session.delete(entity)
            db.session.commit()
            from .logic_normal import LogicNormal
            LogicNormal.scheduler_switch(id, False)
            return 'success'
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'fail'

    