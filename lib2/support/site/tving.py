import os, sys, traceback, time, urllib.parse, requests, json, base64, re, platform
if __name__ == '__main__':
    if platform.system() == 'Windows':
        sys.path += ["C:\SJVA3\lib2", "C:\SJVA3\data\custom", "C:\SJVA3_DEV"]
    else:
        sys.path += ["/root/SJVA3/lib2", "/root/SJVA3/data/custom"]

from support import d, logger


apikey = '1e7952d0917d6aab1f0293a063697610'
#apikey = '95a64ebcd8e154aeb96928bf34848826'

class SupportTving:
    default_param = f'&screenCode=CSSD0100&networkCode=CSND0900&osCode=CSOD0900&teleCode=CSCD0900&apiKey={apikey}'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer' : '',
    } 

    # 같은 코드가 여러군에 있는게 불편하여 그냥 sjva안에서는 ins를 가져와서 사용하는 것으로 한다.
    # sjva외에서는 생성해서 사용.
    # ins를 만드는 것은 system plugin
    ins = None


    def __init__(self, token=None, proxy=None, user=None, password=None, deviceid=None, uuid=None):
        self.token = token
        if self.token and '_tving_token=' in self.token:
            self.token = self.token.split('=')[1]
        self.proxies = None
        self.proxy = proxy
        if self.proxy != None:
            self.proxies = {"https": proxy, 'http':proxy}
        self.user = user
        self.password = password
        self.deviceid = deviceid
        self.uuid = uuid
    

    def do_login(self, user_id, user_pw, login_type):
        try:
            url = 'https://user.tving.com/user/doLogin.tving'
            if login_type == '0': 
                login_type_value = '10'
            else: 
                login_type_value = '20'
            params = { 
                'userId' : user_id,
                'password' : user_pw,
                'loginType' : login_type_value
            }
            res = requests.post(url, data=params)
            cookie = res.headers['Set-Cookie']
            for c in cookie.split(','):
                c = c.strip()
                if c.startswith('_tving_token'):
                    ret = c.split(';')[0]
                    return ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    def get_device_list(self):
        url = f"http://api.tving.com/v1/user/device/list?{self.default_param[1:]}"
        return self.api_get(url)
        
    def get_info(self, mediacode, streamcode):
        ts = str(int(time.time()))
        try:
            tmp_param = self.default_param
            if streamcode == 'stream70':
                tmp_param = self.default_param.replace('CSSD0100', 'CSSD1200')
            url = f"http://api.tving.com/v2/media/stream/info?info=y{tmp_param}&noCache={ts}&mediaCode={mediacode}&streamCode={streamcode}&deviceId={self.deviceid}"
            #logger.warning(url)
            if self.token != None:
                self.headers['Cookie'] = f"_tving_token={self.token}"
            info = self.api_get(url)
            if streamcode == 'stream70':
                for stream in info['content']['info']['stream']:
                    if stream['code'] == 'stream70':
                        break
                else:
                    #logger.debug("stream70이 없어서 50으로 재요청")
                    return self.get_info(mediacode, 'stream50')
            #logger.debug(d(self.headers))
            #logger.debug(d(info))
            #logger.error(mediacode)

            if info['result']['code'] == "000":
                info['avaliable'] = True
            else:
                info['avaliable'] = False
                return info
            
            #logger.error(info['stream']['drm_yn'])
            if 'drm_yn' in info['stream'] and info['stream']['drm_yn'] == 'Y' and '4k_nondrm_url' not in info['stream']['broadcast']:
                info['drm'] = True
                info['play_info'] = {
                    'drm' : True,
                    'uri' : self.__decrypt2(mediacode, ts, info['stream']['broadcast']['widevine']['broad_url']),
                    'drm_scheme' : 'widevine',
                    'drm_license_uri' : 'http://cj.drmkeyserver.com/widevine_license',
                    'drm_key_request_properties': {
                        'origin' : 'https://www.tving.com',
                        'sec-fetch-site' : 'cross-site',
                        'sec-fetch-mode' : 'cors',
                        'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
                        'Host' : 'cj.drmkeyserver.com',
                        'referer' : 'https://www.tving.com/',
                        'AcquireLicenseAssertion' : info['stream']['drm_license_assertion'],
                    }
                }
                info['play_info']['url'] = info['play_info']['uri']
            else:
                if '4k_nondrm_url' in info['stream']['broadcast']:
                    url = info['stream']['broadcast']['4k_nondrm_url']
                else:
                    url = info['stream']['broadcast']['broad_url']
                decrypted_url = self.__decrypt2(mediacode, ts, url)
                #logger.error(decrypted_url)
                #if decrypted_url.find('m3u8') == -1:
                #    decrypted_url = decrypted_url.replace('rtmp', 'http')
                #    decrypted_url = decrypted_url.replace('?', '/playlist.m3u8?')
                #2020-06-12
                if decrypted_url.find('smil/playlist.m3u8') != -1 and decrypted_url.find('content_type=VOD') != -1 :
                    tmps = decrypted_url.split('playlist.m3u8')
                    r = requests.get(decrypted_url, headers=self.headers, proxies=self.proxies)
                    lines = r.text.split('\n')
                    #logger.debug(lines)
                    i = -1
                    last = ''
                    while len(last) == 0:
                        last = lines[i].strip()
                        i -= 1
                    decrypted_url = '%s%s' % (tmps[0], last)
                    #logger.debug(f"VOD : {decrypted_url}")
                if 'manifest.m3u8' in decrypted_url: #QVOD
                    r = requests.get(decrypted_url, headers=self.headers, proxies=self.proxies)
                    lines = r.text.split('\n')
                    i = -1
                    last = ''
                    while len(last) == 0:
                        last = lines[i].strip()
                        i -= 1
                    tmps = decrypted_url.split('//')
                    tmps2 = tmps[1].split('/', 1)
                    tmps3 = tmps2[1].rsplit('/', 1)
                    tmps3[1] = re.sub(r'manifest\.m3u8\?start=(\d|-|:)+&end=(\d|-|:)+', '', tmps3[1])
                    decrypted_url = f"{tmps[0]}//{tmps2[0]}{last}{tmps3[1]}"
                    
                info['broad_url'] = decrypted_url
                info['drm'] = False
                info['play_info'] = {
                    'drm': False, 
                    'hls': decrypted_url,
                    'url': decrypted_url,
                }
            if mediacode[0] in ['E', 'M']:
                info['filename'] = self.get_filename(info)
            return info
        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())



    

    # list_type : all, live, vod
    def get_live_list(self, list_type='live', order='rating', include_drm=False):

        def func(param, page, order='rating', include_drm=True):
            has_more = 'N'
            try:
                result = []
                url = f'https://api.tving.com/v2/media/lives?cacheType=main&pageNo={page}&pageSize=20&order={order}&adult=all&free=all&guest=all&scope=all{param}{self.default_param}'
                data = self.api_get(url)

                #logger.debug(url)
                for item in data["result"]:
                    try:
                        # 2020-11-10 현재 /v1 에서는 drm채널인지 알려주지않고, 방송이 drm 적용인지 알려줌. 그냥 fix로..
                        info = {'is_drm':self.is_drm_channel(item['live_code'])}
                        info['id'] = item["live_code"]
                        info['title'] = item['schedule']['channel']['name']['ko']
                        info['episode_title'] = ' '
                        info['img'] = 'http://image.tving.com/upload/cms/caic/CAIC1900/%s.png' % item["live_code"]
                        if item['schedule']['episode'] is not None:
                            info['episode_title'] = item['schedule']['episode']['name']['ko']
                            if info['title'].startswith('CH.') and len(item['schedule']['episode']['image']) > 0:
                                info['img'] = 'http://image.tving.com' + item['schedule']['episode']['image'][0]['url']
                        #info['free'] = (item['schedule']['broadcast_url'][0]['broad_url1'].find('drm') == -1)
                        info['summary'] = info['episode_title']
                        result.append(info)
                    except Exception as exception:
                        logger.error('Exception:%s', exception)
                        logger.error(traceback.format_exc())
                has_more = data["has_more"]
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
            return has_more, result

        ret = []
        if list_type == 'live': 
            params = ['&channelType=CPCS0100,CPCS0400']
        elif list_type == 'vod': 
            params = ['&channelType=CPCS0300']
        elif list_type == 'all': 
            params = ['&channelType=CPCS0100,CPCS0400', '&channelType=CPCS0300']
        else:
            params = ['&channelType=CPCS0100,CPCS0400']

        for param in params:
            page = 1
            while True:
                hasMore, data = func(param, page, order=order, include_drm=include_drm)
                ret += data
                if hasMore == 'N': 
                    break
                page += 1
        return ret




    def get_vod_list(self, program_code=None, page=1):
        url = f'http://api.tving.com/v2/media/episodes?pageNo={page}&pageSize=18&adult=all&guest=all&scope=all&personal=N{self.default_param}'
        if program_code is not None: 
            url += f'&free=all&order=frequencyDesc&programCode={program_code}'
        else:
            url += "&free=all&lastFrequency=n&order=broadDate"
        return self.api_get(url)
    

    def get_vod_list_genre(self, genre, page=1):
        url = f'http://api.tving.com/v2/media/episodes?pageNo={page}&pageSize=18&adult=all&guest=all&scope=all&personal=N{self.default_param}'
        if genre != None and genre != 'all':
            url += f"&free=all&lastFrequency=y&order=broadDate&categoryCode={genre}"
        else:
            url += "&free=all&lastFrequency=y&order=broadDate"
        return self.api_get(url)

    
    def get_movie_list(self, page=1, category='all'):
        url = f'https://api.tving.com/v2/media/movies?pageNo={page}&pageSize=24&order=viewDay&free=all&adult=all&guest=all&scope=all&productPackageCode=338723&personal=N&diversityYn=N{self.default_param}'
        if category != 'all':
            url += f'&multiCategoryCode={category}'
        return self.api_get(url)


    def get_frequency_programid(self, programid, page=1):
        url = f'https://api.tving.com/v2/media/frequency/program/{programid}?pageNo={page}&pageSize=10&order=new&free=all&adult=all&scope=all{self.default_param}'
        return self.api_get(url)
        

    def get_schedules(self, code, date, start_time, end_time):
        url = f"https://api.tving.com/v2/media/schedules?pageNo=1&pageSize=20&order=chno&scope=all&adult=n&free=all&broadDate={date}&broadcastDate={date}&startBroadTime={start_time}&endBroadTime={end_time}&channelCode={','.join(code)}{self.default_param}"
        return self.api_get(url)


    def get_program_programid(self, programid):
        url = f'https://api.tving.com/v2/media/program/{programid}?pageNo=1&pageSize=10&order=name{self.default_param}'
        return self.api_get(url)
        

    def search(keyword):
        # gubun VODBC, VODMV
        try:
            import urllib.parse
            url = 'https://search.tving.com/search/common/module/getAkc.jsp?kwd=' + urllib.parse.quote(str(keyword))
            data = self.api_get(url)
            if 'dataList' in data['akcRsb']:
                return data['akcRsb']['dataList']
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    def api_get(self, url):
        try:
            if self.token != None:
                self.headers['Cookie'] = f"_tving_token={self.token}"
            data = requests.get(url, headers=self.headers, proxies=self.proxies).json()
            try:
                if type(data['body']['result']) == type({}) and data['body']['result']['message'] != None:
                    logger.debug(f"tving api message : {data['body']['result']['message']}")
            except:
                pass
            if data['header']['status'] == 200:
                return data['body']
        except Exception as e:
            logger.error(f'url: {url}')
            logger.error(f"Exception:{str(e)}")
            logger.error(traceback.format_exc())



    def is_drm_channel(self, code):
        # C07381:ocn C05661:디즈니채널  C44441:koon  C04601:ocn movie  C07382:ocn thrill
        return (code in ['C07381', 'C05661', 'C44441', 'C04601', 'C07382'])

  

    def get_filename(self, episode_data):
        try:
            title = episode_data["content"]["program_name"]
            title = title.replace("<", "").replace(">", "").replace("\\", "").replace("/", "").replace(":", "").replace("*", "").replace("\"", "").replace("|", "").replace("?", "").replace("  ", " ").strip()
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

            if 'frequency' in episode_data["content"]:
                episodeno = episode_data["content"]["frequency"]
                airdate = str(episode_data["content"]["info"]["episode"]["broadcast_date"])[2:]
                if episodeno > 0:
                    ret = f"{title}.E{str(episodeno).zfill(2)}.{airdate}.{qualityRes}-ST.mp4"
                else:
                    ret = f"{title}.{airdate}.{qualityRes}-ST.mp4"
            else:
                ret = f"{title}.{qualityRes}-ST.mp4"
            #if episode_data['play_info']['drm']:
            #    ret = ret.replace('.mp4', '.mkv')
            from support.base import SupportFile
            return SupportFile.text_for_filename(ret)
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
        

    def get_quality_to_tving(self, quality):
        if quality == 'FHD':
            return 'stream50'
        elif quality == 'HD':
            return 'stream40'
        elif quality == 'SD':
            return 'stream30'
        elif quality == 'UHD':
            return 'stream70'
        return 'stream50'



    def __decrypt2(self, mediacode, ts, url):
        try:
            #raise Exception('test')
            import sc
            ret = sc.td1(mediacode, str(ts), url).strip()
            #data = sc.td1(code, ts, url)
            ret = re.sub('[^ -~]+', '', ret)
            #logger.error(f"[{ret}]")
            return ret
        except Exception as e:
            logger.error(f"Exception:{str(e)}")
            #logger.error(traceback.format_exc())
            data = {'url':url, 'code':mediacode, 'ts':ts}
            ret = requests.post('https://sjva.me/sjva/tving.php', data=data).json()
            return ret['url']
    







if __name__ == '__main__':
    import argparse
    #from support.base import d, get_logger
    from lib_wvtool import WVDownloader

    parser = argparse.ArgumentParser()
    parser.add_argument('--code', required=True, help='컨텐츠 코드')
    parser.add_argument('--quality', required=False, default='stream50', help='화질')
    parser.add_argument('--token', required=True,)
    parser.add_argument('--proxy', default=None)
    parser.add_argument('--deviceid', default=None)
    parser.add_argument('--folder_tmp', default=None)
    parser.add_argument('--folder_output', default=None)

    args = parser.parse_args()
    info = SupportTving(token=args.token, proxy=args.proxy, deviceid=args.deviceid).get_info(args.code, args.quality)
    logger.debug(d(info['play_info']))
    if info['play_info']['drm']:
        SupportTving.headers['Cookie'] = f"_tving_token={args.token}"
        downloader = WVDownloader({
            'logger' : logger,
            'mpd_url' : info['play_info']['uri'],
            'code' : args.code,
            'output_filename' : info['filename'],
            'license_headers' : info['play_info']['drm_key_request_properties'],
            'license_url' : info['play_info']['drm_license_uri'],
            'clean' : True,
            'folder_output': args.folder_output,
            'folder_tmp': args.folder_tmp,
            'mpd_headers' : SupportTving.headers
            
        })
        downloader.download()
    else:
        logger.error("DRM 영상이 아닙니다.")
    #print(args)


















































