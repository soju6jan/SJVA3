# -*- coding: utf-8 -*-
#########################################################
# python
import base64

# third-party

from Crypto.Cipher import AES
from Crypto import Random

# sjva 공용
from framework.logger import get_logger
from framework import app, logger
# 패키지

# 로그

#########################################################

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
if app.config['config']['is_py2']:
    unpad = lambda s : s[0:-ord(s[-1])]
else:
    unpad = lambda s : s[0:-s[-1]]


key = '140b41b22a29beb4061bda66b6747e14'
if app.config['config']['is_py3']:
    key = key.encode()

class ToolAESCipher(object):
    @staticmethod
    def encrypt(raw, mykey=None):
        try:
            Random.atfork()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 

        if app.config['config']['is_py2']:
            raw = pad(raw)
            iv = Random.new().read( AES.block_size )
            cipher = AES.new(key if mykey is None else mykey, AES.MODE_CBC, iv )
            ret = base64.b64encode( iv + cipher.encrypt( raw ) ) 
            if app.config['config']['is_py3']:
                ret = ret.decode()
            return ret
        else:
            raw = pad(raw)
            #logger.debug('>>raw2:%s', type(raw))
            if type(raw) == type(''):
                raw = raw.encode()
            if mykey is not None and type(mykey) == type(''):
                mykey = mykey.encode()
            #logger.debug('>>raw2:%s', type(raw))
            #logger.debug('>>raw2:%s', raw)
            iv = Random.new().read( AES.block_size )
            #logger.debug('>>iv:%s', iv)
            cipher = AES.new(key if mykey is None else mykey, AES.MODE_CBC, iv )
            try:
                tmp = cipher.encrypt( raw )
            except:
                # 아마도 pycrypto와 pycryptodome이 다른 차이
                tmp = cipher.encrypt( raw.encode() )
            #logger.debug('>>cipher.encrypt( raw ):%s', tmp)
            ret = base64.b64encode( iv + tmp ) 
            #logger.debug('>>ret:%s', ret)
            if app.config['config']['is_py3']:
                ret = ret.decode()
            #logger.debug('>>ret2:%s', ret)                
            return ret

    @staticmethod
    def decrypt(enc, mykey=None):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(key if mykey is None else mykey, AES.MODE_CBC, iv )
        return unpad(cipher.decrypt( enc[16:] ))


if __name__== "__main__":
    key = "140b41b22a29beb4061bda66b6747e14"
    text = u'안녕하세요..'
    key=key[:32]

    a = AESCipher.encrypt(text)
    
    b = AESCipher.decrypt(a)
    
