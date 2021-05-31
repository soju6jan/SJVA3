# -*- coding: utf-8 -*-
#########################################################
import os, sys, traceback, subprocess, json, platform
from framework import app, logger, path_data
from .subprocess import ToolSubprocess

class ToolRclone(object):

    @classmethod
    def lsjson(cls, remote_path, rclone_path='rclone', config_path=os.path.join(path_data, 'db', 'rclone.conf'), option=None):
        try:
            command = [rclone_path, '--config', config_path, 'lsjson', remote_path]
            if option is not None:
                command += option
            logger.warning(' '.join(command))
            ret = ToolSubprocess.execute_command_return(command, format='json')
            if ret is not None:
                ret = list(sorted(ret, key=lambda k:k['Path']))
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @classmethod
    def size(cls, remote_path, rclone_path='rclone', config_path=os.path.join(path_data, 'db', 'rclone.conf'), option=None):
        try:
            command = [rclone_path, '--config', config_path, 'size', remote_path, '--json']
            if option is not None:
                command += option
            ret = ToolSubprocess.execute_command_return(command, format='json')
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    

    @classmethod
    def getid(cls, remote_path, rclone_path='rclone', config_path=os.path.join(path_data, 'db', 'rclone.conf'), option=None):
        try:
            command = [rclone_path, '--config', config_path, 'backend', 'getid', remote_path]
            if option is not None:
                command += option
            ret = ToolSubprocess.execute_command_return(command)
            if ret is not None and (len(ret.split(' ')) > 1 or ret == ''):
                ret = None
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    

    @classmethod
    def rmdir(cls, remote_path, rclone_path='rclone', config_path=os.path.join(path_data, 'db', 'rclone.conf'), option=None):
        try:
            command = [rclone_path, '--config', config_path, 'rmdir', remote_path, '-vv']#, '--drive-use-trash=false', '-vv']
            if option is not None:
                command += option
            ret = ToolSubprocess.execute_command_return(command)
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    @classmethod
    def config_list(cls, rclone_path='rclone', config_path=os.path.join(path_data, 'db', 'rclone.conf'), option=None):
        try:
            command = [rclone_path, '--config', config_path, 'config', 'dump']#, '--drive-use-trash=false', '-vv']
            if option is not None:
                command += option
            ret = ToolSubprocess.execute_command_return(command, format='json')
            for key, value in ret.items():
                if 'token' in value and value['token'].startswith('{'):
                    value['token'] = json.loads(value['token'])
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())





    @classmethod
    def move_server_side(cls, source, target, rclone_path='rclone', config_path=os.path.join(path_data, 'db', 'rclone.conf'), option=None):
        try:
            
            command = [rclone_path, '--config', config_path, 'move', source, target, '--drive-server-side-across-configs=true', '--delete-empty-src-dirs', '-vv']
            if option is not None:
                command += option
            logger.debug(' '.join(command))
            ret = ToolSubprocess.execute_command_return(command)
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    

            