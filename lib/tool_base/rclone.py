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
    
