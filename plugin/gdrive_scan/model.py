# -*- coding: utf-8 -*-
#########################################################
# python
import os
from datetime import datetime
# third-party

# sjva 공용
from framework import db, app, path_data

# 패키지
from .plugin import logger, package_name
#########################################################
app.config['SQLALCHEMY_BINDS'][package_name] = 'sqlite:///%s' % (os.path.join(path_data, 'db', '%s.db' % package_name))
from plugin import get_model_setting
ModelSetting = get_model_setting(package_name, logger)

class ModelGDriveScanJob(db.Model):
    __tablename__ = '%s_job' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    gdrive_path = db.Column(db.String)
    plex_path = db.Column(db.String)
 
    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}

class ModelGDriveScanFile(db.Model):
    __tablename__ = '%s_file' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    gdrive_name = db.Column(db.String)
    name = db.Column(db.String)
    section_id = db.Column(db.Integer)
    is_file = db.Column(db.Boolean)
    is_add = db.Column(db.Boolean)
    created_time = db.Column(db.DateTime)
    scan_time = db.Column(db.DateTime)

    def __init__(self, gdrive_name, name, section_id, is_file, is_add):
        self.gdrive_name = gdrive_name
        self.name = name
        self.section_id = section_id
        self.is_file = is_file
        self.is_add = is_add
        self.created_time = datetime.now()


    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S') if self.created_time is not None else ''
        ret['scan_time'] = self.scan_time.strftime('%m-%d %H:%M:%S') if self.scan_time is not None else ''
        return ret

    @staticmethod
    def add(gdrive_name, name, section_id, is_file, is_add):
        item = ModelGDriveScanFile(gdrive_name, name, section_id, is_file, is_add)
        db.session.add(item)
        db.session.commit()
        return item.id
