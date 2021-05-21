# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, platform

from framework import app, logger, args
try:
    from celery import Celery
    #if app.config['config']['use_celery'] == False: # 변수 할당 전
    if (args is not None and args.use_gevent == False) or platform.system() == 'Windows':
        raise Exception('no celery')
    try:
        redis_port = os.environ['REDIS_PORT']
    except:
        redis_port = '6379'

    app.config['CELERY_BROKER_URL'] = 'redis://localhost:%s/0' % redis_port
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:%s/0' % redis_port
    celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])
    #celery.conf.update(app.config)
    celery.conf['CELERY_ENABLE_UTC'] = False
    #celery.conf['CELERY_TIMEZONE'] = 'Asia/Seoul'
    celery.conf.update(
        task_serializer='pickle',
        result_serializer='pickle',
        accept_content=['pickle'],
        timezone='Asia/Seoul'
    )

except:
    """
    from functools import wraps
    class DummyCelery:
        def task(self, original_function):
            @wraps(original_function)
            def wrapper_function(*args, **kwargs):  #1
                return original_function(*args, **kwargs)  #2
            return wrapper_function
    
    celery = DummyCelery()
    """

    def ffff():
        pass
    
            
    class celery(object):
        class task(object):
            def __init__(self, *args, **kwargs):
                if len(args) > 0:
                    self.f = args[0]
        
            def __call__(self, *args, **kwargs):
                if len(args) > 0 and type(args[0]) == type(ffff):
                    return args[0]
                self.f(*args, **kwargs)