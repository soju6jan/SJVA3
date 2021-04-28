# -*- coding: utf-8 -*-
import sys
if sys.version_info[0] == 2: 
    import Queue as py_queue
    import urllib2 as py_urllib2  #Request, urlopen
    import urllib as py_urllib #quote, unuote, urlencode
    py_reload = reload
    def py_unicode(v):
        return unicode(v)
else: 
    import queue as py_queue
    import urllib.request as py_urllib2
    import urllib.parse as py_urllib #urlencode
    #from imp import reload as py_reload
    from importlib import reload as py_reload
    def py_unicode(v):
        return str(v)