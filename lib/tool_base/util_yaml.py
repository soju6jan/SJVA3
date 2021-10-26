# -*- coding: utf-8 -*-
#########################################################
import os, sys, traceback, subprocess, json, platform
from framework import app, logger, path_data
from .file import ToolBaseFile

class ToolUtilYaml(object):

    @classmethod
    def copy_section(cls, source_file, target_file, section_name):
        try:
            if os.path.exists(source_file) == False:
                return 'not_exist_source_file'
            if os.path.exists(target_file) == False:
                return 'not_exist_target_file'
            lines = ToolBaseFile.read(source_file).split('\n')
            section = {}
            current_section_name = None
            current_section_data = None

            for line in lines:
                line = line.strip()
                if line.startswith('# SECTION START : '):
                    current_section_name = line.split(':')[1].strip()
                    current_section_data = []
                if current_section_data is not None:
                    current_section_data.append(line)
                if line.startswith('# SECTION END'):
                    section[current_section_name] = current_section_data
                    current_section_name = current_section_data = None

            if section_name not in section:
                return 'not_include_section'
            
            data = '\n'.join(section[section_name])
            source_data = ToolBaseFile.read(target_file)
            source_data = source_data + f"\n{data}\n"
            ToolBaseFile.write(source_data, target_file)
            return 'success'
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return 'exception'
