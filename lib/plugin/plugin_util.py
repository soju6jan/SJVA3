import os, traceback, io, re
from . import logger

class PluginUtil(object):

    @classmethod
    def make_info_json(cls, info, plugin_py_filepath):
        try:
            from framework import SystemModelSetting
            if info['developer'] == SystemModelSetting.get('sjva_me_user_id'):
                from tool_base import ToolUtil
                filename = os.path.join(os.path.dirname(plugin_py_filepath), 'info.json')
                ToolUtil.save_dict(info, filename)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
