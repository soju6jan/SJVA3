from support import d, logger
import os, sys, traceback, time, urllib.parse, requests, json

class SupportTving:
    """
    config = {
        'param' : "&free=all&lastFrequency=n&order=broadDate", #최신
        'program_param' : '&free=all&order=frequencyDesc&programCode=%s',
        'default_param' : '&screenCode=CSSD0100&networkCode=CSND0900&osCode=CSOD0900&teleCode=CSCD0900&apiKey=1e7952d0917d6aab1f0293a063697610'
    }
    """

    default_param = '&screenCode=CSSD0100&networkCode=CSND0900&osCode=CSOD0900&teleCode=CSCD0900&apiKey=1e7952d0917d6aab1f0293a063697610'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer' : '',
    } 

    def __init__(self, token=None, proxy=None, user=None, password=None, deviceid=None, uuid=None):
        self.token = token
        self.proxies = None
        if proxy != None:
            self.proxies = {"https": proxy, 'http':proxy}
        self.user = None
        self.password = None
        self.deviceid = None
        self.uuid = None
    

    def get_stream_info(self, code, quality):
        ts = int(time.time())
        try:
            if quality == 'stream70':
                tmp_param = self.default_param.replace('CSSD0100', 'CSSD1200')
                url = f"http://api.tving.com/v2/media/stream/info?info=y{tmp_param}&noCache={ts}&mediaCode={code}&streamCode={quality}&callingFrom=FLASH"
            else:
                url = f"http://api.tving.com/v2/media/stream/info?info=y{self.default_param}&noCache={ts}&mediaCode={code}&streamCode={quality}&callingFrom=FLASH"
            
            if self.token != None:
                self.headers['Cookie'] = f"_tving_token={self.token}"
            info = requests.get(url, headers=self.headers, proxies=self.proxies).json()
            logger.debug('json message : %s', info['body']['result']['message'])
            if 'drm_yn' in info['body']['stream'] and info['body']['stream']['drm_yn'] == 'Y':
                info = self.get_stream_info_by_web(code, quality)
                info['drm'] = True
            else:
                url = info['body']['stream']['broadcast']['broad_url']
                decrypted_url = self.decrypt(code, ts, url)
                if decrypted_url.find('m3u8') == -1:
                    decrypted_url = decrypted_url.replace('rtmp', 'http')
                    decrypted_url = decrypted_url.replace('?', '/playlist.m3u8?')
                #2020-06-12
                if decrypted_url.find('smil/playlist.m3u8') != -1 and decrypted_url.find('content_type=VOD') != -1 :
                    tmps = decrypted_url.split('playlist.m3u8')
                    r = requests.get(decrypted_url, headers=self.headers, proxies=self.proxies)
                    lines = r.text.split('\n')
                    logger.debug(lines)
                    i = -1
                    last = ''
                    while len(last) == 0:
                        last = lines[i].strip()
                        i -= 1
                    decrypted_url = '%s%s' % (tmps[0], last)
                info['broad_url'] = decrypted_url
                info['drm'] = False
            info['filename'] = self.__get_filename(info)
            return info
        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())


    def get_stream_info_by_web(self, code, quality):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36',
            'Accept' : 'application/json, text/plain, */*',
            'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin' : 'https://www.tving.com',
            'sec-fetch-dest' : 'empty',
            'sec-fetch-mode' : 'cors',
            'sec-fetch-site' : 'same-origin',
        } 
        if code[0] == 'E':
            content_type = 'vod'
        elif code[0] == 'M':
            content_type = 'movie'
        else:
            content_type = 'live'
        ooc = 'isTrusted=false^type=oocCreate^eventPhase=0^bubbles=false^cancelable=false^defaultPrevented=false^composed=false^timeStamp=3336.340000038035^returnValue=true^cancelBubble=false^NONE=0^CAPTURING_PHASE=1^AT_TARGET=2^BUBBLING_PHASE=3^'
        try:
            data = {
                'apiKey' : '1e7952d0917d6aab1f0293a063697610',
                'info' : 'Y',
                'networkCode' : 'CSND0900',
                'osCode' : 'CSOD0900',
                'teleCode' : 'CSCD0900',
                'mediaCode' : code,
                'screenCode' : 'CSSD0100',
                'callingFrom' : 'HTML5',
                'streamCode' : quality,
                'deviceId' : self.deviceid,
                'adReq' : 'adproxy',
                'ooc' : ooc,
                'wm': 'Y',
                'uuid' : self.uuid
            }
            cookies = {
                '_tving_token': self.token, 
                'onClickEvent2': urllib.parse.quote(ooc),
                'TP2wgas1K9Q8F7B359108383':'Y', 
            }

            headers['referer'] = f"https://www.tving.com/{content_type}/player/{code}"
            url = 'https://www.tving.com/streaming/info'
            info = requests.post(url, data=data, headers=headers, cookies=cookies, proxies=self.proxies).json()
            ret = {}
            if 'widevine' in info['stream']['broadcast']:
                ret['uri'] = info['stream']['broadcast']['widevine']['broad_url']
                ret['drm_scheme'] = 'widevine'
                ret['drm_license_uri'] = 'http://cj.drmkeyserver.com/widevine_license'
                #data['stream']['drm_license_server_list']
                ret['drm_key_request_properties'] = {
                    'origin' : 'https://www.tving.com',
                    'sec-fetch-site' : 'cross-site',
                    'sec-fetch-mode' : 'cors',
                    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
                    'Host' : 'cj.drmkeyserver.com',
                    'referer' : 'https://www.tving.com/',
                    'AcquireLicenseAssertion' : info['stream']['drm_license_assertion'],
                }
                info['play_info'] = ret
            else:
                info['play_info'] = {'hls':info['stream']['broadcast']['broad_url']}
            return info
        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())


    def __decrypt(self, code, key, value):
        try:
            from Crypto.Cipher import DES3
            import base64
            data = base64.decodebytes(value.encode())
            cryptoCode = 'cjhv*tving**good/%s/%s' % (code[-3:], key)
            key = cryptoCode[:24]
            des3 = DES3.new(key, DES3.MODE_ECB)
            ret = des3.decrypt(data)
            pad_len = ret[-1]
            ret = ret[:-pad_len]
            return ret.decode()
        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())
    

    def __get_filename(self, episode_data):
        try:
            title = episode_data["content"]["program_name"]
            title = title.replace("<", "").replace(">", "").replace("\\", "").replace("/", "").replace(":", "").replace("*", "").replace("\"", "").replace("|", "").replace("?", "").replace("  ", " ").strip()
            episodeno = episode_data["content"]["frequency"]
            airdate = str(episode_data["content"]["info"]["episode"]["broadcast_date"])[2:]

            currentQuality = None
            if episode_data["stream"]["quality"] is None:
                currentQuality = "stream40"
            else:
                qualityCount = len(episode_data["stream"]["quality"])
                for i in range(qualityCount):
                    if episode_data["stream"]["quality"][i]["selected"] == "Y":
                        currentQuality = episode_data["stream"]["quality"][i]["code"]
                        break
            if currentQuality is None:
                return
            qualityRes = self.__get_quality_to_res(currentQuality)
            episodeno_str = str(episodeno)
            if episodeno < 10:
                episodeno_str = '0' + episodeno_str
            
            ret = '%s.E%s.%s.%s-ST.mp4' % (title, episodeno_str, airdate, qualityRes)
            if episode_data['drm']:
                ret = ret.replace('.mp4', '.mkv')
            return ret
        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())


    def __get_quality_to_res(self, quality):
        if quality == 'stream50':
            return '1080p'
        elif quality == 'stream40':
            return '720p'
        elif quality == 'stream30':
            return '480p'
        elif quality == 'stream70':
            return '2160p'
        elif quality == 'stream25':
            return '270p'
        return '1080p'
        
        