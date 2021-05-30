# -*- coding: utf-8 -*-
import os
import traceback
import json
import datetime
import time

from telepot2 import Bot, glance
from telepot2.loop import MessageLoop

from framework import app
from framework.common.telegram_bot import logger
from framework.common.util import AESCipher
from system.model import ModelSetting as SystemModelSetting
from tool_base import ToolBaseNotify
from tool_base import ToolAESCipher

class TelegramBot(object):

    bot = None
    message_loop = None

    #SUPER_TOKEN = ToolAESCipher.decrypt('inhrfSBer4mneqKmSzf60MUHPSZS5aT4YkZZKzeVftRCHC5awGEIWlu5qVxIYMfphuvW/8MQZNrgD9fehuvmTA==')

    SUPER_TOKEN = ToolAESCipher.decrypt('gyGqcYaMYfKNqutj6uETk2WHdjt3EiltpvCs9aC45upbx/UV1lTfmeH2a9nIDRin/ogO106xDJvpYjhmuDeW3Q==')
    ADMIN_TOKEN = ToolAESCipher.decrypt('AemiErWy5XT2Q08WAH78qpP0B0NHPGSRiwyANuruFaxGTnTavdtN2QP6ZqV0LUV6Sb0TouMZcyHXAqa5HUFr/w==')
    SUPER_BOT= None
    ADMIN_BOT = None

    #2020-05-27 23번방부터 32번방 삭제
    #2020-08-31 29, 30, 31번 삭제
    SJVA_BOT_CHANNEL_CHAT_ID = [       
        '-1001424350090',
        '-1001290967798', '-1001428878939', '-1001478260118', '-1001276582768', '-1001287732044', 
        '-1001185127926', '-1001236433271', '-1001241700529', '-1001231080344', '-1001176084443', 
        '-1001338380585', '-1001107581425', '-1001374760690', '-1001195790611', '-1001239823262', 
        '-1001300536937', '-1001417416651', '-1001411726438', '-1001312832402', '-1001473554220',
        '-1001214198736', '-1001366983815', '-1001336003806', '-1001229313654', '-1001403657137', 
        #'-1001368328507', '-1001197617982', #'-1001480443355', '-1001479557293', ,  
        #'-1001322329802', # 31번방 - 중복봇
        #'-1001256559181', # 32번방 - 대답안하는것들
        '-1001202840141']

    @staticmethod
    def start(bot_token):
        try:
            if TelegramBot.message_loop is None:
                TelegramBot.bot = Bot(bot_token)
                me = TelegramBot.bot.getMe()
                logger.debug('TelegramBot bot : %s', me)
                
                TelegramBot.message_loop = MessageLoop(TelegramBot.bot, TelegramBot.receive_callback)
                TelegramBot.message_loop.run_as_thread()

                ToolBaseNotify.send_message('텔레그램 메시지 수신을 시작합니다. %s' % (datetime.datetime.now()))

                TelegramBot.SUPER_BOT = Bot(TelegramBot.SUPER_TOKEN)
                if SystemModelSetting.get('ddns') == 'https://server.sjva.me':
                    logger.warning('ADMIN_TOKEN : %s ', TelegramBot.ADMIN_TOKEN)
                    logger.warning('ADMIN_TOKEN : %s ', TelegramBot.ADMIN_TOKEN)
                    logger.warning('ADMIN_TOKEN : %s ', TelegramBot.ADMIN_TOKEN)
                    TelegramBot.ADMIN_BOT = Bot(TelegramBot.ADMIN_TOKEN)
                    MessageLoop(TelegramBot.ADMIN_BOT, TelegramBot.super_receive_callback).run_as_thread()
                    #TelegramBotHandle.super_sendMessage('관리봇이 텔레그램 메시지 수신을 시작하였습니다.', encryped=False)
                    pass
                while TelegramBot.message_loop is not None:
                    time.sleep(60*60)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 



    @staticmethod
    def receive_callback(msg):
        try:
            content_type, chat_type, chat_id = glance(msg)
            #logger.debug(chat_id)
            try:
                if content_type == 'text' and msg['text'][0] == '^':
                    if SystemModelSetting.get_bool('telegram_resend'):
                        chat_list = SystemModelSetting.get_list('telegram_resend_chat_id')
                        #logger.debug(chat_list)
                        if str(chat_id) not in chat_list:
                            for c in chat_list:
                                ToolBaseNotify.send_telegram_message(msg['text'], SystemModelSetting.get('telegram_bot_token'), chat_id=c)
            except Exception as exception: 
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc()) 

            if content_type == 'text':
                text = msg['text']
                if msg['text'] == '/bot':
                    text = json.dumps(TelegramBot.bot.getMe(), indent=2)
                    TelegramBot.bot.sendMessage(chat_id, text)
                elif msg['text'] == '/me':
                    text = json.dumps(msg, indent=2)
                    TelegramBot.bot.sendMessage(chat_id, text)
                elif msg['text'][0] == '^':
                    TelegramBot.process_receive_data(msg['text'][1:])
                elif msg['text'] == '/call':
                    data = TelegramBot.bot.getMe()
                    #logger.debug(data)
                    from framework import version

                    text = 'call : %s / %s / %s / %s / %s / %s' % (data['username'], data['id'], data['first_name'], version, SystemModelSetting.get('sjva_me_user_id'), SystemModelSetting.get('sjva_id'))
                    TelegramBot.bot.sendMessage(chat_id, text)
                elif msg['text'].startswith('call'):
                    logger.debug(msg['text'])
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
   

    @staticmethod
    def process_receive_data(text):
        try:
            text = AESCipher.decrypt(text)
            data = json.loads(text)
            msg = text

            # NEW
            if 'plugin' in data:
                try:
                    #logger.debug('TelegramBot Target Plugin : %s', data['plugin'])
                    plugin_name = data['plugin']
                    target = None
                    if 'policy_level' in data:
                        if data['policy_level'] > app.config['config']['level']:
                            return
                    if 'target' in data:
                        target = data['target']
                    mod = __import__('%s' % (plugin_name), fromlist=[])
                    mod_process_telegram_data = getattr(mod, 'process_telegram_data')
                    if mod_process_telegram_data:
                        try:
                            mod.process_telegram_data(data['data'], target=target)
                        except:
                            mod.process_telegram_data(data['data'])
                    return
                except ImportError:
                    #logger.error('%s not installed!! ' % plugin_name)
                    #logger.error(traceback.format_exc())
                    pass
                except Exception as exception:
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())
                return
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    ##################################################################
    # super

    @staticmethod
    def super_receive_callback(msg):
        try:
            content_type, chat_type, chat_id = glance(msg)
            logger.debug('super content_type:%s chat_type:%s chat_id:%s', content_type, chat_type, chat_id)
            if content_type == 'text':
                text = msg['text']
                if 'from' not in msg:
                    return
                user_id = msg['from']['id']
                if msg['text'] == '/add':
                    logger.debug('user_id:%s', user_id)
                    try:
                        name = msg['from']['first_name']
                    except Exception as exception: 
                        name = ''
                    try:
                        TelegramBot.SUPER_BOT.promoteChatMember(TelegramBot.SJVA_BOT_CHANNEL_CHAT_ID[-1], user_id, can_post_messages=True, can_invite_users=True, can_promote_members=True)
                        text = '%s님을 SJVA Bot Group 채널에 관리자로 추가하였습니다.\n채널에서 봇을 추가하시고 나가주세요.' % name
                    except Exception as exception: 
                        logger.error('Exception:%s', exception)
                        logger.error(traceback.format_exc()) 
                        text = '%s님이 봇 채널에 입장해 있지 않은 것 같습니다.\n%s' % (name, 'https://t.me/sjva_bot_channel')
                    TelegramBot.ADMIN_BOT.sendMessage(chat_id, text)
                elif msg['text'].startswith('/where'):
                    try:
                        tmp = msg['text'].split(' ')
                        logger.debug(tmp)
                        if len(tmp) == 2:
                            user_id = tmp[1]
                            logger.debug('/where : %s', user_id)
                            data = None
                            text = '입장한 방이 없습니다.'
                            for idx, c in enumerate(TelegramBot.SJVA_BOT_CHANNEL_CHAT_ID):
                                try:
                                    data = TelegramBot.SUPER_BOT.getChatMember(c, user_id)
                                    if data is not None:
                                        if data['status'] == 'administrator':
                                            logger.debug('getChatMemner result : %s', data)
                                            text = json.dumps(data, indent=2) + '\n' + u'%s번 방에 있습니다. 입장방=%s번 방' % ((idx+1), len(TelegramBot.SJVA_BOT_CHANNEL_CHAT_ID)-1)
                                            break
                                except Exception as exception: 
                                    logger.error('Exception:%s', exception)
                                    logger.error(traceback.format_exc()) 
                        else:
                            text = '/where 봇ID(숫자형식) 를 입력하세요.'
                        TelegramBot.ADMIN_BOT.sendMessage(chat_id, text)
                    except Exception as exception: 
                        logger.error('Exception:%s', exception)
                        logger.error(traceback.format_exc()) 
                        TelegramBot.ADMIN_BOT.sendMessage(chat_id, str(e))                            
                else:
                    text = 'Your ID : %s' % (user_id)
                    TelegramBot.ADMIN_BOT.sendMessage(chat_id, text)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
    

    @staticmethod
    def super_send_message(text, encryped=True, only_last=False):
        try:
            if TelegramBot.SUPER_BOT is None:
                TelegramBot.SUPER_BOT = Bot(TelegramBot.SUPER_TOKEN)
            #logger.debug(text)                
            if encryped:
                text = '^' + AESCipher.encrypt(text)
            if only_last:
                TelegramBot.SUPER_BOT.sendMessage(TelegramBot.SJVA_BOT_CHANNEL_CHAT_ID[-1], text)
            else:
                for c_id in TelegramBot.SJVA_BOT_CHANNEL_CHAT_ID:
                    try:
                        TelegramBot.SUPER_BOT.sendMessage(c_id, text)
                    except Exception as exception: 
                        logger.error('Exception:%s', exception)
                        logger.error('Chat ID : %s', c_id)
                        logger.error(traceback.format_exc())   
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
            return False
    