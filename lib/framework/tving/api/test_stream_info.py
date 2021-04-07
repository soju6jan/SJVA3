# -*- coding: utf-8 -*-
import os
import traceback
import sys
import requests
import time
import json
import base64



session = requests.session()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36',
    'Accept' : 'application/json, text/plain, */*',
    'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'origin' : 'https://www.tving.com',
    'referer' : 'https://www.tving.com/live/player/C07381',
    'sec-fetch-dest' : 'empty',
    'sec-fetch-mode' : 'cors',
    'sec-fetch-site' : 'same-origin',
    #'cookie': '_xm_webid_1_=248959937; _ga=GA1.2.489898194.1602221313; _aproxy_aid=CrbKnFo0hmUYnvMU; _trs_id=eY%3F437%3F7147144%3E4%3E; cs=screenCode%3DCSSD0100%3BnetworkCode%3DCSND0900%3BosCode%3DCSOD0900%3BteleCode%3DCSCD0900; TVING_AUTO_EXPIRE_TIME=FHi0wXJTfQXQ30DOaVSmxA%3D%3D; _tving_token=GZ2lHPOGpKyNhJY8FZgFmw%3D%3D; POC_USERINFO=aeSjz7IMYkx%2Fj0Ss7YLkzcPMJAQnttf5uFn1sdCanThpnYhJFsxWcAn6UDS2BeBvOSgrDXYFD5vQgt%2BteF9K5vesy60ntBs0BgcPN9kt5Vjwi%2BYnUFMRao0ggX%2BGaH3oK69ZTUxC7Bq9yq3hrffbKSSfdfHlcn9fZ4E%2BgYdi8VkycY7rFSWfWCRg4y7S6WkmePnc0oBWVz7n7E5Owfw3sSlIFEqlxD%2BhJtagzPbWR6PGUrRgXvUTFjKJy4kLzOIbT2pdtprGKHXCWTz87WjpjE7SkuJnblay6iD7L%2Fq%2FL1zevsW%2BLzihmDmQAY%2BraNExwxhpVZd2jYQxknpUO%2FjL%2FEwIjRR8uLxoOuDMp6Kbir3QZyAhjIjCGWyqRJhelRuAxn1qBPWDMBc6jXJP3%2BDKgGQ8iIHvVYmSAaZ6bjl%2BbwRFeCNRTREXbjBw03E%2F2GG2%2BZXyoZR3iXLnJQ00c3MFVw240OpLzGUu0NdtQVumdLZ868dEcqWIaPErjPlCspllZZvJrSGbhdXaGfp%2Bm6gLzFp8H0LVAYSl0a6IwaMA5qEtRPJRCCl1biSFh%2BOzuCSBCnZBmASb2aC5jw0KspfWy%2BLG4XfZ4ej26ae9yrL3NkqIU9y1eTI4NKeC2yh2bivY7iK%2BXwR9C6aW%2FOFZ5mFk3mOtQX%2F70HCaf8AyX97WrxY%3D; GA360_USERTYPE_JSON=%7B%22dm019_paycnt%22%3A%22C34%22%2C%22dm016_TL_FYMD%22%3A%22%22%2C%22dm018_LP_FYMD%22%3A%2220180131%22%2C%22dm022_MP_CYMD%22%3A%22%22%2C%22dm017_TL_CYMD%22%3A%22%22%2C%22dm020_LP_CYMD%22%3A%22%22%2C%22dm009_usertype%22%3A%22C%22%2C%22dm021_MP_FYMD%22%3A%22%22%2C%22dm013_resIsPaid%22%3A%22P%22%7D; ADULT_CONFIRM_YN=Y; LEGAL_CONFIRM_YN=N; PERAGREE_CONFIRM_YN=N; MARKETING_CONFIRM_YN=N; _login_onetime_www_hellovision=Y; TSID=6fbed3445c466a2d99d3fb302f3cb671; adTag=00016054; _gid=GA1.2.210040630.1604992740; _gat_UA-118660069-1=1; 736f6a75366a616e=true; JSESSIONID=725690FDC1D2DDF9B5695D88B84E62A7; wcs_bt=s_1b6ae80a204f:1604992760; onClickEvent2=isTrusted%253Dfalse%255Etype%253DoocCreate%255EeventPhase%253D0%255Ebubbles%253Dfalse%255Ecancelable%253Dfalse%255EdefaultPrevented%253Dfalse%255Ecomposed%253Dfalse%255EtimeStamp%253D4459.404999972321%255EreturnValue%253Dtrue%255EcancelBubble%253Dfalse%255ENONE%253D0%255ECAPTURING_PHASE%253D1%255EAT_TARGET%253D2%255EBUBBLING_PHASE%253D3%255E'
} 


config = {
    'token': None,
    'param' : "&free=all&lastFrequency=y&order=broadDate", #최신
    'program_param' : '&free=all&order=frequencyDesc&programCode=%s',
    'default_param' : '&screenCode=CSSD0100&networkCode=CSND0900&osCode=CSOD0900&teleCode=CSCD0900&apiKey=1e7952d0917d6aab1f0293a063697610'
}


import requests

def get_stream_info():
    print('aaa') 

    url = 'https://www.tving.com/streaming/info'
    ooc = 'isTrusted=false^type=oocCreate^eventPhase=0^bubbles=false^cancelable=false^defaultPrevented=false^composed=false^timeStamp=4459.404999972321^returnValue=true^cancelBubble=false^NONE=0^CAPTURING_PHASE=1^AT_TARGET=2^BUBBLING_PHASE=3^'
    ooc = 'composed=false^CAPTURING_PHASE=1^cancelable=false^returnValue=true^cancelBubble=false^bubbles=false^defaultPrevented=false^NONE=0^AT_TARGET=2^BUBBLING_PHASE=3^timeStamp=2158.7350000045262^isTrusted=false^type=oocCreate^eventPhase=0'
    data = {
        'apiKey' : '1e7952d0917d6aab1f0293a063697610',
        'info' : 'Y',
        'networkCode' : 'CSND0900',
        'osCode' : 'CSOD0400',
        'teleCode' : 'CSCD0900',
        'mediaCode' : 'C07381',
        'screenCode' : 'CSSD0100',
        'callingFrom' : 'HTML5',
        'streamCode' : 'stream40',
        'deviceId' : '18747739',
        'adReq' : 'adproxy',
        'ooc' : ooc
    }

    url2 = "http://api.tving.com/v1/user/device/list?model=PC&screenCode=CSSD0100&networkCode=CSND0900&osCode=CSOD0900&teleCode=CSCD0900&apiKey=1e7952d0917d6aab1f0293a063697610"
    
    #params= {'networkCode': 'CSND0900', 'apiKey': '1e7952d0917d6aab1f0293a063697610', 'guest': 'all', 'screenCode': 'CSSD0100', 'free': 'all', 'scope': 'all', 'osCode': 'CSOD0900', 'order': 'rating', 'teleCode': 'CSCD0900'}
    #print(requests.get(url2, headers=headers).text)
    res2 = requests.get(url2,  headers =  {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'} , cookies = {'_tving_token': 'GZ2lHPOGpKyNhJY8FZgFmw%3D%3D', 'POC_USERINFO': 'aeSjz7IMYkx%2Fj0Ss7YLkzcPMJAQnttf5uFn1sdCanThpnYhJFsxWcAn6UDS2BeBvOSgrDXYFD5vQgt%2BteF9K5vesy60ntBs0BgcPN9kt5Vjwi%2BYnUFMRao0ggX%2BGaH3oK69ZTUxC7Bq9yq3hrffbKSSfdfHlcn9fZ4E%2BgYdi8VkycY7rFSWfWCRg4y7S6WkmePnc0oBWVz7n7E5Owfw3sSlIFEqlxD%2BhJtagzPbWR6PGUrRgXvUTFjKJy4kLzOIbT2pdtprGKHXCWTz87WjpjE7SkuJnblay6iD7L%2Fq%2FL1zevsW%2BLzihmDmQAY%2BraNExwxhpVZd2jYQxknpUO%2FjL%2FEwIjRR8uLxoOuDMp6Kbir3QZyAhjIjCGWyqRJhelRuAxn1qBPWDMBc6jXJP3%2BDKgGQ8iIHvVYmSAaZ6bjl%2BbwRFeCNRTREXbjBw03E%2F2GG2%2BZXyoZR3iXLnJQ00c3MFVw240OpLzGUu0NdtQVumdLZ868dEcqWIaPErjPlCspllZZvJrSGbhdXaGfp%2Bm6gLzFp8H0LVAYSl0a6IwaMA5qEtRPJRCCl1biSFh%2BOzuCSBCnZBmASb2aC5jw0KspfWy%2BLG4XfZ4ej26ae9yrL3NkqIU9y1eTI4NKeC2yh2bivY7iK%2BXwR9C6aW%2FOFZ5mFk3mOtQX%2F70HCaf8AyX97WrxY%3D'}  )
    print(res2.text)

    import time
    print(time.time())

    return
    
    #res = requests.post(url, headers=headers, json=data)

    #res = requests.post(url, data={'info': 'N', 'networkCode': 'CSND0900', 'apiKey': '1e7952d0917d6aab1f0293a063697610', 'adReq': 'none', 'ooc': 'composed=false^CAPTURING_PHASE=1^cancelable=false^returnValue=true^cancelBubble=false^bubbles=false^defaultPrevented=false^NONE=0^AT_TARGET=2^BUBBLING_PHASE=3^timeStamp=2158.7350000045262^isTrusted=false^type=oocCreate^eventPhase=0^', 'streamCode': 'stream50', 'screenCode': 'CSSD0100', 'mediaCode': 'C07381', 'callingFrom': 'HTML5', 'deviceId': '18747739', 'osCode': 'CSOD0400', 'teleCode': 'CSCD0900'}, headers={'origin': 'https://www.tving.com', 'Referer': 'https://www.tving.com/vod/player/C07381', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'}, cookies = {'_tving_token': 'GZ2lHPOGpKyNhJY8FZgFmw%3D%3D', 'POC_USERINFO': 'aeSjz7IMYkx%2Fj0Ss7YLkzcPMJAQnttf5uFn1sdCanThpnYhJFsxWcAn6UDS2BeBvOSgrDXYFD5vQgt%2BteF9K5vesy60ntBs0BgcPN9kt5Vjwi%2BYnUFMRao0ggX%2BGaH3oK69ZTUxC7Bq9yq3hrffbKSSfdfHlcn9fZ4E%2BgYdi8VkycY7rFSWfWCRg4y7S6WkmePnc0oBWVz7n7E5Owfw3sSlIFEqlxD%2BhJtagzPbWR6PGUrRgXvUTFjKJy4kLzOIbT2pdtprGKHXCWTz87WjpjE7SkuJnblay6iD7L%2Fq%2FL1zevsW%2BLzihmDmQAY%2BraNExwxhpVZd2jYQxknpUO%2FjL%2FEwIjRR8uLxoOuDMp6Kbir3QZyAhjIjCGWyqRJhelRuAxn1qBPWDMBc6jXJP3%2BDKgGQ8iIHvVYmSAaZ6bjl%2BbwRFeCNRTREXbjBw03E%2F2GG2%2BZXyoZR3iXLnJQ00c3MFVw240OpLzGUu0NdtQVumdLZ868dEcqWIaPErjPlCspllZZvJrSGbhdXaGfp%2Bm6gLzFp8H0LVAYSl0a6IwaMA5qEtRPJRCCl1biSFh%2BOzuCSBCnZBmASb2aC5jw0KspfWy%2BLG4XfZ4ej26ae9yrL3NkqIU9y1eTI4NKeC2yh2bivY7iK%2BXwR9C6aW%2FOFZ5mFk3mOtQX%2F70HCaf8AyX97WrxY%3D', 'onClickEvent2': 'composed%3Dfalse%5ECAPTURING_PHASE%3D1%5Ecancelable%3Dfalse%5EreturnValue%3Dtrue%5EcancelBubble%3Dfalse%5Ebubbles%3Dfalse%5EdefaultPrevented%3Dfalse%5ENONE%3D0%5EAT_TARGET%3D2%5EBUBBLING_PHASE%3D3%5EtimeStamp%3D2158.7350000045262%5EisTrusted%3Dfalse%5Etype%3DoocCreate%5EeventPhase%3D0%5E'} , )
    #composed=false^CAPTURING_PHASE=1^cancelable=false^returnValue=true^cancelBubble=false^bubbles=false^defaultPrevented=false^NONE=0^AT_TARGET=2^BUBBLING_PHASE=3^timeStamp=2158.7350000045262^isTrusted=false^type=oocCreate^eventPhase=0
    #composed=false^CAPTURING_PHASE=1^cancelable=false^returnValue=true^cancelBubble=false^bubbles=false^defaultPrevented=false^NONE=0^AT_TARGET=2^BUBBLING_PHASE=3^timeStamp=2158.7350000045262^isTrusted=false^type=oocCreate^eventPhase=0



    #res = requests.post(url, data={'info': 'N', 'networkCode': 'CSND0900', 'apiKey': '1e7952d0917d6aab1f0293a063697610', 'adReq': 'none', 'ooc': 'composed=false^CAPTURING_PHASE=1^cancelable=false^returnValue=true^cancelBubble=false^bubbles=false^defaultPrevented=false^NONE=0^AT_TARGET=2^BUBBLING_PHASE=3^timeStamp=2158.7350000045262^isTrusted=false^type=oocCreate^eventPhase=0^', 'streamCode': 'stream50', 'screenCode': 'CSSD0100', 'mediaCode': 'C07381', 'callingFrom': 'HTML5', 'deviceId': '18747739', 'osCode': 'CSOD0400', 'teleCode': 'CSCD0900'}, headers={'origin': 'https://www.tving.com', 'Referer': 'https://www.tving.com/vod/player/C07381', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'}, cookies = {'_tving_token': 'GZ2lHPOGpKyNhJY8FZgFmw%3D%3D', 'POC_USERINFO': 'aeSjz7IMYkx%2Fj0Ss7YLkzcPMJAQnttf5uFn1sdCanThpnYhJFsxWcAn6UDS2BeBvOSgrDXYFD5vQgt%2BteF9K5vesy60ntBs0BgcPN9kt5Vjwi%2BYnUFMRao0ggX%2BGaH3oK69ZTUxC7Bq9yq3hrffbKSSfdfHlcn9fZ4E%2BgYdi8VkycY7rFSWfWCRg4y7S6WkmePnc0oBWVz7n7E5Owfw3sSlIFEqlxD%2BhJtagzPbWR6PGUrRgXvUTFjKJy4kLzOIbT2pdtprGKHXCWTz87WjpjE7SkuJnblay6iD7L%2Fq%2FL1zevsW%2BLzihmDmQAY%2BraNExwxhpVZd2jYQxknpUO%2FjL%2FEwIjRR8uLxoOuDMp6Kbir3QZyAhjIjCGWyqRJhelRuAxn1qBPWDMBc6jXJP3%2BDKgGQ8iIHvVYmSAaZ6bjl%2BbwRFeCNRTREXbjBw03E%2F2GG2%2BZXyoZR3iXLnJQ00c3MFVw240OpLzGUu0NdtQVumdLZ868dEcqWIaPErjPlCspllZZvJrSGbhdXaGfp%2Bm6gLzFp8H0LVAYSl0a6IwaMA5qEtRPJRCCl1biSFh%2BOzuCSBCnZBmASb2aC5jw0KspfWy%2BLG4XfZ4ej26ae9yrL3NkqIU9y1eTI4NKeC2yh2bivY7iK%2BXwR9C6aW%2FOFZ5mFk3mOtQX%2F70HCaf8AyX97WrxY%3D', 'onClickEvent2': 'composed%3Dfalse%5ECAPTURING_PHASE%3D1%5Ecancelable%3Dfalse%5EreturnValue%3Dtrue%5EcancelBubble%3Dfalse%5Ebubbles%3Dfalse%5EdefaultPrevented%3Dfalse%5ENONE%3D0%5EAT_TARGET%3D2%5EBUBBLING_PHASE%3D3%5EtimeStamp%3D2158.7350000045262%5EisTrusted%3Dfalse%5Etype%3DoocCreate%5EeventPhase%3D0%5E'} , )


    import urllib
    print (urllib.quote(ooc))

    res = requests.post(url, data=data, headers=headers, cookies = {'_tving_token': 'GZ2lHPOGpKyNhJY8FZgFmw%3D%3D', 'onClickEvent2': urllib.quote(ooc)})

    print(res.status_code)
    ret = res.text

    print(ret)



"""

 'isTrusted' : 'false'
 , 'NONE' : '0'
 , 'CAPTURING_PHASE' : '1'
 , 'AT_TARGET' : '2'
 , 'BUBBLING_PHASE' : '3'
 , 'type' : 'oocCreate'
 , 'eventPhase' : '0'
 , 'bubbles' : 'false'
 , 'cancelable' : 'false'
 , 'defaultPrevented' : 'false'
 , 'composed' : 'false'
 , 'timeStamp' : '2158.7350000045262'
 , 'returnValue' : 'true'
 , 'cancelBubble' : 'false'
 }

"""

"""
cs=screenCode%3DCSSD0100%3BnetworkCode%3DCSND0900%3BosCode%3DCSOD0900%3BteleCode%3DCSCD0900; Domain=.tving.com; Path=/, TVING_AUTO_EXPIRE_TIME=FHi0wXJTfQXQ30DOaVSmxA%3D%3D; Domain=.tving.com; Path=/, _tving_token=GZ2lHPOGpKyNhJY8FZgFmw%3D%3D; Domain=.tving.com; Path=/, POC_USERINFO=aeSjz7IMYkx%2Fj0Ss7YLkzcPMJAQnttf5uFn1sdCanThpnYhJFsxWcAn6UDS2BeBvOSgrDXYFD5vQgt%2BteF9K5vesy60ntBs0BgcPN9kt5Vjwi%2BYnUFMRao0ggX%2BGaH3oK69ZTUxC7Bq9yq3hrffbKSSfdfHlcn9fZ4E%2BgYdi8VkycY7rFSWfWCRg4y7S6WkmePnc0oBWVz7n7E5Owfw3sSlIFEqlxD%2BhJtagzPbWR6PGUrRgXvUTFjKJy4kLzOIbT2pdtprGKHXCWTz87WjpjE7SkuJnblay6iD7L%2Fq%2FL1zevsW%2BLzihmDmQAY%2BraNExwxhpVZd2jYQxknpUO%2FjL%2FEwIjRR8uLxoOuDMp6Kbir3QZyAhjIjCGWyqRJhelRuAxn1qBPWDMBc6jXJP3%2BDKgGQ8iIHvVYmSAaZ6bjl%2BbwRFeCNRTREXbjBw03E%2F2GG2%2BZXyoZR3iXLnJQ00c3MFVw240OpLzGUu0NdtQVumdLZ868dEcqWIaPErjPlCspllZZvJrSGbhdXaGfp%2Bm6gLzFp8H0LVAYSl0a6IwaMA5qEtRPJRCCl1biSFh%2BOzuCSBCnZBmASb2aC5jw0KspfWy%2BLG4XfZ4ej26ae9yrL3NkqIU9y1eTI4NKeC2yh2bivY7iK%2BXwR9C6aW%2FOFZ5mFk3mOtQX%2F70HCaf8AyX97WrxY%3D; Domain=.tving.com; Path=/, GA360_USERTYPE_JSON=%7B%22dm019_paycnt%22%3A%22C34%22%2C%22dm016_TL_FYMD%22%3A%22%22%2C%22dm018_LP_FYMD%22%3A%2220180131%22%2C%22dm022_MP_CYMD%22%3A%22%22%2C%22dm017_TL_CYMD%22%3A%22%22%2C%22dm020_LP_CYMD%22%3A%22%22%2C%22dm009_usertype%22%3A%22C%22%2C%22dm021_MP_FYMD%22%3A%22%22%2C%22dm013_resIsPaid%22%3A%22P%22%7D; Domain=.tving.com; Path=/, ADULT_CONFIRM_YN=Y; Domain=.tving.com; Path=/, LEGAL_CONFIRM_YN=N; Domain=.tving.com; Path=/, PERAGREE_CONFIRM_YN=N; Domain=.tving.com; Path=/, MARKETING_CONFIRM_YN=N; Domain=.tving.com; Path=/, _login_onetime_www_hellovision=Y; Domain=.tving.com; Path=/, LOGIN_FAIL_LIMIT=""; Domain=.tving.com; Expires=Thu, 01-Jan-1970 00:00:10 GMT; Path=/, LOGIN_EXCESS_LIMIT=""; Domain=.tving.com; Expires=Thu, 01-Jan-1970 00:00:10 GMT; Path=/, TVING_CAPTCHA_KEY=""; Domain=.tving.com; Expires=Thu, 01-Jan-1970 00:00:10 GMT; Path=/


{'info': 'N', 'networkCode': 'CSND0900', 'apiKey': '1e7952d0917d6aab1f0293a063697610', 'adReq': 'none', 'ooc': 'composed=false^CAPTURING_PHASE=1^cancelable=false^returnValue=true^cancelBubble=false^bubbles=false^defaultPrevented=false^NONE=0^AT_TARGET=2^BUBBLING_PHASE=3^timeStamp=2158.7350000045262^isTrusted=false^type=oocCreate^eventPhase=0^', 'streamCode': 'stream50', 'screenCode': 'CSSD0100', 'mediaCode': 'C07381', 'callingFrom': 'HTML5', 'deviceId': '18747739', 'osCode': 'CSOD0400', 'teleCode': 'CSCD0900'}

{'origin': 'https://www.tving.com', 'Referer': 'https://www.tving.com/vod/player/C07381', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'}

{'_tving_token': 'GZ2lHPOGpKyNhJY8FZgFmw%3D%3D', 'POC_USERINFO': 'aeSjz7IMYkx%2Fj0Ss7YLkzcPMJAQnttf5uFn1sdCanThpnYhJFsxWcAn6UDS2BeBvOSgrDXYFD5vQgt%2BteF9K5vesy60ntBs0BgcPN9kt5Vjwi%2BYnUFMRao0ggX%2BGaH3oK69ZTUxC7Bq9yq3hrffbKSSfdfHlcn9fZ4E%2BgYdi8VkycY7rFSWfWCRg4y7S6WkmePnc0oBWVz7n7E5Owfw3sSlIFEqlxD%2BhJtagzPbWR6PGUrRgXvUTFjKJy4kLzOIbT2pdtprGKHXCWTz87WjpjE7SkuJnblay6iD7L%2Fq%2FL1zevsW%2BLzihmDmQAY%2BraNExwxhpVZd2jYQxknpUO%2FjL%2FEwIjRR8uLxoOuDMp6Kbir3QZyAhjIjCGWyqRJhelRuAxn1qBPWDMBc6jXJP3%2BDKgGQ8iIHvVYmSAaZ6bjl%2BbwRFeCNRTREXbjBw03E%2F2GG2%2BZXyoZR3iXLnJQ00c3MFVw240OpLzGUu0NdtQVumdLZ868dEcqWIaPErjPlCspllZZvJrSGbhdXaGfp%2Bm6gLzFp8H0LVAYSl0a6IwaMA5qEtRPJRCCl1biSFh%2BOzuCSBCnZBmASb2aC5jw0KspfWy%2BLG4XfZ4ej26ae9yrL3NkqIU9y1eTI4NKeC2yh2bivY7iK%2BXwR9C6aW%2FOFZ5mFk3mOtQX%2F70HCaf8AyX97WrxY%3D', 'onClickEvent2': 'composed%3Dfalse%5ECAPTURING_PHASE%3D1%5Ecancelable%3Dfalse%5EreturnValue%3Dtrue%5EcancelBubble%3Dfalse%5Ebubbles%3Dfalse%5EdefaultPrevented%3Dfalse%5ENONE%3D0%5EAT_TARGET%3D2%5EBUBBLING_PHASE%3D3%5EtimeStamp%3D2158.7350000045262%5EisTrusted%3Dfalse%5Etype%3DoocCreate%5EeventPhase%3D0%5E'}
"""

get_stream_info()




