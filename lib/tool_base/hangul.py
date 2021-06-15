# -*- coding: utf-8 -*-
#########################################################
import os, traceback, io, re
from . import logger

class ToolHangul(object):


    @classmethod
    def is_include_hangul(cls, text):
        try:
            hanCount = len(re.findall(u'[\u3130-\u318F\uAC00-\uD7A3]+', text))
            return hanCount > 0
        except:
            return False

    @classmethod
    def language_info(cls, text):
        try:
            text = text.strip().replace(' ', '')
            all_count = len(text)
            han_count = len(re.findall('[\u3130-\u318F\uAC00-\uD7A3]', text))
            eng_count = len(re.findall('[a-zA-Z]', text))
            han_percent = int(han_count * 100 / all_count)
            eng_percent = int(eng_count * 100 / all_count)
            return (han_percent, eng_percent)
        except:
            return False