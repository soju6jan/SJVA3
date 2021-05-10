# -*- coding: utf-8 -*-
#########################################################
import os, sys, traceback, subprocess, json, platform
from framework import app, logger


class ToolSubprocess(object):

    @classmethod
    def execute_command_return(cls, command, format=None, force_log=False):
        try:
            logger.debug('execute_command_return : %s', ' '.join(command))
            if app.config['config']['is_py2']:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                ret = []
                with process.stdout:
                    for line in iter(process.stdout.readline, b''):
                        ret.append(line.strip())
                        if force_log:
                            logger.debug(ret[-1])
                    process.wait() # wait for the subprocess to exit
            else:
                process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
                ret = []
                with process.stdout:
                    for line in iter(process.stdout.readline, ''):
                        ret.append(line.strip())
                        if force_log:
                            logger.debug(ret[-1])
                    process.wait() # wait for the subprocess to exit


            if format is None:
                ret2 = '\n'.join(ret)
            elif format == 'json':
                try:
                    index = 0
                    for idx, tmp in enumerate(ret):
                        #logger.debug(tmp)
                        if tmp.startswith('{') or tmp.startswith('['):
                            index = idx
                            break
                    ret2 = json.loads(''.join(ret[index:]))
                except:
                    ret2 = None

            return ret2
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            logger.error('command : %s', command)
