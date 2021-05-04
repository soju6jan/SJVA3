# -*- coding: utf-8 -*-
import os
import traceback
import shutil

from framework import app, celery, logger


class ToolShutil(object):
    
    # run_in_celery=True 이미 celery안에서 실행된다. 바로 콜한다.
    @staticmethod
    def move(source_path, target_path, run_in_celery=False):
        try:
            if app.config['config']['use_celery'] and run_in_celery == False:
                result = ToolShutil._move_task.apply_async((source_path, target_path))
                return result.get()
            else:
                return ToolShutil._move_task(source_path, target_path)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return ToolShutil._move_task(source_path, target_path)

    @staticmethod
    @celery.task
    def _move_task(source_path, target_path):
        try:
            logger.debug('_move_task:%s %s', source_path, target_path)
            shutil.move(source_path, target_path)
            logger.debug('_move_task end')
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False

    @staticmethod
    def move_exist_remove(source_path, target_path, run_in_celery=False):
        try:
            if app.config['config']['use_celery'] and run_in_celery == False:
                result = ToolShutil._move_exist_remove_task.apply_async((source_path, target_path))
                return result.get()
            else:
                return ToolShutil._move_exist_remove_task(source_path, target_path)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return ToolShutil._move_exist_remove_task(source_path, target_path)

    @staticmethod
    @celery.task
    def _move_exist_remove_task(source_path, target_path):
        try:
            target_file_path = os.path.join(target_path, os.path.basename(source_path))
            if os.path.exists(target_file_path):
                os.remove(source_path)
                return True
            logger.debug('_move_exist_remove:%s %s', source_path, target_path)
            shutil.move(source_path, target_path)
            logger.debug('_move_exist_remove end')
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False

    @staticmethod
    def copytree(source_path, target_path):
        try:
            if app.config['config']['use_celery']:
                result = ToolShutil._copytree_task.apply_async((source_path, target_path))
                return result.get()
            else:
                return ToolShutil._copytree_task(source_path, target_path)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return ToolShutil._copytree_task(source_path, target_path)

    @staticmethod
    @celery.task
    def _copytree_task(source_path, target_path):
        try:
            shutil.copytree(source_path, target_path)
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False

    # copy
    @staticmethod
    def copy(source_path, target_path):
        try:
            if app.config['config']['use_celery']:
                result = ToolShutil._copy_task.apply_async((source_path, target_path))
                return result.get()
            else:
                return ToolShutil._copy_task(source_path, target_path)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return ToolShutil._copy_task(source_path, target_path)

    @staticmethod
    @celery.task
    def _copy_task(source_path, target_path):
        try:
            shutil.copy(source_path, target_path)
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False

    # rmtree
    @staticmethod
    def rmtree(source_path):
        try:
            if app.config['config']['use_celery']:
                result = ToolShutil._rmtree_task.apply_async((source_path,))
                return result.get()
            else:
                return ToolShutil._rmtree_task(source_path)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return ToolShutil._rmtree_task(source_path)

    @staticmethod
    @celery.task
    def _rmtree_task(source_path):
        try:
            shutil.rmtree(source_path)
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False   

    @staticmethod
    def remove(remove_path):
        try:
            logger.debug('CELERY os.remove start : %s', remove_path)
            if app.config['config']['use_celery']:
                result = ToolShutil._remove_task.apply_async((remove_path,))
                return result.get()
            else:
                return ToolShutil._remove_task(remove_path)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return ToolShutil._remove_task(remove_path)
        finally:
            logger.debug('CELERY os.remove end : %s', remove_path)

    @staticmethod
    @celery.task
    def _remove_task(remove_path):
        try:
            os.remove(remove_path)
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return False   