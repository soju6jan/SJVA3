import os, io, traceback, time, random, requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from . import logger

webhook_list = [
    'https://discord.com/api/webhooks/932753790757654618/fAV5ROkvMzLb3oe4gjBXMmm2gC8wk38qvPKRItK-W6JQgwGOgHFSw2S2IUmNUq_cCVXY', # 1
    'https://discord.com/api/webhooks/932754078839234731/R2iFzQ7P8IKV-MGWp820ToWX07s5q8X-st-QsUJs7j3JInUj6ZlI4uDYKeR_cwIi98mf', # 2
    'https://discord.com/api/webhooks/932754171835351131/50RLrYa_B69ybk4BWoLruNqU7YlZ3pl3gpPr9bwuankWyTIGtRGbgf0CJ9ExJWJmvXwo', # 3
    'https://discord.com/api/webhooks/794661043863027752/A9O-vZSHIgfQ3KX7wO5_e2xisqpLw5TJxg2Qs1stBHxyd5PK-Zx0IJbAQXmyDN1ixZ-n', # 4
    'https://discord.com/api/webhooks/810373348776476683/h_uJLBBlHzD0w_CG0nUajFO-XEh3fvy-vQofQt1_8TMD7zHiR7a28t3jF-xBCP6EVlow', # 5
    'https://discord.com/api/webhooks/810373405508501534/wovhf-1pqcxW5h9xy7iwkYaf8KMDjHU49cMWuLKtBWjAnj-tzS1_j8RJ7tsMyViDbZCE', # 6
    'https://discord.com/api/webhooks/796558388326039552/k2VV356S1gKQa9ht-JuAs5Dqw5eVkxgZsLUzFoxmFG5lW6jqKl7zCBbbKVhs3pcLOetm', # 7
    'https://discord.com/api/webhooks/810373566452858920/Qf2V8BoLOy2kQzlZGHy5HZ1nTj7lK72ol_UFrR3_eHKEOK5fyR_fQ8Yw8YzVh9EQG54o', # 8
    'https://discord.com/api/webhooks/810373654411739157/SGgdO49OCkTNIlc_BSMSy7IXQwwXVonG3DsVfvBVE6luTCwvgCqEBpEk30WBeMMieCyI', # 9
    'https://discord.com/api/webhooks/810373722341900288/FwcRJ4YxYjpyHpnRwF5f2an0ltEm8JPqcWeZqQi3Qz4QnhEY-kR2sjF9fo_n6stMGnf_', # 10
    'https://discord.com/api/webhooks/931779811691626536/vvwCm1YQvE5tW4QJ4SNKRmXhQQrmOQxbjsgRjbTMMXOSiclB66qipiZaax5giAqqu2IB', # 11
    'https://discord.com/api/webhooks/931779905631420416/VKlDwfxWQPJfIaj94-ww_hM1MNEayRKoMq0adMffCC4WQS60yoAub_nqPbpnfFRR3VU5', # 12
    'https://discord.com/api/webhooks/931779947914231840/22amQuHSOI7wPijSt3U01mXwd5hTo_WHfVkeaowDQMawCo5tXVfeEMd6wAWf1n7CseiG', # 13
    'https://discord.com/api/webhooks/810374294416654346/T3-TEdKIg7rwMZeDzNr46KPDvO7ZF8pRdJ3lfl39lJw2XEZamAG8uACIXagbNMX_B0YN', # 14
    'https://discord.com/api/webhooks/810374337403289641/_esFkQXwlPlhxJWtlqDAdLg2Nujo-LjGPEG3mUmjiRZto69NQpkBJ0F2xtSNrCH4VAgb', # 15
    'https://discord.com/api/webhooks/810374384736534568/mH5-OkBVpi7XqJioaQ8Ma-NiL-bOx7B5nYJpL1gZ03JaJaUaIW4bCHeCt5O_VGLJwAtj', # 16
    'https://discord.com/api/webhooks/810374428604104724/Z1Tdxz3mb0ytWq5LHWi4rG5CeJnr9KWXy5aO_waeD0NcImQnhRXe7h7ra7UrIDRQ2jOg', # 17
    'https://discord.com/api/webhooks/810374475773509643/QCPPN4djNzhuOmbS3DlrGBunK0SVR5Py9vMyCiPL-0T2VPgitFZS4YM6GCLfM2fkrn4-', # 18
    'https://discord.com/api/webhooks/810374527652855819/5ypaKI_r-hYzwmdDlVmgAU6xNgU833L9tFlPnf3nw4ZDaPMSppjt77aYOiFks4KLGQk8', # 19
    'https://discord.com/api/webhooks/810374587917402162/lHrG7CEysGUM_41DMnrxL2Q8eh1-xPjJXstYE68WWfLQbuUAV3rOfsNB9adncJzinYKi', # 20
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
            if retry:
                time.sleep(1)
                return cls.discord_proxy_image_localfile(filepath, retry=False)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
            if retry:
                time.sleep(1)
                return cls.discord_proxy_image_localfile(filepath, retry=False)


    @classmethod
    def discord_proxy_image_bytes(cls, bytes, retry=True):
        data = None
        idx = random.randint(0,len(webhook_list)-1)
        webhook_url =  webhook_list[idx]
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
            logger.error(f"discord webhook error : {webhook_url}")
            logger.error(f"discord webhook error : {idx}")
            if retry:
                time.sleep(1)
                return cls.discord_proxy_image_bytes(bytes, retry=False)
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
            if retry:
                time.sleep(1)
                return cls.discord_proxy_image_localfile(filepath, retry=False)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            if retry:
                time.sleep(1)
                return cls.discord_proxy_image_localfile(filepath, retry=False)
                
