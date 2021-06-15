# -*- coding: utf-8 -*-
#########################################################
# python
import os, re
import traceback
import time
import threading
import shutil

from tool_base import d
from . import logger


EXTENSION = 'mp4|avi|mkv|ts|wmv|m2ts|smi|srt|ass|m4v|flv|asf|mpg|ogm'

REGEXS = [
    r'^(?P<name>.*?)\.([sS](?P<sno>\d+))?[eE](?P<no>\d+)(\-E\d{1,4})?\.?(END\.)?(?P<date>\d{6})\.(?P<etc>.*?)(?P<quality>\d+)[p|P](\-?(?P<release>.*?))?(\.(.*?))?$',
    r'^(?P<name>.*?)\s([sS](?P<sno>\d+))?[eE](?P<no>\d+)(\-E\d{1,4})?\.?(END\.)?(?P<date>\d{6})\.(?P<etc>.*?)(?P<quality>\d+)[p|P](?P<more>\..*?)(?P<ext>\.[\w|\d]{3})$',
    r'^(?P<name>.*?)\.([sS](?P<sno>\d+))?(E(?P<no>\d+)\.?)?(END\.)?(?P<date>\d{6})\.(?P<etc>.*?)(?P<quality>\d+)[p|P](\-?(?P<release>.*?))?(\.(.*?))?$',
    r'^(?P<name>.*?)([sS](?P<sno>\d+))?[eE](?P<no>\d+)', # 외국 릴
    r'^(?P<name>.*?)\.(Series\.(?P<sno>\d+)\.)?(?P<no>\d+)of', # 외국 릴
    r'^(?P<name>.*?)[\s\(](?P<no>\d+)[회화]',
    
]

#합본처리 제외
#_REGEX_FILENAME_RENAME = r'(?P<title>.*?)[\s\.]E?(?P<no>\d{1,2})[\-\~\s\.]?E?\d{1,2}'



class EntityKtv(object):
    meta_cache = {}
    def __init__(self, filename, dirname=None, meta=False):
        self.data = {
            'filename' : {
                'original' : filename, 
                'dirname' : dirname, 
                'is_matched' : False,
                'match_index' : -1,
            },
            'meta' : {
                'find':False,
            },
            'process_info' : {
                'rebuild':'',
                'status':''
            }
        }
        self.analyze()

        search_try = False
        if meta and self.data['filename']['is_matched']:
            if self.data['filename']['match_index'] in [3, 4]:
                from tool_base import ToolHangul
                info = ToolHangul.language_info(self.data['filename']['name'])
                logger.warning(f"language : {info}")
                if info[0] == 0:
                    search_try = True
                    self.find_meta_tmdb()

            if search_try == False:
                self.find_meta()

            if self.data['meta']['find']:
                try:
                    logger.warning(f"찾은 메타 : {self.data['meta']['info']['title']} {self.data['meta']['info']['code']}")
                    if self.data['filename']['date'] == '':
                        self.data['process_info']['status'] = 'no_date'
                    else:
                        self.check_episode_no()
                except Exception as exception:
                    logger.debug('Exception:%s', exception)
                    logger.debug(traceback.format_exc())


    def analyze(self):
        def get(md, field):
            if field in md and md[field] is not None:
                return md[field]
            return ''

        for idx, regex in enumerate(REGEXS):
            match = re.compile(regex).match(self.data['filename']['original'])
            if not match:
                continue
            md = match.groupdict()
            self.data['filename']['is_matched'] = True
            self.data['filename']['match_index'] = idx
            self.data['filename']['name'] = get(md, 'name').replace('.', ' ').strip()
            tmp = get(md, 'sno')
            self.data['filename']['sno'] = int(tmp) if tmp != '' else 1
            tmp = get(md, 'no')
            try:
                self.data['filename']['no'] = int(tmp) if tmp != '' else -1
                if self.data['filename']['no'] == 0:
                    raise Exception('0')
            except:
                self.data['process_info']['rebuild'] += 'remove_episode'
                self.data['filename']['no'] = -1

            self.data['filename']['date'] = get(md, 'date')
            self.data['filename']['etc'] = get(md, 'etc')
            self.data['filename']['quality'] = get(md, 'quality')
            self.data['filename']['release'] = get(md, 'release')
            self.data['filename']['more'] = get(md, 'more')
            
            logger.warning(d(self.data['filename']))
            break
        


    def check_episode_no(self):
        logger.warning(self.data['filename']['original'])
        logger.warning(f"방송일 : {self.data['filename']['date']} / 번호 : {self.data['filename']['no']}")
        #if self.data['meta']['info']['extra_info']['episodes'].keys()
        #if self.data['filename']['no'] == -1:


        if self.data['filename']['no'] > 0 and self.data['filename']['no'] in self.data['meta']['info']['extra_info']['episodes']:
            logger.warning(f"에피소드 정보 있음")
            logger.warning(self.data['meta']['info']['extra_info']['episodes'][self.data['filename']['no']])
            tmp = self.data['meta']['info']['extra_info']['episodes'][self.data['filename']['no']]
            # daum만 체크
            if 'daum' in tmp:
                value = tmp['daum']
                tmp2 = value['premiered']
                if self.data['filename']['date'] == tmp2.replace('-', '')[2:]:
                    logger.warning("메타와 방송일, 번호 일치")
                    self.data['process_info']['status'] = 'number_and_date_match'
                    return
                else:
                    logger.warning("날짜가 맞지 않음.")
                    #하루차이는 매칭시킴
                    if abs(int(self.data['filename']['date']) - int(tmp2.replace('-', '')[2:])) in [1, 70, 71, 72, 73, 8870]:
                        self.data['process_info']['status'] = 'number_and_date_match'
                        self.data['process_info']['rebuild'] += 'change_date'
                        self.data['process_info']['change_date'] = tmp2.replace('-', '')[2:]
                        return

        # 맞는 에피소드 몾찾음
        if len(self.data['meta']['info']['extra_info']['episodes']) == 0:
            # 메타검색은 했지만 에피소드 목록이 없음.
            self.data['process_info']['status'] = 'meta_epi_empty'
            return

        # 방송일에 맞는 에피 번호 찾기
        logger.warning(f"에피소드 목록")

        for epi_no, value in self.data['meta']['info']['extra_info']['episodes'].items():
            if 'daum' in value:
                site_info = value['daum']
                tmp2 = site_info['premiered']
                if self.data['filename']['date'] == tmp2.replace('-', '')[2:]:
                    logger.warning(f"다음에서 새로운 에피소드 번호 찾음 : {epi_no}")
                    logger.warning(d(site_info))
                    self.data['process_info']['status'] = 'number_and_date_match'
                    self.data['process_info']['rebuild'] += 'change_epi_number'
                    self.data['process_info']['change_epi_number'] = epi_no
                    return
        
        # 다음에서 몾찾았지만 티빙 웨이브에 있다면 그대로 유지해야함.
        # 굳이 찾을 필요없이 릴리즈로 맞다고 넘김
        # 근데 받을때는 에피번호가 없고 나중에 메타가 생기는 경우가 잇는 것 같음
        if self.data['filename']['no'] != -1:
            if self.data['filename']['release'] in ['ST', 'SW', 'SWQ', 'STQ', 'ODK']:
                self.data['process_info']['status'] = 'number_and_date_match_by_release'
                return
        else:
            for epi_no, value in self.data['meta']['info']['extra_info']['episodes'].items():
                for site, site_info in value.items():
                    if site == 'daum':
                        continue
                    tmp2 = site_info['premiered']
                    if self.data['filename']['date'] == tmp2.replace('-', '')[2:]:
                        logger.warning(f"다음에서 새로운 에피소드 번호 찾음 : {epi_no}")
                        logger.warning(d(site_info))
                        self.data['process_info']['status'] = 'number_and_date_match_ott'
                        self.data['process_info']['rebuild'] += 'change_epi_number'
                        self.data['process_info']['change_epi_number'] = epi_no
                        return


        logger.error("에피소드 목록이 있지만 맞는 메타를 찾지 못함")
        logger.error(f"에피소드 번호 {epi_no}")
        logger.error(f"에피소드 번호 {self.data['filename']['original']}")
        logger.warning(d(self.data['meta']['info']['extra_info']['episodes']))

        logger.debug("티빙, 웨이브에서 찾음")
        if self.data['filename']['no'] > 0 and self.data['filename']['no'] in self.data['meta']['info']['extra_info']['episodes']:
            logger.warning(f"에피소드 정보 있음 22")
            logger.warning(self.data['meta']['info']['extra_info']['episodes'][self.data['filename']['no']])
            tmp = self.data['meta']['info']['extra_info']['episodes'][self.data['filename']['no']]
            # daum만 체크
            for site, value in tmp.items():
                if site == 'daum':
                    continue
                tmp2 = value['premiered']
                if self.data['filename']['date'] == tmp2.replace('-', '')[2:]:
                    logger.warning(f"메타와 방송일, 번호 일치 {site}")
                    self.data['process_info']['status'] = 'number_and_date_match'
                    return
                else:
                    logger.warning("날짜가 맞지 않음.")
                    #하루차이는 매칭시킴
                    if abs(int(self.data['filename']['date']) - int(tmp2.replace('-', '')[2:])) in [1, 70, 71, 72, 73, 8870]:
                        self.data['process_info']['status'] = 'number_and_date_match'
                        self.data['process_info']['rebuild'] += 'change_date'
                        self.data['process_info']['change_date'] = tmp2.replace('-', '')[2:]
                        return

        logger.debug("에피소드 목록중 티빙, 웨이브에서 찾음 ")
        for epi_no, value in self.data['meta']['info']['extra_info']['episodes'].items():
            for site, site_info in value.items(): 
                if site == 'daum':
                    continue
                tmp2 = site_info['premiered']
                if self.data['filename']['date'] == tmp2.replace('-', '')[2:]:
                    logger.warning(f"2222 다음에서 새로운 에피소드 번호 찾음 : {epi_no}")
                    logger.warning(d(site_info))
                    self.data['process_info']['status'] = 'number_and_date_match'
                    self.data['process_info']['rebuild'] += 'change_epi_number'
                    self.data['process_info']['change_epi_number'] = epi_no
                    return

        if epi_no < self.data['filename']['no']:
            self.data['process_info']['status'] = 'meta_epi_not_find'
            
        self.data['process_info']['status'] = 'meta_epi_not_find'
        #for tmp in self.data['meta']['info']['extra_info']['episode']:
        #    logger.debug((tmp))




    
    def find_meta(self):
        from lib_metadata import SiteDaumTv, SiteTvingTv, SiteWavveTv
        module_map = [('daum', SiteDaumTv), ('tving',SiteTvingTv), ('wavve',SiteWavveTv)]
        #if self.data['filename']['name'] in EntityKtv.meta_cache:
        #    self.data['meta'] = EntityKtv.meta_cache[self.data['filename']['name']]
        #    return
        #module_list = [SiteDaumTv, SiteTvingTv, SiteWavveTv]
        #module_list = [SiteDaumTv]
        
        for site, site_class in module_map:
            try:
                logger.warning(f"{site} {self.data['filename']['name']}")
                if self.data['filename']['name'] in EntityKtv.meta_cache and site in EntityKtv.meta_cache[self.data['filename']['name']]:
                    self.data['meta'] = EntityKtv.meta_cache[self.data['filename']['name']][site]
                    # 없는 것도 저장하여 중복검색 방지
                    if self.data['meta']['find']:
                        return
                site_data = site_class.search(self.data['filename']['name'])
                #logger.warning(f"{site} {d(site_data)}")
                if site_data['ret'] == 'success':
                    if site == 'daum':
                        self.data['meta']['search'] = site_data['data']
                        self.data['meta']['info'] = site_class.info(self.data['meta']['search']['code'], self.data['meta']['search']['title'])['data']
                        if self.data['meta']['info']['genre'][0] != '드라마' and self.data['meta']['info']['genre'][0].find('드라마') != -1 and self.data['filename']['release']in ['ST', 'SW']:
                            continue

                        SiteTvingTv.apply_tv_by_search(self.data['meta']['info'], force_search_title=self.data['filename']['name'])
                        SiteWavveTv.apply_tv_by_search(self.data['meta']['info'], force_search_title=self.data['filename']['name'])
                        self.data['meta']['find'] = True
                    else:
                        if len(site_data['data']) > 0 and site_data['data'][0]['score'] > 90:
                            self.data['meta']['search'] = site_data['data'][0]
                            self.data['meta']['info'] = site_class.info(self.data['meta']['search']['code'])['data']
                            self.data['meta']['find'] = True
                
                if self.data['meta']['find']:
                    if len(self.data['meta']['info']['genre']) == 0:
                        self.data['meta']['info']['genre'].append('기타')
                    if self.data['filename']['name'] not in EntityKtv.meta_cache:
                        EntityKtv.meta_cache[self.data['filename']['name']] = {}
                    EntityKtv.meta_cache[self.data['filename']['name']][site] = self.data['meta']
                    logger.error('11111111111111111111')
                    return
                else:
                    logger.error('222222222222222222')
                    if self.data['filename']['name'] not in EntityKtv.meta_cache:
                        EntityKtv.meta_cache[self.data['filename']['name']] = {}
                    EntityKtv.meta_cache[self.data['filename']['name']][site] = self.data['meta']
            except Exception as exception:
                logger.debug('Exception:%s', exception)
                logger.debug(traceback.format_exc())


    def get_newfilename(self):
        if self.data['filename']['match_index'] == 2:
           self.data['process_info']['rebuild'] += f"match_{self.data['filename']['match_index']}"

        logger.error(self.data['process_info']['rebuild'])
        if self.data['process_info']['rebuild'] in ['', 'match_2', 'meta_epi_not_find', 'match_3']:
            return self.data['filename']['original']

        elif self.data['process_info']['rebuild'] == 'remove_episode':
            logger.error(self.data['filename']['original'])
            return re.sub('\.[eE].*?\.', '.', self.data['filename']['original'])
        elif self.data['process_info']['rebuild'] == 'remove_episodechange_epi_number' and self.data['process_info']['change_epi_number'] == 0:
            logger.error(self.data['filename']['original'])
            return re.sub('\.[eE].*?\.', '.', self.data['filename']['original'])   
        
        elif self.data['process_info']['rebuild'].startswith('match_'):
            logger.error(f"match_ {self.data['filename']['original']}")
            time.sleep(100)
        elif self.data['process_info']['rebuild'] == 'change_epi_number':
            logger.error('change_epi_number')
            return re.sub('\.[eE].*?\.', f".E{str(self.data['process_info']['change_epi_number']).zfill(2)}.", self.data['filename']['original'])
            time.sleep(100)
        elif self.data['process_info']['rebuild'] == 'change_epi_numbermatch_2':
            # 날짜만 있는 원본 에피소드 삽입
            logger.error('change_epi_numbermatch_2')
            return self.data['filename']['original'].replace(f".{self.data['filename']['date']}.", f".E{str(self.data['process_info']['change_epi_number']).zfill(2)}.{self.data['filename']['date']}.")
        elif self.data['process_info']['rebuild'] == 'change_date':
            logger.error('change_date')
            return self.data['filename']['original'].replace(f".{self.data['filename']['date']}.", f".{self.data['process_info']['change_date']}.")
            time.sleep(100)
         
        else:
            pass

    

    def find_meta_tmdb(self):
        from lib_metadata import SiteTmdbFtv
        from tool_base import ToolBaseFile
        module_map = [('tmdb', SiteTmdbFtv)]
        
        for site, site_class in module_map:
            try:
                logger.warning(f"{site} {self.data['filename']['name']}")
                if self.data['filename']['name'] in EntityKtv.meta_cache and site in EntityKtv.meta_cache[self.data['filename']['name']]:
                    self.data['meta'] = EntityKtv.meta_cache[self.data['filename']['name']][site]
                    # 없는 것도 저장하여 중복검색 방지
                    if self.data['meta']['find']:
                        return
                site_data = site_class.search(self.data['filename']['name'])
                logger.warning(f"{site} {d(site_data)}")
                if site_data['ret'] == 'success':
                    if len(site_data['data']) > 0 and site_data['data'][0]['score'] >= 80:
                        self.data['filename']['name'] = site_data['data'][0]['title']
                        self.find_meta()
                        if self.data['meta']['find'] == False:
                            self.data['process_info']['status'] = 'ftv'
                            self.data['process_info']['ftv_title'] = ToolBaseFile.text_for_filename(site_data['data'][0]['title'])
                            self.data['process_info']['ftv_year'] = site_data['data'][0]['year']
                        return
            except Exception as exception:
                logger.debug('Exception:%s', exception)
                logger.debug(traceback.format_exc())
