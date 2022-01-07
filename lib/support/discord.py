import os, io, traceback, time, random, requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from . import logger

webhook_list = [
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



class SupportDiscord(object):

    @classmethod
    def send_discord_message(cls, text, image_url=None, webhook_url=None):
        try:
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
    def discord_proxy_image(cls, image_url, webhook_url=None, retry=True):
        #2020-12-23
        #image_url = None
        if image_url == '' or image_url is None:
            return
        data = None
        
        if webhook_url is None or webhook_url == '':
            webhook_url =  webhook_list[random.randint(0,len(webhook_list)-1)]

        try:
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
        webhook_url =  webhook_list[random.randint(0,len(webhook_list)-1)]

        try:
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


    @classmethod
    def discord_proxy_image_bytes(cls, bytes, retry=True):
        data = None
        webhook_url =  webhook_list[random.randint(0,len(webhook_list)-1)]
        try:
            webhook = DiscordWebhook(url=webhook_url, content='')
            webhook.add_file(file=bytes, filename='image.jpg')
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
                return cls.discord_proxy_image_bytes(bytes, retry=False)




    # RSS에서 자막 올린거
    @classmethod    
    def discord_cdn(cls, byteio=None, filepath=None, filename=None, webhook_url=None, content='', retry=True):
        data = None
        if webhook_url is None:
            webhook_url =  webhook_list[random.randint(0,9)]  # sjva 채널

        try:
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
                
