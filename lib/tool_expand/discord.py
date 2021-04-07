# -*- coding: utf-8 -*-
#########################################################

import os
import traceback, time
import random

import requests
from discord_webhook import DiscordWebhook, DiscordEmbed

from framework import app
from . import logger


server_plugin_ddns = 'https://meta.sjva.me'


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
            #discord = response.json()
            #logger.debug(discord)
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
        return False

    """
    @classmethod
    def discord_proxy_get_target(cls, image_url):  #주석처리함
        try:
            return
            from framework import py_urllib
            url = '{server_plugin_ddns}/server/normal/discord_proxy/get_target?source={source}'.format(server_plugin_ddns=server_plugin_ddns, source=py_urllib.quote_plus(image_url))
            data = requests.get(url).json()
            if data['ret'] == 'success':
                if data['target'].startswith('https://images-ext-') and requests.get(data['target']).status_code == 200:
                    return data['target']
        except Exception as exception: 
            logger.error('server disconnect..')
    """

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


    #webhook_list = ['https://discordapp.com/api/webhooks/794558958164639754/BGEDja1NFyKSlPlHQdwrSJ0mAGBVppFT2etVY4QRp9tUoQQz_d4QzmhwtyW5127vAK6b', 'https://discordapp.com/api/webhooks/794641397617131592/-Sz4mlkBzakneJ7JhrzxhrpV21gB6xlFBYHUMARFIlJgsO1t7SznFoHs58vrIs30Jh02', 'https://discordapp.com/api/webhooks/794642181049679924/-PfiwTmXmhNUIa7LYxZsBVW4nZ5cO-aA408PM6OmgkRGSl0ddxCaeGONAB9Ev-akGki9', 'https://discordapp.com/api/webhooks/794642233444794459/VMCqvfirE7trfmAaShOcbzrDTDSvy2t5RhV7hAmERgr_sQ6dCppVoTmrc1KrJrL5lu4P']

    webhook_list = [
        'https://discord.com/api/webhooks/810372911872344114/7yLzAhRnBUcsbCB-dIG16tCEEw3Z7QkBSa9eKw7J7o7fQhF8M2o4L-e-WIXOYznxnFNO',
        'https://discord.com/api/webhooks/810373137225089035/twZOBuMzJlxyiV87e0Ubers8yTeKd7a71mjGiBTMube7WbN5S3PlxlZYVa2ee3XeQjn3',
        'https://discord.com/api/webhooks/810373216547766282/GFAS8enTYSoc58vqd7j3_ehrCT8odat8J1LuuAzluTtjxlAOLCNBQtsx7mhiMVC7BTqk',
        'https://discord.com/api/webhooks/810373281127333928/Jpmrq9VUp9pQZLgD3RdDIxN-xP_ZuHUSqoWYUgpYIxeTBpS0HVhdotX9tepYDlMQmnMi',
        'https://discord.com/api/webhooks/810373348776476683/h_uJLBBlHzD0w_CG0nUajFO-XEh3fvy-vQofQt1_8TMD7zHiR7a28t3jF-xBCP6EVlow',
        'https://discord.com/api/webhooks/810373405508501534/wovhf-1pqcxW5h9xy7iwkYaf8KMDjHU49cMWuLKtBWjAnj-tzS1_j8RJ7tsMyViDbZCE',
        'https://discord.com/api/webhooks/796558388326039552/k2VV356S1gKQa9ht-JuAs5Dqw5eVkxgZsLUzFoxmFG5lW6jqKl7zCBbbKVhs3pcLOetm',
        'https://discord.com/api/webhooks/810373566452858920/Qf2V8BoLOy2kQzlZGHy5HZ1nTj7lK72ol_UFrR3_eHKEOK5fyR_fQ8Yw8YzVh9EQG54o',
        'https://discord.com/api/webhooks/810373654411739157/SGgdO49OCkTNIlc_BSMSy7IXQwwXVonG3DsVfvBVE6luTCwvgCqEBpEk30WBeMMieCyI',
        'https://discord.com/api/webhooks/810373722341900288/FwcRJ4YxYjpyHpnRwF5f2an0ltEm8JPqcWeZqQi3Qz4QnhEY-kR2sjF9fo_n6stMGnf_',
        
        'https://discord.com/api/webhooks/810374116652744704/93MJfYgZSUF8M40Rnk_UoZEbLv0IbXdQjoZBDRJzHxbxq0YyOo9ngh2p6iJ6BjTkymQL',
        'https://discord.com/api/webhooks/810374206168104960/Xv4p9xRH5W3Fmb7aqzDG22svg5oAc15jyMU-1iPR9yK7HmO4X9efqWclR48yf_lwX0HO',
        'https://discord.com/api/webhooks/810374244222500864/4xbuvs5F9tpaIuXOSF41Io7hhE0GvNO-Di__vudmAU3TDyYL-PFmwfS4jVfkbrJzNgap',
        'https://discord.com/api/webhooks/810374294416654346/T3-TEdKIg7rwMZeDzNr46KPDvO7ZF8pRdJ3lfl39lJw2XEZamAG8uACIXagbNMX_B0YN',
        'https://discord.com/api/webhooks/810374337403289641/_esFkQXwlPlhxJWtlqDAdLg2Nujo-LjGPEG3mUmjiRZto69NQpkBJ0F2xtSNrCH4VAgb',
        'https://discord.com/api/webhooks/810374384736534568/mH5-OkBVpi7XqJioaQ8Ma-NiL-bOx7B5nYJpL1gZ03JaJaUaIW4bCHeCt5O_VGLJwAtj',
        'https://discord.com/api/webhooks/810374428604104724/Z1Tdxz3mb0ytWq5LHWi4rG5CeJnr9KWXy5aO_waeD0NcImQnhRXe7h7ra7UrIDRQ2jOg',
        'https://discord.com/api/webhooks/810374475773509643/QCPPN4djNzhuOmbS3DlrGBunK0SVR5Py9vMyCiPL-0T2VPgitFZS4YM6GCLfM2fkrn4-',
        'https://discord.com/api/webhooks/810374527652855819/5ypaKI_r-hYzwmdDlVmgAU6xNgU833L9tFlPnf3nw4ZDaPMSppjt77aYOiFks4KLGQk8',
        'https://discord.com/api/webhooks/810374587917402162/lHrG7CEysGUM_41DMnrxL2Q8eh1-xPjJXstYE68WWfLQbuUAV3rOfsNB9adncJzinYKi',
    ]

    
    @classmethod
    def discord_proxy_image(cls, image_url, webhook_url=None, retry=True):
        #2020-12-23
        #image_url = None
        data = None

        """
        if image_url is None or image_url == '':
            return image_url
        ret = cls.discord_proxy_get_target(image_url)
        if ret is not None:
            return ret
        """
        
        if webhook_url is None or webhook_url == '':
            #webhook_url = 'https://discordapp.com/api/webhooks/723161710030225510/_kqNtqrPtEH8pBV9oh-STl9qplcx1iZXa0VnyZNtQzk8LJs9jJt1p19abWVUwmRUgbzt' #soju6jan

            webhook_url =  cls.webhook_list[random.randint(10,len(cls.webhook_list)-1)]  # sjva 채널

        try:
            #logger.debug('webhook_url : %s', webhook_url)
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
            #logger.debug(response)
            #logger.debug(type(response))
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
                #if cls.discord_proxy_set_target(image_url, target):
                #    return target
                else:
                    return image_url
            else:
                raise Exception(str(data))
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            logger.debug(image_url) 
            logger.debug(data)
            if retry:
                time.sleep(1)
                return cls.discord_proxy_image(image_url, webhook_url=None, retry=False)
            else:
                return image_url

    
    @classmethod
    def discord_proxy_image_localfile(cls, filepath, retry=True):
        data = None
        webhook_url =  cls.webhook_list[random.randint(0,9)]  # sjva 채널

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
            #logger.debug(image_url) 
            #logger.debug(data)
            if retry:
                time.sleep(1)
                return cls.discord_proxy_image_localfile(filepath, retry=False)


    # RSS에서 자막 올린거
    @classmethod    
    def discord_cdn(cls, byteio=None, filepath=None, filename=None, webhook_url=None, content='', retry=True):
        data = None
        if webhook_url is None:
            webhook_url =  cls.webhook_list[random.randint(0,9)]  # sjva 채널

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
            #logger.debug(image_url) 
            #logger.debug(data)
            if retry:
                time.sleep(1)
                return cls.discord_proxy_image_localfile(filepath, retry=False)