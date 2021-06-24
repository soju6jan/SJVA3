import os
import traceback
import json
import datetime
import time

from telepot2 import Bot, glance
from telepot2.loop import MessageLoop

from framework import app
from . import logger

from tool_base import ToolAESCipher

class ToolTelegram(object):
    SUPER_BOT = None
    SJVA_BOT_CHANNEL_CHAT_ID = app.config['DEFINE']['SJVA_BOT_CHANNEL_CHAT_ID']

    @classmethod
    def broadcast(cls, text, encrypted=True, only_last=False):
        try:
            if cls.SUPER_BOT is None:
                cls.SUPER_BOT = Bot(ToolAESCipher.decrypt(app.config['DEFINE']['SUPER_BOT_TOKEN']).decode('utf-8'))
            #logger.debug(text)                
            if encrypted:
                text = '^' + ToolAESCipher.encrypt(text)
            if only_last:
                cls.SUPER_BOT.sendMessage(cls.SJVA_BOT_CHANNEL_CHAT_ID[-1], text)
            else:
                for c_id in cls.SJVA_BOT_CHANNEL_CHAT_ID:
                    try:
                        cls.SUPER_BOT.sendMessage(c_id, text)
                    except Exception as exception: 
                        logger.error('Exception:%s', exception)
                        logger.error('Chat ID : %s', c_id)
                        logger.error(traceback.format_exc())   
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
            return False


#ToolTelegram().broadcast('1', encrypted=False)





    
