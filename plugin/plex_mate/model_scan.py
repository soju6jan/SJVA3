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


class ModelScanItem(ModelBase):
    __tablename__ = 'scan_item'
    __bind_key__ = package_name

    model_setting = ModelSetting
    logger = logger

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)

    status = db.Column(db.String) # ready
    # 파일 체크 대상
    # wait_add_not_find : 추가모드. 아직 파일이 없음
    # wait_remove_still_exist : 삭제모드. 아직 파일이 있음

    # 스캔 대상
    # run_add_find : 추가모드. 파일 찾음
    # run_remove_removed : 삭제모드 파일 없어짐

    # enqueue
    # enqueue_add_find : 추가모드. 파일 찾음
    # enqueue_remove_removed : 삭제모드 파일 없어짐

   
    # 완료
    # finish_not_find_library : section_location에 없음. 라이브러리에 포함되어 있지 않음.
    # finish_wrong_section_id : 잘못된 섹션 ID로 요청
    # finish_add_already_in_db : 추가모드. 이미 DB에 파일이 있음
    # finish_remove_already_not_in_db : 삭제모드. 이미 DB에 파일이 없음. 완료
    # finish_already_scan_folder_exist : 추가나 삭제모드. 이미 스캔 대상 폴더가 DB에 있음
    # finish_time_over : 추가모드. 대기시간 지남



    # finish_add : 추가모드 끝
    # finish_remove : 삭제모드 끝
    

    # 요청
    call_from = db.Column(db.String)
    callback_id = db.Column(db.String)
    callback_url = db.Column(db.String)
    mode = db.Column(db.String) # add, remove
    target = db.Column(db.String) # 입력받은 것 그대로
    target_mode = db.Column(db.String) # file, folder
    section_id = db.Column(db.Integer) # 입력 받을 수도 있음. 같은 폴더가 여러 라이브러리에 있을 수 있음. 모든것을 다 스캔하기는 귀찮지만 이 섹션id를 요청하면 여기 아래 폴더만 찾음. 없다면 db 순서대로 하나 찾으면 끝

    # 요청후 처리
    section_title = db.Column(db.String)
    section_type = db.Column(db.Integer) 
    scan_folder = db.Column(db.String) # target이 파일이면 부모, 폴더면 그대로

    # 체크
    check_count = db.Column(db.Integer)
    check_finished_time = db.Column(db.DateTime)

    # scan
    scan_process_pid = db.Column(db.String)
    scan_duration = db.Column(db.Integer)
    finish_time = db.Column(db.DateTime)

    # 완료후    
    add_metadata_item_id = db.Column(db.String)
    remove_metadata_item_id = db.Column(db.String)



    def __init__(self):
        self.created_time = datetime.now()
        self.status = "ready"


    def set_status(self, status, save=False):
        self.status = status
        if self.status.startswith('finish_'):
            if self.callback_id is not None and self.callback_url is not None:
                try:
                    ret = requests.post(self.callback_url, data=self.as_dict()).text
                    logger.debug(f'scan callback : {ret}')
                except Exception as e: 
                    logger.error(f'Exception:{str(e)}')
                    logger.error(traceback.format_exc())
        if save:
            self.save()

       


    @classmethod
    def get_items(cls, mode):
        if mode == 'wait':
            query = db.session.query(cls).filter(or_(cls.status == 'ready', cls.status.like('wait_%')))
            
        elif mode == 'run':
            query = db.session.query(cls).filter(cls.status.like('run_%'))
        elif mode == 'all':
            query = db.session.query(cls)

        query = query.order_by(cls.id)
        #logger.debug(query)
        items = query.all()
        return items

    
    @classmethod
    def is_already_scan_folder_exist(cls, scan_folder):
        query = db.session.query(cls).filter(
            cls.scan_folder == scan_folder,
            or_(cls.status == 'run_add_find', cls.status == 'run_remove_removed')
        )
        query = query.order_by(cls.id)
        items = query.all()
        return items   

    @classmethod
    def not_finished_to_ready(cls):
        items = db.session.query(cls).filter(not_(cls.status.like('finish_%'))).with_for_update().all()
        for item in items:
            item.status = 'ready'
        db.session.commit()

       
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


    