import os, sys, traceback, subprocess, json, platform
from . import logger


class SupportProcess(object):

    @classmethod
    def execute(cls, command, format=None, shell=False, env=None, timeout=1000):
        logger.debug(command)
        try:
            if platform.system() == 'Windows':
                command =  ' '.join(command)

            iter_arg =  ''
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=shell, env=env, encoding='utf8')
            try:
                process_ret = process.wait(timeout=timeout) # wait for the subprocess to exit
            except:
                import psutil
                process = psutil.Process(process.pid)
                for proc in process.children(recursive=True):
                    proc.kill()
                process.kill()
                return "timeout"
            ret = []
            with process.stdout:
                for line in iter(process.stdout.readline, iter_arg):
                    ret.append(line.strip())

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
        except Exception as e: 
            logger.error(f'Exception:{str(e)}', )
            logger.error(traceback.format_exc())
            logger.error('command : %s', command)
            