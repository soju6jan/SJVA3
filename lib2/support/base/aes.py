import base64, traceback
from Crypto.Cipher import AES
from Crypto import Random
from . import logger
BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[0:-s[-1]]
key = b'140b41b22a29beb4061bda66b6747e14'

class SupportAES(object):
    @classmethod
    def encrypt(cls, raw, mykey=None):
        try:
            Random.atfork()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 

        raw = pad(raw)
        if type(raw) == type(''):
            raw = raw.encode()
        if mykey is not None and type(mykey) == type(''):
            mykey = mykey.encode()
        iv = Random.new().read( AES.block_size )
        cipher = AES.new(key if mykey is None else mykey, AES.MODE_CBC, iv )
        try:
            tmp = cipher.encrypt( raw )
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
            tmp = cipher.encrypt( raw.encode() )
        ret = base64.b64encode( iv + tmp ) 
        ret = ret.decode()
        return ret

    @classmethod
    def decrypt(cls, enc, mykey=None):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(key if mykey is None else mykey, AES.MODE_CBC, iv )
        return unpad(cipher.decrypt( enc[16:] )).decode()
