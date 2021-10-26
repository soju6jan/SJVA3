# python
import os, sys, traceback, re, json, threading, time, shutil, fnmatch, glob
from datetime import datetime, timedelta

# sjva 공용
from framework import db, app, path_data
from sqlalchemy import or_, and_, func, not_, desc
from plugin import ModelBase

# 패키지
from .plugin import P

logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting


class ModelPeriodicItem(ModelBase):
    __tablename__ = 'periodic_item'
    __bind_key__ = package_name

    model_setting = ModelSetting
    logger = logger

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    reserved = db.Column(db.JSON)

    mode = db.Column(db.String) # 스케쥴링에 의해 실행, 수동실행
    status = db.Column(db.String)

    section_id = db.Column(db.Integer)
    section_title = db.Column(db.String)
    section_type = db.Column(db.Integer)
    process_pid = db.Column(db.String)
    folder = db.Column(db.String)
    duration = db.Column(db.Integer)
    #result = db.Column(db.JSON, ensure_ascii=False)
    append_files = db.Column(db.String)
    start_time = db.Column(db.DateTime)
    finish_time = db.Column(db.DateTime)
    part_before_max = db.Column(db.Integer)
    part_before_count = db.Column(db.Integer)
    part_after_max = db.Column(db.Integer)
    part_after_count = db.Column(db.Integer)
    part_append_count = db.Column(db.Integer)
    

    def __init__(self):
        self.created_time = datetime.now()
        self.status = "ready"

    @classmethod
    def set_terminated(cls):
        db.session.query(cls).filter(cls.status == 'working').update(dict(status='terminated'))
        db.session.commit()

    @classmethod
    def remove_no_append_data(cls):
        db.session.query(cls).filter(
            cls.status != 'working',
            or_(cls.part_append_count == 0, cls.part_append_count == None)
        ).delete()
        db.session.commit()
        return {'ret':'success', 'msg':'삭제하였습니다.'}


    # JSON 
    @classmethod
    def make_query(cls, order='desc', search='', option1='all', option2='all'):
        query = db.session.query(cls)
        if search is not None and search != '':
            if search.find('|') != -1:
                tmp = search.split('|')
                conditions = []
                for tt in tmp:
                    if tt != '':
                        conditions.append(cls.append_files.like('%'+tt.strip()+'%') )
                query = query.filter(or_(*conditions))
            elif search.find(',') != -1:
                tmp = search.split(',')
                for tt in tmp:
                    if tt != '':
                        query = query.filter(cls.append_files.like('%'+tt.strip()+'%'))
            else:
                query = query.filter(or_(cls.append_files.like('%'+search+'%'), cls.append_files.like('%'+search+'%')))

        #if av_type != 'all':
        #    query = query.filter(cls.av_type == av_type)

        if option1 != 'all':
            query = query.filter(cls.section_id == option1)
        
        if option2 == 'append':
            query = query.filter(cls.part_append_count > 0)

        if order == 'desc':
            query = query.order_by(desc(cls.id))
        else:
            query = query.order_by(cls.id)

        return query 




"""
class ModelPeriodicTask(ModelBase):
    __tablename__ = 'periodic_task'
    __bind_key__ = package_name

    model_setting = ModelSetting
    logger = logger

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    reserved = db.Column(db.JSON)

    section_id = db.Column(db.Integer)
    interval = db.Column(db.String)
    scan_mode = db.Column(db.String)
    use_scheduler = db.Column(db.Boolean)
    timeout = db.Column(db.Integer)
    directory = db.Column(db.String)
    desc = db.Column(db.String)

    section_title = db.Column(db.String)

    def __init__(self):
        self.created_time = datetime.now()

"""




