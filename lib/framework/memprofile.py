# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import logging
import xml.etree.ElementTree as ET
# third-party

# sjva 공용
from framework.logger import get_logger

# 패키지

# 로그
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
#########################################################

class HeapMon:
    #=====================================================================================
    def __init__(self):
        try:
            from guppy import hpy
            self.enabled = True
        except:
            self.enabled = False
        if self.enabled:
            self._h = hpy()
        self.hsize = 0
        self.hdiff = 0
    #=====================================================================================
    @staticmethod
    def getReadableSize(lv):
        if not isinstance(lv, (int, long)):
            return '0'
        if lv >= 1024*1024*1024*1024:
            s = "%4.2f TB" % (float(lv)/(1024*1024*1024*1024))
        elif lv >= 1024*1024*1024:
            s = "%4.2f GB" % (float(lv)/(1024*1024*1024))
        elif lv >= 1024*1024:
            s = "%4.2f MB" % (float(lv)/(1024*1024))
        elif lv >= 1024:
            s = "%4.2f KB" % (float(lv)/1024)
        else:
            s = "%d B" % lv
        return s
    #=====================================================================================
    def __repr__(self):
        if not self.enabled:
            return 'Not enabled. guppy module not found!'
        if self.hdiff > 0:
            s = 'Total %s, %s incresed' % \
                (self.getReadableSize(self.hsize), self.getReadableSize(self.hdiff))
        elif self.hdiff < 0:
            s = 'Total %s, %s decresed' % \
                (self.getReadableSize(self.hsize), self.getReadableSize(-self.hdiff))
        else:
            s = 'Total %s, not changed' % self.getReadableSize(self.hsize)
        return s
    #=====================================================================================
    def getHeap(self):
        if not self.enabled:
            return None
        return str(self._h.heap())
    #=====================================================================================
    def check(self, msg=''):
        if not self.enabled:
            return 'Not enabled. guppy module not found!'
        hdr = self.getHeap().split('\n')[0]
        chsize = long(hdr.split()[-2])
        self.hdiff = chsize - self.hsize
        self.hsize = chsize
        return '%s: %s'% (msg, str(self))
