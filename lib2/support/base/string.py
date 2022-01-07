import os, traceback, io, re, json, codecs
from . import logger

class SupportString(object):


    @classmethod
    def get_cate_char_by_first(cls, title):  # get_first
        value = ord(title[0].upper())
        if value >= ord('0') and value <= ord('9'): return '0Z'
        elif value >= ord('A') and value <= ord('Z'): return '0Z'
        elif value >= ord('가') and value < ord('나'): return '가'
        elif value < ord('다'): return '나'
        elif value < ord('라'): return '다'
        elif value < ord('마'): return '라'
        elif value < ord('바'): return '마'
        elif value < ord('사'): return '바'
        elif value < ord('아'): return '사'
        elif value < ord('자'): return '아'
        elif value < ord('차'): return '자'
        elif value < ord('카'): return '차'
        elif value < ord('타'): return '카'
        elif value < ord('파'): return '타'
        elif value < ord('하'): return '파'
        elif value <= ord('힣'): return '하'
        else: return '0Z'
    

