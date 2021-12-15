import uuid
import hmac
import base64
import time
import requests
import re

from . import constants as CONST

def getUUID():
  return uuid.uuid4()

def getTimeString():
  return str(int(time.time()*1000))

def getAuthorization(url, version, uuid, time):
  hm = hmac.new(
    bytearray(version, encoding='ascii'),
    msg=bytearray(
      str(uuid) + '\n' + url + '\n' + time,
      encoding='ascii'
    ),
    digestmod='md5'
  ).digest()
  hm_base64 = base64.b64encode(hm)
  return f"PPG {str(uuid)}:{hm_base64.decode('ascii')}"

def getVersion(proxy):
  homepage = requests.get(CONST.url['main'], proxies=proxy).text
  jsFileRegex = re.compile('/main\..*\.js')
  jsFileURL = jsFileRegex.findall(homepage)[0]

  jsFile = requests.get(f"{CONST.url['main']}{jsFileURL}", proxies=proxy).text
  versionStringRegex = re.compile('v\d{1,2}\.\d{1,2}\.\d{1,2}_[a-z0-9]{10}')
  versionString = versionStringRegex.findall(jsFile)[0]

  return versionString
