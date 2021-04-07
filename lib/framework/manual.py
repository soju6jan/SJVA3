# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import requests
import json

# third-party
from flask import request, Markup, jsonify
import markdown
# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, path_app_root, path_data
from framework.job import Job
from framework.util import Util

# 패키지

# 로그
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
#########################################################


    
@app.route('/manual/<sub>', methods=['GET', 'POST'])
def manual(sub):
    logger.debug('MANUAL %s %s', package_name, sub)
    if sub == 'menu':
        try:
            url = request.form['url']
            #if not url.startswith('http'):
            #    url = '%s%s' % (request.host_url, url)
            #res = requests.get(url)
            ret = {}
            if url.startswith('http'):
                ret['menu'] = requests.get(url).json()
            else:
                data = fileread(url)
                ret['menu'] = json.loads(data)
            #ret['content'] = {}
            for r in ret['menu']:
                if r['type'] == 'file':
                   r['content'] = Markup(markdown.markdown(fileread(r['arg']))) 
                elif r['type'] == 'url':
                    if r['url'].startswith('http'):
                        res = requests.get(r['url'])
                        #ret['content'][r['title']] = Markup(markdown.markdown(res.text))
                        r['content'] = Markup(markdown.markdown(res.text))
            #logger.debug(ret)
            return jsonify(ret)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

def fileread(filename):
    try:
        import io
        filename = os.path.join(path_app_root, 'manual', filename)
        file_is = io.open(filename, 'r', encoding="utf8")  ## 3)
        text_str = file_is.read()  ## 4)
        #print(text_str)  
        file_is.close()  ## 5)
        return text_str
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
