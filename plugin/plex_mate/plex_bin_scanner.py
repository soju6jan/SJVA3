# python
import os, sys, traceback, re, json, threading, time, shutil, fnmatch, glob, platform
from datetime import datetime, timedelta
# third-party
import requests, sqlite3

# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from tool_base import ToolShutil, d, ToolUtil, ToolBaseFile, ToolOSCommand, ToolSubprocess

from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting



class PlexBinaryScanner(object):
    
    @classmethod
    def scan_refresh(cls, section_id, folderpath):
        try:
            if platform.system() == 'Windows':
                cmd = f'"{ModelSetting.get("base_bin_scanner")}" --scan  --refresh --section {section_id} --directory "{folderpath}"'
                logger.warning(cmd)
                ToolSubprocess.execute_command_return(cmd)
            else:
                #env=dict(FOO='BAR', **os.environ))
                #command = [f'"{ModelSetting.get("base_bin_scanner")}"', '--scan', '--refresh', '--section', section_id, '--directory', f'"{folderpath}"']
                command = [ModelSetting.get("base_bin_scanner"), '--scan', '--refresh', '--section', section_id, '--directory', folderpath]
                #logger.warning(' '.join(command))
                #logger.error(os.environ())
                #ret = ToolSubprocess.execute_command_return(command,  env=dict(PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR='/var/lib/plexmediaserver/Library/Application Support', **os.environ))
                ret = ToolSubprocess.execute_command_return(command,  env=dict(PLEX_MEDIA_SERVER_APPLICATION_SUPPORT_DIR=f"{os.path.dirname(os.path.dirname(ModelSetting.get('base_path_metadata')))}", **os.environ))
                logger.warning(ret)
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        return False 
