import os, traceback, io, re, platform
from . import logger
from . import ToolSubprocess
from . import ToolUtil

class ToolOSCommand(object):

    @classmethod
    def get_size(cls, path):
        if platform.system() == 'Windows':
            pass
        else:
            command = ['du', '-bs', path]
            data = ToolSubprocess.execute_command_return(command)
            ret = {}
            tmp = data.split('\t')
            ret['target'] = tmp[1].strip()
            ret['size'] = int(tmp[0].strip())
            ret['sizeh'] = ToolUtil.sizeof_fmt(ret['size'])
        return ret
            