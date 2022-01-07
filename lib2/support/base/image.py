import os, sys, traceback, requests
from io import BytesIO
from . import logger

class SupportImage(object):

    @classmethod
    def horizontal_to_vertical(cls, url):
        try:
            from PIL import Image
            im = Image.open(requests.get(url, stream=True).raw)
            width,height = im.size
            new_height = int(width * 1.5)
            new_im = Image.new('RGB', (width, new_height))
            new_im.paste(im, (0, int((new_height-height)/2)))

            img_byte_arr = BytesIO()
            new_im.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            from . import SupportDiscord
            return SupportDiscord.discord_proxy_image_bytes(img_byte_arr)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

