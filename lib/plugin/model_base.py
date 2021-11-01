# -*- coding: utf-8 -*-
#########################################################
# python
import traceback
from datetime import datetime

# third-party

# sjva 공용
from framework import db
from framework.util import Util

#########################################################
class ModelBase(db.Model):
    __abstract__ = True
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    model_setting = None
    logger = None

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        return {x.name: getattr(self, x.name).strftime('%m-%d %H:%M:%S') if isinstance(getattr(self, x.name), datetime) else getattr(self, x.name) for x in self.__table__.columns}
    

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            self.logger.error(f'Exception:{str(e)}')
            self.logger.error(traceback.format_exc())

    @classmethod
    def get_paging_info(cls, count, current_page, page_size):
        try:
            paging = {}
            paging['prev_page'] = True
            paging['next_page'] = True
            if current_page <= 10:
                paging['prev_page'] = False
            
            paging['total_page'] = int(count / page_size) + 1
            if count % page_size == 0:
                paging['total_page'] -= 1
            paging['start_page'] = int((current_page-1)/10) * 10 + 1
            paging['last_page'] = paging['total_page'] if paging['start_page'] + 9 > paging['total_page'] else paging['start_page'] + 9
            if paging['last_page'] == paging['total_page']:
                paging['next_page'] = False
            paging['current_page'] = current_page
            paging['count'] = count
            cls.logger.debug('paging : c:%s %s %s %s %s %s', count, paging['total_page'], paging['prev_page'], paging['next_page'] , paging['start_page'], paging['last_page'])
            return paging
        except Exception as e:
            cls.logger.error(f'Exception:{str(e)}')
            cls.logger.error(traceback.format_exc())

    
    @classmethod
    def get_by_id(cls, id):
        try:
            return db.session.query(cls).filter_by(id=id).first()
        except Exception as e:
            cls.logger.error(f'Exception:{str(e)}')
            cls.logger.error(traceback.format_exc())


    @classmethod
    def get_list(cls, by_dict=False):
        try:
            tmp = db.session.query(cls).all()
            if by_dict:
                tmp = [x.as_dict() for x in tmp]
            return tmp
        except Exception as e:
            cls.logger.error(f'Exception:{str(e)}')
            cls.logger.error(traceback.format_exc())



    @classmethod
    def delete_by_id(cls, id):
        try:
            db.session.query(cls).filter_by(id=id).delete()
            db.session.commit()
            return True
        except Exception as e:
            cls.logger.error(f'Exception:{str(e)}')
            cls.logger.error(traceback.format_exc())
        return False

    @classmethod
    def delete_all(cls):
        try:
            db.session.query(cls).delete()
            db.session.commit()
            return True
        except Exception as e:
            cls.logger.error(f'Exception:{str(e)}')
            cls.logger.error(traceback.format_exc())
        return False
    

    @classmethod
    def web_list(cls, req):
        try:
            ret = {}
            page = 1
            page_size = 30
            search = ''
            if 'page' in req.form:
                page = int(req.form['page'])
            if 'keyword' in req.form:
                search = req.form['keyword']
            option1 = req.form.get('option1', 'all')
            option2 = req.form.get('option2', 'all')
            order = req.form['order'] if 'order' in req.form else 'desc'

            query = cls.make_query(order=order, search=search, option1=option1, option2=option2)
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            cls.logger.debug('cls count:%s', count)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = cls.get_paging_info(count, page, page_size)
            try:
                if cls.model_setting is not None and cls.__tablename__ is not None:
                    cls.model_setting.set(f'{cls.__tablename__}_last_list_option', f'{order}|{page}|{search}|{option1}|{option2}')
            except Exception as e:
                cls.logger.error('Exception:%s', e)
                cls.logger.error(traceback.format_exc())
                cls.logger.error(f'{cls.__tablename__}_last_list_option ERROR!' )
            return ret
        except Exception as e:
            cls.logger.error('Exception:%s', e)
            cls.logger.error(traceback.format_exc())


    # 오버라이딩
    @classmethod
    def make_query(cls, order='desc', search='', option1='all', option2='all'):
        query = db.session.query(cls)
        return query 
        