# -*- coding: utf-8 -*-
#########################################################

import os
import traceback

from discord_webhook import DiscordWebhook, DiscordEmbed
from telepot import Bot, glance
from telepot.loop import MessageLoop

from . import logger

class ToolBaseNotify(object):

    @classmethod
    def send_message(cls, text, message_id=None, image_url=None):
        from system.model import ModelSetting as SystemModelSetting
        if SystemModelSetting.get_bool('notify_advaned_use'):
            return cls.send_advanced_message(text, image_url=image_url, message_id=message_id)
        else:
            if SystemModelSetting.get_bool('notify_telegram_use'):
                cls.send_telegram_message(text, image_url=image_url, bot_token=SystemModelSetting.get('notify_telegram_token'), chat_id=SystemModelSetting.get('notify_telegram_chat_id'))
            if SystemModelSetting.get_bool('notify_discord_use'):
                cls.send_discord_message(text, image_url=image_url, webhook_url=SystemModelSetting.get('notify_discord_webhook')) 

    @classmethod
    def send_advanced_message(cls, text, image_url=None, policy=None, message_id=None):
        from system.model import ModelSetting as SystemModelSetting
        try:
            if policy is None:
                policy = SystemModelSetting.get('notify_advaned_policy')

            if message_id is None:
                message_id = 'DEFAULT'
            
            policy_list = cls._make_policy_dict(policy)
            #logger.debug(policy_list)
            #logger.debug(message_id)
            if message_id.strip() not in policy_list:
                message_id = 'DEFAULT'
            
            for tmp in policy_list[message_id.strip()]:
                if tmp.startswith('http'):
                    cls.send_discord_message(text, image_url=image_url, webhook_url=tmp)
                elif tmp.find(',') != -1:
                    tmp2 = tmp.split(',')
                    cls.send_telegram_message(text, image_url=image_url, bot_token=tmp2[0], chat_id=tmp2[1])
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
            #logger.debug('Chatid:%s', chat_id)
        return False

    @classmethod
    def _make_policy_dict(cls, policy):
        try:
            ret = {}
            for t in policy.split('\n'):
                t = t.strip()
                if t == '' or t.startswith('#'):
                    continue
                else:
                    tmp2 = t.split('=')
                    if len(tmp2) != 2:
                        continue
                    ret[tmp2[0].strip()] = [x.strip() for x in tmp2[1].split('|')]
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
        return False

    @classmethod
    def send_discord_message(cls, text, image_url=None, webhook_url=None):
        from system.model import ModelSetting as SystemModelSetting
        try:
            if webhook_url is None:
                webhook_url = SystemModelSetting.get('notify_discord_webhook')
            
            webhook = DiscordWebhook(url=webhook_url, content=text)
            if image_url is not None:
                embed = DiscordEmbed()
                embed.set_timestamp()
                embed.set_image(url=image_url)
                webhook.add_embed(embed)
            response = webhook.execute()
            #discord = response.json()
            #logger.debug(discord)
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
        return False

    @classmethod
    def send_telegram_message(cls, text, bot_token=None, chat_id=None, image_url=None,  disable_notification=None):
        from system.model import ModelSetting as SystemModelSetting
        try:
            if bot_token is None:
                bot_token = SystemModelSetting.get('notify_telegram_token')
            
            if chat_id is None:
                chat_id = SystemModelSetting.get('notify_telegram_chat_id')

            if disable_notification is None:
                disable_notification = SystemModelSetting.get_bool('notify_telegram_disable_notification')

            bot = Bot(bot_token)
            if image_url is not None:
                #bot.sendPhoto(chat_id, text, caption=caption, disable_notification=disable_notification)
                bot.sendPhoto(chat_id, image_url, disable_notification=disable_notification)
            bot.sendMessage(chat_id, text, disable_web_page_preview=True, disable_notification=disable_notification)
            #elif mime == 'video':
            #    bot.sendVideo(chat_id, text, disable_notification=disable_notification)
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
            logger.debug('Chatid:%s', chat_id)
        return False

