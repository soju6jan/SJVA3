# -*- coding: utf-8 -*-
#########################################################
# python
import os
from datetime import datetime
# third-party

# sjva 공용
from framework import db, app, path_data

# 패키지

# 로그
from .plugin import logger, package_name
#########################################################
app.config['SQLALCHEMY_BINDS'][package_name] = 'sqlite:///%s' % (os.path.join(path_data, 'db', '%s.db' % package_name))
from plugin import get_model_setting
ModelSetting = get_model_setting(package_name, logger)

class ModelRcloneJob(db.Model):
    __tablename__ = '%s_job' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.Integer)
    name = db.Column(db.String)
    command = db.Column(db.String)
    remote = db.Column(db.String)
    remote_path = db.Column(db.String)
    local_path = db.Column(db.String)
    option_user = db.Column(db.String)
    option_static = db.Column(db.String)
    last_run_time = db.Column(db.DateTime)
    last_file_count = db.Column(db.Integer)
    is_scheduling = db.Column(db.Boolean)
    def __init__(self): 
        self.last_file_count = 0

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['last_run_time'] = self.last_run_time.strftime('%m-%d %H:%M:%S') if self.last_run_time is not None else ''
        return ret

class ModelRcloneFile(db.Model):
    __tablename__ = '%s_file' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer)
    folder = db.Column(db.String)
    name = db.Column(db.String)
    percent = db.Column(db.Integer)
    size = db.Column(db.String)
    speed = db.Column(db.String)
    rt_hour = db.Column(db.String)
    rt_min = db.Column(db.String)
    rt_sec = db.Column(db.String)
    log = db.Column(db.String)
    created_time = db.Column(db.DateTime)
    finish_time = db.Column(db.DateTime)

    def __init__(self, job_id, folder, name): 
        self.job_id = int(job_id)
        self.folder = folder
        self.name = name
        self.log = ''
        self.created_time = datetime.now()

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S')
        ret['finish_time'] = self.finish_time.strftime('%m-%d %H:%M:%S') if self.finish_time is not None else ''
        ret['delta'] = ''
        try:
            ret['delta'] = str(self.finish_time - self.created_time).split('.')[0]
        except:
            pass
        return ret

class ModelRcloneMount(db.Model):
    __tablename__ = '%s_mount' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    json = db.Column(db.JSON)
    name = db.Column(db.String)
    #job_id = db.Column(db.Integer)
    remote = db.Column(db.String)
    remote_path = db.Column(db.String)
    local_path = db.Column(db.String)
    option = db.Column(db.String)
    auto_start = db.Column(db.Boolean)
    #log_filename = db.Column(db.String)
    #current_status = db.Column(db.Boolean)
    
    def __init__(self): 
        self.current_status = False
        self.created_time = datetime.now()

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S')
        #ret['current_status'] = True if self.current_process is not None else False
        return ret

class ModelRcloneServe(db.Model):
    __tablename__ = '%s_serve' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name
    
    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    json = db.Column(db.JSON)
    name = db.Column(db.String)
    command = db.Column(db.String)
    remote = db.Column(db.String)
    remote_path = db.Column(db.String)
    port = db.Column(db.Integer)
    option = db.Column(db.String)
    auto_start = db.Column(db.Boolean)
    
    def __init__(self): 
        self.current_status = False
        self.created_time = datetime.now()

    def __repr__(self):
        return str(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S')
        ret['command_ui'] = ModelRcloneServe.commands[ret['command']]
        return ret

    commands = {'webdav':'WebDav', 'ftp':'FTP', 'dlna':'DLNA', 'sftp':'SFTP', 'http':'HTTP'}