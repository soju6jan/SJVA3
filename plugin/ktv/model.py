# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import datetime
# third-party

# sjva 공용
from framework.logger import get_logger
from framework import db, app, path_data
from sqlalchemy import or_, and_, func, not_
# 패키지

# 로그
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
#########################################################
app.config['SQLALCHEMY_BINDS'][package_name] = 'sqlite:///%s' % (os.path.join(path_data, 'db', '%s.db' % package_name))
from framework.common.plugin import get_model_setting
ModelSetting = get_model_setting(package_name, logger)

class ModelKtvLibrary(db.Model):
    __tablename__ = '%s_library' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    library_type = db.Column(db.Integer)
    library_path = db.Column(db.String)
    rclone_path = db.Column(db.String)
    replace_for_plex_source = db.Column(db.String)
    replace_for_plex_target = db.Column(db.String)
    index = db.Column(db.Integer)
    
    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}

        
class ModelKtvFile(db.Model):
    __tablename__ = '%s_file' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String)
    filename = db.Column(db.String)
    created_time = db.Column(db.DateTime)
    move_type = db.Column(db.Integer)
    match_folder_name = db.Column(db.String)      # 방송명 set_find_library_path 때 scan_abspath와 같이 설정
    move_abspath_local = db.Column(db.String)     # 옮겨질 절대경로 sef_find_library_path 
    move_abspath_sync = db.Column(db.String)      # 업로드 할 절대경로. rclone일때 다운로드폴더내, sync일때 지정된
    move_abspath_cloud = db.Column(db.String)     # 업로드 완료후 보여질 폴더. root의 마운트 폴더
    send_command_time = db.Column(db.DateTime)     # XXXXXXXXXXX 삭제
    scan_status = db.Column(db.Integer)              # 스캔플래그 
    scan_time = db.Column(db.DateTime)              # 스캔완료시 입력
    scan_abspath = db.Column(db.String)           # 스캔한 폴더. 로컬일때 move_abspath_local / 그외move_abspath_cloud
    plex_section_id = db.Column(db.Integer)        # 섹션ID
    plex_show_id = db.Column(db.Integer)           # 쇼ID
    plex_daum_id = db.Column(db.Integer)           # 다음ID
    plex_title = db.Column(db.String)             # 
    plex_image = db.Column(db.String)             #
    plex_abspath = db.Column(db.String)
    plex_part = db.Column(db.String)
    log = db.Column(db.String)

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S') if self.created_time is not None else ''
        ret['send_command_time'] = self.send_command_time.strftime('%m-%d %H:%M:%S') if self.send_command_time is not None else ''
        ret['scan_time'] = self.scan_time.strftime('%m-%d %H:%M:%S') if self.scan_time is not None else ''
        return ret


    @staticmethod
    def create(entity):
        try:
            f = ModelKtvFile()
            f.original_filename = entity.original_filename
            f.filename = entity.filename
            f.created_time = entity.download_time
            #f.created_time = datetime.now()
            f.move_type = int(entity.move_type)
            f.match_folder_name = entity.match_folder_name
            f.move_abspath_local = entity.move_abspath_local
            f.move_abspath_sync = entity.move_abspath_sync
            f.move_abspath_cloud = entity.move_abspath_cloud
            if entity.send_command_time != '':
                f.send_command_time = entity.send_command_time
            f.scan_status = int(entity.scan_status)
            #f.scan_time = entity.scan_time
            f.scan_abspath = entity.scan_abspath
            f.plex_section_id = entity.plex_section_id
            f.plex_show_id = entity.plex_show_id
            f.plex_daum_id = entity.plex_daum_id
            f.plex_title = entity.plex_title
            f.plex_image = entity.plex_image
            f.plex_abspath = entity.plex_abspath
            f.log = entity.log
            #db.session.add(f)
            #db.session.commit()
            return f
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_library_check_list():
        try:
            query = db.session.query(ModelKtvFile).filter_by(scan_status=1)
            query = query.filter(or_(ModelKtvFile.send_command_time.is_(None), ModelKtvFile.send_command_time < datetime.datetime.now() + datetime.timedelta(hours=-1)))
            query = query.filter(ModelKtvFile.created_time > datetime.datetime.now() + datetime.timedelta(hours=-24))
            ret = query.all()
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def get_image_empty_list():
        try:
            query = db.session.query(ModelKtvFile).filter_by(scan_status=3)
            query = query.filter(ModelKtvFile.plex_image.is_(None))
            query = query.filter(ModelKtvFile.plex_show_id != -1)
            #query = query.filter(ModelKtvFile.created_time > datetime.datetime.now() + datetime.timedelta(days=-7))
            query = query.filter(ModelKtvFile.created_time > datetime.datetime.now() + datetime.timedelta(hours=-24))
            ret = query.all()
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())