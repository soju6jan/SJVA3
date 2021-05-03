

# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys

from framework import app, logger, path_app_root
try:
    from celery import Celery

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
    from functools import wraps
    class DummyCelery:
        def task(self, original_function):
            @wraps(original_function)
            def wrapper_function(*args, **kwargs):  #1
                return original_function(*args, **kwargs)  #2
            return wrapper_function
    
    celery = DummyCelery()
