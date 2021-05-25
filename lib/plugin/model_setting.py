# -*- coding: utf-8 -*-
#########################################################
# python
import traceback

# third-party

# sjva 공용
from framework import db
from framework.util import Util

#########################################################
def get_model_setting(package_name, logger, table_name=None):
    class ModelSetting(db.Model):
        __tablename__ = '%s_setting' % package_name if table_name is None else table_name
        __table_args__ = {'mysql_collate': 'utf8_general_ci'}
        __bind_key__ = package_name

        id = db.Column(db.Integer, primary_key=True)
        key = db.Column(db.String, unique=True, nullable=False)
        value = db.Column(db.String, nullable=False)
    
        def __init__(self, key, value):
            self.key = key
            self.value = value

        def __repr__(self):
            return repr(self.as_dict())

        def as_dict(self):
            return {x.name: getattr(self, x.name) for x in self.__table__.columns}

        @staticmethod
        def get(key):
            try:
                ret = db.session.query(ModelSetting).filter_by(key=key).first()
                if ret is not None:
                    return ret.value.strip()
                return None
            except Exception as exception:
                logger.error('Exception:%s %s', exception, key)
                logger.error(traceback.format_exc())

        @staticmethod
        def has_key(key):
            return (db.session.query(ModelSetting).filter_by(key=key).first() is not None)
        
        @staticmethod
        def get_int(key):
            try:
                return int(ModelSetting.get(key))
            except Exception as exception:
                logger.error('Exception:%s %s', exception, key)
                logger.error(traceback.format_exc())
        
        @staticmethod
        def get_bool(key):
            try:
                return (ModelSetting.get(key) == 'True')
            except Exception as exception:
                logger.error('Exception:%s %s', exception, key)
                logger.error(traceback.format_exc())

        @staticmethod
        def set(key, value):
            try:
                item = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
                if item is not None:
                    item.value = value.strip() if value is not None else value
                    db.session.commit()
                else:
                    db.session.add(ModelSetting(key, value.strip()))
            except Exception as exception:
                logger.error('Exception:%s %s', exception, key)
                logger.error(traceback.format_exc())

        @staticmethod
        def to_dict():
            try:
                ret = Util.db_list_to_dict(db.session.query(ModelSetting).all())
                ret['package_name'] = package_name
                return ret 
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())


        @staticmethod
        def setting_save(req):
            try:
                for key, value in req.form.items():
                    if key in ['scheduler', 'is_running']:
                        continue
                    if key.startswith('global_') or key.startswith('tmp_'):
                        continue
                    logger.debug('Key:%s Value:%s', key, value)
                    entity = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
                    entity.value = value
                db.session.commit()
                return True                  
            except Exception as exception: 
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
                logger.debug('Error Key:%s Value:%s', key, value)
                return False

        @staticmethod
        def get_list(key, delimeter, comment=' #'):
            try:
                value = ModelSetting.get(key).replace('\n', delimeter)
                if comment is None:
                    values = [x.strip() for x in value.split(delimeter)]
                else:
                    values = [x.split(comment)[0].strip() for x in value.split(delimeter)]
                values = Util.get_list_except_empty(values)
                return values
            except Exception as exception: 
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
                logger.error('Error Key:%s Value:%s', key, value)

    return ModelSetting