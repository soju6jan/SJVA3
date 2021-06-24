# -*- coding: utf-8 -*-
#########################################################

import os
import traceback, time
import random

import requests
from discord_webhook import DiscordWebhook, DiscordEmbed

from framework import app
from . import logger


server_plugin_ddns = app.config['DEFINE']['METADATA_SERVER_URL']
webhook_list = app.config['DEFINE']['WEBHOOK_LIST_FOR_IMAGE_PROXY']

class ToolExpandDiscord(object):

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
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
        return False


    @classmethod
    def discord_proxy_set_target(cls, source, target):
        try:
            return
            if source is None or target is None:
                return False
            if requests.get(target).status_code != 200:
                return False
            if target.startswith('https://images-ext-') and target.find('discordapp.net') != -1:
                from framework import py_urllib
                from system.model import ModelSetting as SystemModelSetting
                url = '{server_plugin_ddns}/server/normal/discord_proxy/set_target?source={source}&target={target}&user={user}'.format(server_plugin_ddns=server_plugin_ddns, source=py_urllib.quote_plus(source), target=py_urllib.quote_plus(target), user=SystemModelSetting.get('sjva_me_user_id'))
                data = requests.get(url).json()
        except Exception as exception: 
            logger.error('server disconnect..')
        return True

    

    
    @classmethod
    def discord_proxy_image(cls, image_url, webhook_url=None, retry=True):
        #2020-12-23
        #image_url = None
        if image_url == '' or image_url is None:
            return
        data = None
        
        if webhook_url is None or webhook_url == '':
            webhook_url =  webhook_list[random.randint(10,len(webhook_list)-1)]  # sjva 채널

        try:
            from framework import py_urllib
            webhook = DiscordWebhook(url=webhook_url, content='')
            embed = DiscordEmbed()
            embed.set_timestamp()
            embed.set_image(url=image_url)
            webhook.add_embed(embed)
            import io
            byteio = io.BytesIO()
            webhook.add_file(file=byteio.getvalue(), filename='dummy')
            response = webhook.execute()
            data = None
            if type(response) == type([]):
                if len(response) > 0:
                    data = response[0].json()
            else:
                data = response.json()    
            
            if data is not None and 'embeds' in data:
                target = data['embeds'][0]['image']['proxy_url']
                if requests.get(target).status_code == 200:
                    return target
                else:
                    return image_url
            else:
                raise Exception(str(data))
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            if retry:
                time.sleep(1)
                return cls.discord_proxy_image(image_url, webhook_url=None, retry=False)
            else:
                return image_url

    
    @classmethod
    def discord_proxy_image_localfile(cls, filepath, retry=True):
        data = None
        webhook_url =  webhook_list[random.randint(0,9)]  # sjva 채널

        try:
            from discord_webhook import DiscordWebhook, DiscordEmbed
            webhook = DiscordWebhook(url=webhook_url, content='')
            import io
            with open(filepath, 'rb') as fh:
                byteio = io.BytesIO(fh.read())
            webhook.add_file(file=byteio.getvalue(), filename='image.jpg')
            embed = DiscordEmbed()
            embed.set_image(url="attachment://image.jpg")
            response = webhook.execute()
            data = None
            if type(response) == type([]):
                if len(response) > 0:
                    data = response[0].json()
            else:
                data = response.json()    
            
            if data is not None and 'attachments' in data:
                target = data['attachments'][0]['url']
                if requests.get(target).status_code == 200:
                    return target
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

            if retry:
                time.sleep(1)
                return cls.discord_proxy_image_localfile(filepath, retry=False)


    # RSS에서 자막 올린거
    @classmethod    
    def discord_cdn(cls, byteio=None, filepath=None, filename=None, webhook_url=None, content='', retry=True):
        data = None
        if webhook_url is None:
            webhook_url =  webhook_list[random.randint(0,9)]  # sjva 채널

        try:
            from discord_webhook import DiscordWebhook, DiscordEmbed
            webhook = DiscordWebhook(url=webhook_url, content=content)
            if byteio is None and filepath is not None:
                import io
                with open(filepath, 'rb') as fh:
                    byteio = io.BytesIO(fh.read())
                
            webhook.add_file(file=byteio.getvalue(), filename=filename)
            embed = DiscordEmbed()
            response = webhook.execute()
            data = None
            if type(response) == type([]):
                if len(response) > 0:
                    data = response[0].json()
            else:
                data = response.json()    
            
            if data is not None and 'attachments' in data:
                target = data['attachments'][0]['url']
                if requests.get(target).status_code == 200:
                    return target
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            if retry:
                time.sleep(1)
                return cls.discord_proxy_image_localfile(filepath, retry=False)
