from .file import *
from .env import *
from .aes_cipher import AESCipher
from .sjva_support_handle import SJVASupportControl
from .vtt_to_srt import convert_vtt_to_srt

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}

def get_filename_from_cd(cd):
    import re
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0].replace('"', '')

def get_json_with_auth_session():
    pass