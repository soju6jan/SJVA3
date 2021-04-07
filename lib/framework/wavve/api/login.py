# -*- coding: utf-8 -*-
import traceback
import json

from framework import py_urllib
from framework.wavve.api import logger, session, config, logger


def do_login(id, pw, json_return=False):
    try:
        body = {
            "type": "general",
            "id": id,
            "pushid": "",
            "password": pw,
            "profile": "0",
            "networktype": "",
            "carrier": "",
            "mcc": "",
            "mnc": "",
            "markettype": "unknown",
            "adid": "",
            "simoperator": "",
            "installerpackagename": ""
        }
        url = "%s/login?%s" % (config['base_url'], py_urllib.urlencode(config['base_parameter']))
        response = session.post(url, json=body, headers=config['headers'])
        data = response.json()
        if 'credential' in data:
            if json_return:
                return data
            else:
                return data['credential']
        else:
            logger.debug('login fail!!')
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
    return

    
def get_baseparameter():
    try:
        #if config['base_parameter']['credential'] is None:
        #    from .login import login
        #    login(config['wavve_id'], config['wavve_pw'])
        return config['base_parameter'].copy()
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
