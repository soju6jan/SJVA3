# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import time
import threading
import shutil
import re
from lxml import html
import requests

from . import logger, Vars
from framework import app
from system import SystemLogicTrans

EXTENSION = 'mp4|avi|mkv|ts|wmv|m2ts|smi|srt|ass|m4v|flv|asf|mpg|ogm'


def change_filename_censored(filename):
 
    #logger.debug('get_plex_filename:%s', file)
    original_filename = filename
    #return file
    filename = filename.lower()
    
    #-h264 제거
    filename = filename.replace('-h264', '')
    filename = filename.replace('-264', '')
    #2019-10-06 -■-IBW-670Z_1080p.mkv => ibw-6701080 [-■-IBW-670Z_1080p].mkv
    filename = filename.replace('z_1080p', '').replace('z_720p', '')
    filename = filename.replace('z_', '')
    filename = filename.replace('-c', '')
    #if file.find('@') != -1:
    #    file = file.split('@')[1]

    # 1080p
    regex = r'^(?P<code>.*?)\.1080p\.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).match(filename)
    if match:
        filename = '%s.%s' % (match.group('code'), match.group('ext'))
    # fhd
    #regex = r'^(?P<code>.*?)fhd\.(?P<ext>%s)$' % EXTENSION
    #2019-10-06
    # sdmu-676_FHD.mp4 => sdmu-676cd-1 [sdmu-676_FHD].mp4
    regex = r'^(?P<code>.*?)(\_|\-)fhd\.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).match(filename)
    if match:
        filename = '%s.%s' % (match.group('code'), match.group('ext'))

    # [ ]숫자 제거
    regex = r'^\[.*?\]\d+(?P<code>.*?)\.(?P<ext>%s)$'
    match = re.compile(regex).match(filename)
    if match:
        filename = '%s.%s' % (match.group('code'), match.group('ext'))

    # [ ] 제거
    regex = r'^\[.*?\](?P<code>.*?)\.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).match(filename)
    if match:
        filename = '%s.%s' % (match.group('code'), match.group('ext'))
    
    # 3,4자리 숫자
    regex = r'^\d{3,4}(?P<code>.*?)\.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).match(filename)
    if match:
        filename = '%s.%s' % (match.group('code'), match.group('ext'))

    regex = r'^.*\.com\-?\d*\-?\d*@?(?P<code>.*?)(\-h264)??\.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).match(filename)
    if match:
        filename = '%s.%s' % (match.group('code'), match.group('ext'))
    
    regex = r'^(?P<dummy>.*\.com.*?)(?P<code>[a-z]+)'
    match = re.compile(regex).match(filename)
    if match:
        filename = filename.replace(match.group('dummy'), '')
    
    # -5 제거
    regex = r'^(?P<code>.*?)\-5.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).match(filename)
    if match:
        filename = '%s.%s' % (match.group('code'), match.group('ext'))

    
    # dhd1080.com@1fset00597hhb.mp4
    #regex = r'^.*?com@(\d)?(?P<code>[a-z]+\d+)\w+.(?P<ext>%s)$' % EXTENSION
    #match = re.compile(regex).match(file)
    #if match:
    #    file = '%s.%s' % (match.group('code'), match.group('ext'))


    # s-cute
    regex = r'^s-cute\s(?P<code>\d{3}).*?.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).match(filename)
    if match:
        ret = 'scute-%s.%s' % (match.group('code'), match.group('ext'))
        return ret.lower()



    regex = r'^(?P<name>[a-zA-Z]+)[-_]?(?P<no>\d+)(([-_]?(cd)?(?P<part_no>\d))|[-_]?(?P<part_char>\w))?\.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).match(filename)
    if match:
        ret = filename
        part = None
        if match.group('part_no') is not None:
            part = 'cd%s' % match.group('part_no')
        elif match.group('part_char') is not None:
            if app.config['config']['is_py2']:
                part = 'cd%s' % (ord(match.group('part_char').lower()) - ord('a') + 1)
            else:
                part = 'cd%s' % (match.group('part_char').lower() - 'a' + 1)
        if part is None:
            ret = '%s-%s.%s' % (match.group('name').lower(), match.group('no'), match.group('ext'))
        else:
            ret = '%s-%s%s.%s' % (match.group('name').lower(), match.group('no'), part, match.group('ext'))
        #logger.debug('%s -> %s' % (file, ret))
        return ret.lower()
    
    # T28 - 매치여야함.
    #logger.debug('N2 before:%s', file)
    regex = r'(?P<name>[a-zA-Z]+\d+)\-(?P<no>\d+).*?\.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).match(filename)
    if match:
        ret = '%s-%s.%s' % (match.group('name'), match.group('no'), match.group('ext'))
        #logger.debug('N2. %s -> %s' % (file, ret))
        return ret.lower()

    # 오리지널로 ABC123 매치여야함.
    # hjd2048.com-0113meyd466-264.mp4
    #logger.debug('N3 before:%s', original_filename)

    regex = r'^(?P<name>[a-zA-Z]{3,})\-?(?P<no>\d+).*?\.(?P<ext>%s)$' % EXTENSION
    #logger.debug(file)
    match = re.compile(regex).match(filename)
    if match:
        ret = '%s-%s.%s' % (match.group('name'), match.group('no'), match.group('ext'))
        #logger.debug('N3. %s -> %s' % (file, ret))]
        #logger.debug('match 00')
        return ret.lower()

    regex = r'^(?P<name>[a-zA-Z]{3,})\-?(?P<no>\d+).*?\.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).match(original_filename)
    if match:
        ret = '%s-%s.%s' % (match.group('name'), match.group('no'), match.group('ext'))
        #logger.debug('N3. %s -> %s' % (file, ret))]
        #logger.debug('match 11')
        return ret.lower()

    # 서치
    #logger.debug('N1 before:%s', file)
    regex = r'(?P<name>[a-zA-Z]+)\-(?P<no>\d+).*?\.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).search(filename)
    if match:
        ret = '%s-%s.%s' % (match.group('name'), match.group('no'), match.group('ext'))
        #logger.debug('N1. %s -> %s' % (file, ret))
        #logger.debug('match 22')
        return ret.lower()
    
    # 서치
    #logger.debug('N1 before:%s', file)
    regex = r'(?P<name>[a-zA-Z]+)\-(?P<no>\d+).*?\.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).search(original_filename)
    if match:
        ret = '%s-%s.%s' % (match.group('name'), match.group('no'), match.group('ext'))
        #logger.debug('N1. %s -> %s' % (file, ret))
        #logger.debug('match 33')
        return ret.lower()
    
    #20-02-02
    regex = r'\w+.\w+@(?P<name>[a-zA-Z]+)(?P<no>\d{5}).*?.(?P<ext>%s)$' % EXTENSION
    match = re.compile(regex).search(original_filename)
    if match:
        no = match.group('no').replace('0', '').zfill(3)
        ret = '%s-%s.%s' % (match.group('name'), no, match.group('ext'))
        #logger.debug('match 44')
        return ret.lower()


    #logger.debug('%s -> %s' % (file, None))
    return None


def change_filename_censored_by_save_original(include_original_filename, original_filename, new_filename, option='0', original_filepath=None):
    ''' 원본파일명 보존 옵션에 의해 파일명을 변경한다. '''

    try:
        if include_original_filename:
            new_name, new_ext = os.path.splitext(new_filename)
            part = None
            match = re.search(r'(?P<part>cd\d+)$', new_name)
            if match:
                # cd1 앞에가 같아야함.
                return new_filename
                part = match.group('part')
                new_name = new_name.replace(part, '')

            ori_name, ori_ext = os.path.splitext(original_filename)
            # 2019-07-30
            ori_name = ori_name.replace('[', '(').replace(']', ')').strip()
            if part is None:
                
                if option == '0':
                    return '%s [%s]%s' % (new_name, ori_name, new_ext)
                elif option == '1':
                    return '%s [%s(%s)]%s' % (new_name, ori_name, os.stat(original_filepath).st_size, new_ext)
                elif option == '2':
                    from framework.util import Util
                    return '%s [%s(%s)]%s' % (new_name, ori_name, Util.sizeof_fmt(os.stat(original_filepath).st_size, suffix='B'), new_ext)
                return '%s [%s]%s' % (new_name, ori_name, new_ext)
            else:
                #안씀
                return '%s [%s] %s%s' % (new_name, ori_name, part, new_ext)
        else:
            return new_filename
    except Exception as exception:
        logger.debug('Exception:%s', exception)
        logger.debug(traceback.format_exc())



_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cookie' : 'over18=1;age_check_done=1;',
} 


_genre = {u'巨尻':u'큰엉덩이', u'ギャル':u'갸루', u'着エロ':u'착에로', u'競泳・スクール水着':u'학교수영복', u'日焼け':u'태닝', u'指マン':u'핑거링', u'潮吹き':u'시오후키', u'ごっくん':u'곳쿤', u'パイズリ':u'파이즈리', u'手コキ':u'수음', u'淫語':u'음란한말', u'姉・妹':u'남매', u'お姉さん':u'누님', u'インストラクター':u'트레이너', u'ぶっかけ':u'붓카케', u'シックスナイン':u'69', u'ボディコン':u'타이트원피스', u'電マ':u'전동마사지', u'イタズラ':u'짖궂음', u'足コキ':u'풋잡', u'原作コラボ':u'원작각색', u'看護婦・ナース':u'간호사', u'コンパニオン':u'접객업', u'家庭教師':u'과외', u'キス・接吻':u'딥키스', u'局部アップ':u'음부확대', u'ポルチオ':u'자궁성감자극', u'セーラー服':u'교복', u'イラマチオ':u'격한페라·딥스로트', u'投稿':u'투고', u'キャンギャル':u'도우미걸', u'女優ベスト・総集編':u'베스트총집편', u'クンニ':u'커닐링구스', u'アナル':u'항문노출', u'超乳':u'폭유', u'復刻':u'리마스터', u'投稿':u'투고', u'義母':u'새어머니', u'おもちゃ':u'노리개', u'くノ一':u'여자닌자', u'羞恥' : u'수치심', u'ドラッグ':u'최음제', u'パンチラ':u'판치라', u'巨乳フェチ':u'큰가슴', u'巨乳':u'큰가슴', u'レズキス':u'레즈비언', u'レズ':u'레즈비언', u'スパンキング':u'엉덩이때리기', u'放尿・お漏らし':u'방뇨·오모라시', u'アクメ・オーガズム':u'절정·오르가즘', u'ニューハーフ':u'쉬메일', u'鬼畜':u'색마·양아치', u'辱め':u'능욕', u'フェラ':u'펠라치오'}



_studio  = {u'乱丸':u'란마루', u'大洋図書':u'대양도서', u'ミル':u'미루', u'無垢':u'무쿠', u'サムシング':u'Something', u'本中':u'혼나카', u'ナンパJAPAN':u'난파 재팬', u'溜池ゴロー':u'다메이케고로', u'プラム':u'프라무', u'アップス':u'Apps', u'えむっ娘ラボ':u'엠코 라보', u'クンカ':u'킁카', u'映天':u'에이텐', u'ジャムズ':u'JAMS', u'牛感':u'규칸'}


_session = requests.Session()



def search(arg, only_javdb=False, do_trans=True):
    try:
        ret = None
        if only_javdb == False:
            ret = dmm_search(arg, do_trans=do_trans)

        if not ret:
            ret = javdb_search(arg, do_trans=do_trans)
        else:
            wrong_match = True
            for tmp in ret:
                if tmp['score'] >= 90:
                    wrong_match = False
                    break
            if wrong_match:
                ret = ret + javdb_search(arg, do_trans=do_trans)
        return ret
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def update(arg, use_discord_proxy=False):
    try:
        if len(arg) <= 5:
            ret = javdb_update(arg)
        else:
            ret = dmm_update(arg, use_discord_proxy=use_discord_proxy)
        #logger.debug('update : %s', ret['code_show'])
        return ret
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def dmm_search(keyword, do_trans=True):
    try:
        keyword = keyword.strip().lower()
        # 2020-06-24
        if keyword[-3:-1] == 'cd':
            keyword = keyword[:-3]
        keyword = keyword.replace('-', ' ')
        tmps = keyword.split(' ')
        if len(tmps) == 2:
            if len(tmps[1]) <= 5:
                title = '%s%s' % (tmps[0], tmps[1].zfill(5))
            elif len(tmps[1]) > 5:
                title = '%s%s' % (tmps[0], tmps[1])
        else:
            title = keyword
        logger.debug('keyword %s -> %s', keyword, title)

        #url = 'https://www.dmm.co.jp/search/=/searchstr=%s/n1=FgRCTw9VBA4GAVhfWkIHWw__/' % title
        #2020-06-14 n1값이 외국 리전으로 인식함. vpn 연결해서 확인한 값으로 수정
        #url = 'https://www.dmm.co.jp/search/=/searchstr=%s/n1=FgRCTw9VBA4GFUFV/' % title
        #url = 'https://www.dmm.co.jp/search/=/searchstr=%s/analyze=V1ECCVYAUAQ_/n1=FgRCTw9VBA4GFUFV' % title
        url = 'https://www.dmm.co.jp/digital/videoa/-/list/search/=/?searchstr=%s' % title
        logger.debug(url)
        #logger.debug(url)
        page = _session.get(url, headers=_headers, proxies=Vars.proxies)
        data = page.text
        logger.debug('text len : %s', len(data))

        tree = html.fromstring(data)
        lists = tree.xpath('//*[@id="list"]/li')
        #tmp = tree.xpath('//*[@id="list"]')[0]
        #lists = tmp.xpath('li')
        #logger.debug('dmm serarch count:%s' % len(lists))
        ret = []
        score = 60
        logger.debug('len lists2 :%s', len(lists))
        for node in lists:
            try:
                #//*[@id="list"]/li/div/p[2]/a
                entity = {'meta':'dmm'}
                #logger.debug(node.xpath('.//div')[0].text_content())
                #logger.debug(node.xpath('.//div/p[2]')[0].text_content())
                #logger.debug(node.xpath('.//div/p[2]/a')[0].text_content())
                tag = node.xpath('.//div/p[@class="tmb"]/a')[0]
                href = tag.attrib['href'].lower()
                match = re.compile(r'\/cid=(?P<code>.*?)\/').search(href)
                if match:
                    entity['id'] = match.group('code')
                already_exist = False
                for exist_item in ret:
                    if exist_item['id'] == entity['id']:
                        already_exist = True
                        break
                if already_exist:
                    continue
                #logger.debug(entity['id'])
                tag = node.xpath('.//span[1]/img')[0]
                entity['title'] = tag.attrib['alt']
                entity['title_ko'] = SystemLogicTrans.trans(entity['title']) if do_trans else entity['title']
                
                match = re.compile(r'(h_)?\d*(?P<real>[a-zA-Z]+)(?P<no>\d+)([a-zA-Z]+)?$').search(entity['id'])
                if match:
                    entity['id_show'] = '%s%s' % (match.group('real'), match.group('no'))
                else:
                    entity['id_show'] = entity['id']
                #logger.debug(entity['id_show'])
                #logger.debug(title)

                if len(tmps) == 2:
                    #2019-11-20 ntr mntr 둘다100
                    if entity['id_show'] == title:
                        entity['score'] = 100
                    elif entity['id_show'].replace('0','') == title.replace('0',''):
                        entity['score'] = 100
                    elif entity['id_show'].find(title) != -1: #전체포함 DAID => AID
                        entity['score'] = score
                        score += -5
                    elif entity['id'].find(tmps[0]) != -1 and entity['id'].find(tmps[1]) != -1:
                        entity['score'] = score
                        score += -5
                    elif entity['id'].find(tmps[0]) != -1 or entity['id'].find(tmps[1]) != -1:
                        entity['score'] = 60
                    else:
                        entity['score'] = 20
                else:
                    if entity['id'] == tmps[0]:
                        entity['score'] = 100
                    elif entity['id'].find(tmps[0]) != -1:
                        entity['score'] = score
                        score += -5
                    else:
                        entity['score'] = 20
                if entity['id_show'].find ('0000') != -1:
                    entity['id_show'] = entity['id_show'].replace('0000', '-00').upper()
                else:
                    entity['id_show'] = entity['id_show'].replace('00', '-').upper()
                if entity['id_show'].endswith('-'):
                    entity['id_show'] = '%s00' % (entity['id_show'][:-1])
                logger.debug('score :%s %s ', entity['score'], entity['id_show'])
                ret.append(entity)
            except Exception as exception: 
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc()) 
        ret = sorted(ret, key=lambda k: k['score'], reverse=True) 
        
        if len(ret) == 0 and len(tmps) == 2 and len(tmps[1]) == 5:
            new_title = '%s%s' % (tmps[0], tmps[1].zfill(6))
            return dmm_search(new_title)
        else:
            return ret

    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
        return False



def dmm_update(arg, use_discord_proxy=False):
    try:
        from system.model import ModelSetting as SystemModelSetting
        from . import Vars
        url = 'https://www.dmm.co.jp/digital/videoa/-/detail/=/cid=%s/' % arg
        page = _session.get(url, headers=_headers, proxies=Vars.proxies)
        #logger.debug(url)
        data = page.text
        tree = html.fromstring(data)
        ret = {}
        
        
        nodes = tree.xpath('//*[@id="mu"]/div/table//tr/td[1]/div[1]/div[2]')
        if not nodes:
            #logger.debug(data)
            logger.debug('CRITICAL!!!')
            return data
        #a_nodes = nodes[0].xpath('.//a')
        ret['poster_full'] = ''
        ret['poster'] = ''

        try:
            a_nodes = nodes[0].xpath('.//a')
            anodes = a_nodes
            #logger.debug(html.tostring(anodes[0]))
            tag = anodes[0].xpath('.//img')[0]
            ret['poster_full'] = a_nodes[0].attrib['href']
            ret['poster'] = tag.attrib['src']
        except:
            tag = nodes[0].xpath('.//img')[0]
            ret['poster'] = img_tag.attrib['src']
            ret['poster_full'] = ret['poster']


        if ret['poster'] != '' and use_discord_proxy:
            ret['poster'] = '%s/av_agent/api/discord_proxy?url=%s' % (SystemModelSetting.get('ddns'), ret['poster'])
            if SystemModelSetting.get_bool('auth_use_apikey'):
                ret['poster'] += '&apikey=%s' % SystemModelSetting.get('auth_apikey')
        elif ret['poster'] != '':
            ret['poster'] = '%s/av_agent/api/image_proxy?url=%s' % (SystemModelSetting.get('ddns'), ret['poster'])
            if SystemModelSetting.get_bool('auth_use_apikey'):
                ret['poster'] += '&apikey=%s' % SystemModelSetting.get('auth_apikey')        

        if ret['poster_full'] != '' and use_discord_proxy:
            ret['poster_full'] = '%s/av_agent/api/discord_proxy?url=%s' % (SystemModelSetting.get('ddns'), ret['poster_full'])
            if SystemModelSetting.get_bool('auth_use_apikey'):
                ret['poster_full'] += '&apikey=%s' % SystemModelSetting.get('auth_apikey')
        if ret['poster_full'] != '':
            from system.model import ModelSetting as SystemModelSetting
            ret['poster_full'] = '%s/av_agent/api/image_proxy?url=%s' % (SystemModelSetting.get('ddns'), ret['poster_full'])
            if SystemModelSetting.get_bool('auth_use_apikey'):
                ret['poster_full'] += '&apikey=%s' % SystemModelSetting.get('auth_apikey')


        ret['title'] = tag.attrib['alt']
        ret['title_ko'] =  SystemLogicTrans.trans(ret['title'])

        try:
            tag = tree.xpath('//*[@id="mu"]/div/table//tr/td[1]/table//tr[4]/td[2]')
            ret['date'] = tag[0].text_content().replace('/', '').strip()
        except:
            ret['date'] = ''
        
        if len(ret['date']) != 8:
            try:
                tag = tree.xpath('//*[@id="mu"]/div/table//tr/td[1]/table//tr[3]/td[2]')
                ret['date'] = tag[0].text_content().replace('/', '').strip()
            except:
                ret['date'] = ''

        tag = tree.xpath('//*[@id="mu"]/div/table//tr/td[1]/table//tr[5]/td[2]')
        match = re.compile(r'^(?P<time>\d+)').search(tag[0].text_content())
        if match:
            ret['running_time'] = match.group('time')
        else:
            ret['running_time'] = ''
        
        nodes = tree.xpath('//*[@id="performer"]/a')
        ret['performer'] = []
        for node in nodes:    
            entity = {}
            match = re.compile(r'\/id=(?P<id>.*?)\/').search(node.attrib['href'])
            if match:
                entity['id'] = match.group('id')
                entity['name'] = node.text_content()
                entity = get_actor_info(entity)
                ret['performer'].append(entity)
        ret = _set_info(tree, ret, '//*[@id="mu"]/div/table//tr/td[1]/table//tr[7]/td[2]/a', 'director')
        ret = _set_info(tree, ret, '//*[@id="mu"]/div/table//tr/td[1]/table//tr[8]/td[2]/a', 'series')
        ret = _set_info(tree, ret, '//*[@id="mu"]/div/table//tr/td[1]/table//tr[9]/td[2]/a', 'studio')
        ret = _set_info(tree, ret, '//*[@id="mu"]/div/table//tr/td[1]/table//tr[10]/td[2]/a', 'label')
        
        #콘텐츠 유형 :	3D
        #라벨 이후에 3D 는 콘텐츠유형이 들어감
        # 장르와 코드가 영향

        tmp = tree.xpath('//*[@id="mu"]/div/table//tr/td[1]/table//tr[11]/td')[0]
        if tmp.text_content().strip() == u'ジャンル：':
            current_tr_index = 11
        else:
            current_tr_index = 12

        ret['genre'] = []
        nodes = tree.xpath('//*[@id="mu"]/div/table//tr/td[1]/table//tr[%s]/td[2]/a' % current_tr_index)
        for node in nodes:
            tmp = node.text_content().strip()
            #logger.debug(tmp)
            if tmp.find('30％OFF') != -1:
                #logger.debug('30000000000000000000000000')
                continue
            if tmp in _genre:
                ret['genre'].append(_genre[tmp])
                continue
            tmp = SystemLogicTrans.trans(tmp).replace(' ', '')
            #logger.debug(tmp)
            if tmp not in ['고화질', '독점전달', '세트상품', '단체작품', '기간한정세일', '기리모자', '데지모', '슬림', '미소녀', '미유', '망상족', '거유', '에로스', '작은', '섹시']:
                ret['genre'].append(tmp)

        tag = tree.xpath('//*[@id="mu"]/div/table//tr/td[1]/table//tr[%s]/td[2]' % (current_tr_index+1))
        ret['code'] = tag[0].text_content()
        match = re.compile(r'(h_)?\d*(?P<real>[a-zA-Z]+)(?P<no>\d+)([a-zA-Z]+)?$').match(ret['code'])
        if match:
            ret['code_show'] = '%s%s' % (match.group('real'), match.group('no'))
            ret['release'] = match.group('real')
        else:
            ret['code_show'] = ret['code']
            ret['release'] = ''

        #
        if ret['code_show'].find ('0000') != -1:
            ret['code_show'] = ret['code_show'].replace('0000', '-00').upper()
        else:
            ret['code_show'] = ret['code_show'].replace('00', '-').upper()
        if ret['code_show'].endswith('-'):
                ret['code_show'] = '%s00' % (ret['code_show'][:-1])
        
        try:
            ret['rating'] = '0'
            tag = tree.xpath('//*[@id="mu"]/div/table//tr/td[1]/table//tr[13]/td[2]/img')
            if tag:
                match = re.compile(r'\/(?P<rating>.*?)\.gif').match(tag[0].attrib['src'])
                if match:
                    tmps = match.group('rating').split('/')
                    ret['rating'] = tmps[len(tmps)-1].replace('_', '.')
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

        tag = tree.xpath('//*[@id="mu"]/div/table//tr/td[1]/div[4]')
        ret['summary'] = tag[0].text_content().split('※')[0].strip()
        ret['summary_ko'] = SystemLogicTrans.trans(ret['summary'])
        nodes = tree.xpath('//*[@id="sample-image-block"]/a')
        ret['sample_image'] = []
        for node in nodes:
            entity = {}
            tag = node.xpath('.//img')
            entity['thumb'] = tag[0].attrib['src']
            entity['full'] = entity['thumb'].replace(ret['code']+'-', ret['code']+'jp-')
            from system.model import ModelSetting as SystemModelSetting
            entity['full'] = '%s/av_agent/api/image_proxy?url=%s' % (SystemModelSetting.get('ddns'), entity['full'])
            entity['thumb'] = '%s/av_agent/api/image_proxy?url=%s' % (SystemModelSetting.get('ddns'), entity['thumb'])
            if SystemModelSetting.get_bool('auth_use_apikey'):
                entity['full'] += '&apikey=%s' % SystemModelSetting.get('auth_apikey')
                entity['thumb'] += '&apikey=%s' % SystemModelSetting.get('auth_apikey')
            ret['sample_image'].append(entity)
        ret['result'] = 'success'
        return ret

    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
        return False



def _set_info(tree, ret, path_str, info):
    ret[info] = ''
    ret['%s_ko' % info] = ''
    try:
        tag = tree.xpath(path_str)
        if tag:
            ret[info] = tag[0].text_content().strip()
            if info == 'studio':
                if ret[info] in _studio:
                    ret['studio_ko'] = _studio[ret['studio']]
                    return ret
            ret['%s_ko' % info] = SystemLogicTrans.trans(ret[info])
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
        
    return ret


def get_actor_info(entity, retry=True):
    try:
        from . import Vars
        url = 'https://hentaku.co/starsearch.php'
        data = {'name' : entity['name']}
        page = _session.post(url, headers=_headers, data=data)
        page.encoding = 'utf-8'
        data = page.text
        data = '<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">' + data
        tree = html.fromstring(data)
        nodes = tree.xpath('//img')
        if nodes:
            entity['img'] = nodes[0].attrib['src'].strip()
            from system.model import ModelSetting as SystemModelSetting
            entity['img'] = '%s/av_agent/api/image_proxy?url=%s' % (SystemModelSetting.get('ddns'), entity['img'])
            if SystemModelSetting.get_bool('auth_use_apikey'):
                entity['img'] += '&apikey=%s' % SystemModelSetting.get('auth_apikey')

            nodes = tree.xpath('//div[@class="avstar_info_b"]')
            tmps = nodes[0].text_content().split('/')
            entity['name_kor'] = tmps[0].strip()
            entity['name_eng'] = tmps[1].strip()
        else:
            entity['img'] = 'xxxx'
            entity['name_kor'] = ''
            entity['name_eng'] = ''
        return entity
    except ValueError:
        # 2020-06-01
        # 단시간에 많은 요청시시 Error발생
        if retry:
            logger.debug(u'단시간 많은 요청으로 재요청')
            time.sleep(1)
            return get_actor_info(entity, retry=False)
        else:
            logger.debug(u'잠시후 다시 요청')
            entity['img'] = 'xxxx'
            entity['name_kor'] = ''
            entity['name_eng'] = ''
            return entity

    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())



###############################
# JAVDB
###############################

    
def javdb_search(keyword, do_trans=True, retry=0):
    try:
        from . import Vars
        keyword = keyword.strip().replace(' ', '-')
        #if content_type != 'censored':
        logger.debug('javdb keyword:%s', keyword)
        keyword = _javdb_prefer_keyword(keyword)
        logger.debug('javdb prefer keyword:%s', keyword)
        logger.debug('Keyword :%s', keyword)
        url = 'https://javdb.com/videos/search_autocomplete.json?q=%s' % keyword
        logger.debug('url : %s', url)
        page = _session.get(url, headers=_headers, proxies=Vars.proxies)
        #logger.debug(page.text)
        try:
            data = page.json()
        except ValueError:
            # 많은요청시 발생
            if retry < 5:
                logger.debug('ValueError... wait:%s', retry)
                time.sleep(retry+1)
                return javdb_search(keyword, do_trans=do_trans, retry=retry+1)
            else:
                logger.debug('ValueError Critical!!!')
                logger.debug('ValueError Critical!!!')
                return

        ret = []
        score = 60
        find_correct = False
        for item in data:
            try:
                
                entity = {'meta':'javdb'}
                entity['id'] = item['uid']
                entity['id_show'] = item['number']
                entity['title'] = item['title']
                tmp = entity['title'].replace('[%s]' % entity['id_show'], '').strip()
                entity['title_ko'] = SystemLogicTrans.trans(tmp) if do_trans else tmp
                entity['poster'] = item['cover_url']
                if entity['poster'].startswith('//'):
                    entity['poster'] = 'https:' + entity['poster']
                
                logger.debug('javdb search entity[id_show]:[%s] keyword:[%s]', entity['id_show'], keyword)
                if entity['id_show'] is None or keyword is None:
                    continue
                if entity['id_show'].upper().replace('-', ' ').replace('_', ' ') == keyword.upper().replace('-', ' ').replace('_', ' '):
                    entity['score'] = 100
                    find_correct = True
                else:
                    if find_correct:
                        break
                    entity['score'] = score
                    score += -5 
                logger.debug('entity[score] : %s', entity['score'])
                ret.append(entity)
            except Exception as exception: 
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
        ret = sorted(ret, key=lambda k: k['score'], reverse=True) 
        return ret

    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())



def javdb_update(arg, retry=0):
    try:
        from . import Vars
        url = 'https://javdb.com/v/%s' % arg
        page = _session.get(url, headers=_headers, proxies=Vars.proxies)
        data = page.text
        data = '<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">' + data
        tree = html.fromstring(data)
        #logger.debug(data)
        ret = {}
        
        insert_code = ''
        # 샘플 이미지 변경해야함 
        DIV_INDEX = 3
        DIV_BASE = '/html/body/section/div/div[%s]/div'
        javdb_base_18 = DIV_BASE % DIV_INDEX
        #base = javdb_base_18 + '/div[2]/nav'
        base = '//nav[@class="panel video-panel-info"]/div'
        #base_full = javdb_base_18 + '/div[1]/a/img'
        base_full = '//div[@class="column column-video-cover"]/a/img'
        #SAMPLE_TAG = DIV_BASE % (DIV_INDEX+1) + '/article/div/div'
        SAMPLE_TAG = '//div[@class="tile-images preview-images"]'
        

        #tag = tree.xpath('{base}/div[1]/span[2]'.format(base=base))[0]
        ret['code'] = ''
        ret['date'] = ''
        ret['running_time'] = ''
        ret['director'] = ''
        ret['director_ko'] = ''
        ret['studio'] = ''
        ret['studio_ko'] = ''
        ret['label'] = ''
        ret['label_ko'] = ''
        ret['series'] = ''
        ret['series_ko'] = ''
        ret['genre'] = []
        ret['performer'] = []

        # 2020-03-28 span 태그 2개 에서 strong , span 으로
        #tags = tree.xpath('{base}/div'.format(base=base))
        # 2020-10-30
        tags = tree.xpath(base)
        # 2020-06-01 마찬가지로 여기도 단시간에 많은 요청시 문제발생
        logger.debug('tags :%s', len(tags))
        if len(tags) == 0: #에러
            if retry < 5:
                logger.debug('JAVDB UPDATE RETRY : %s', arg)
                return javdb_update(arg, retry+1)
            else:
                #logger.debug(data)
                logger.debug('JAVDB UPDATE CRITICAL : %s', arg)
                return
        
        for tag in tags:
            #logger.debug(tag.text_content().strip())
            #tmp = tag.xpath('span') 
            #if tmp is None or len(tmp)<2:
            #    break
            #label = tmp[0].text_content().strip()
            #value = tmp[1].text_content().strip()
            if not tag.xpath('strong') or  not tag.xpath('span'):
                break
            label = tag.xpath('strong')[0].text_content().strip()
            value = tag.xpath('span')[0].text_content().strip()

            if label == '番號:':
                ret['code'] = value
            elif label == '時間:' or label == '日期:':
                ret['date'] = value.replace('-', '')
            elif label == '時長:':
                ret['running_time'] = value.split(' ')[0].strip()
            elif label == '導演:':
                if value.replace(' ', '') != 'N/A':
                    ret['director'] = value
                    ret['director_ko'] = SystemLogicTrans.trans(ret['director'])
            elif label == '片商:':
                if value.replace(' ', '') != 'N/A':
                    ret['studio'] = value
                    if ret['studio'] in _studio:
                        ret['studio_ko'] = _studio[ret['studio']]
                    elif ret['studio'] == 'カリビアンコム':
                        ret['studio_ko'] = insert_code = 'Carib'
                    elif ret['studio'] == 'pacopacomama':
                        ret['studio_ko'] = insert_code = 'paco'
                    elif ret['studio'] == '一本道':
                        ret['studio_ko'] = insert_code = '1pondo'
                    elif ret['studio'] == '10musume':
                        ret['studio_ko'] = insert_code = '10mu'
                    elif ret['studio'] == 'Tokyo-Hot':
                        ret['studio_ko'] = insert_code = 'Tokyo-Hot'
                    else:
                        ret['studio_ko'] = SystemLogicTrans.trans(ret['studio'])
            elif label == '發行:':
                if value.replace(' ', '') != 'N/A':
                    ret['label'] = value
                    ret['label_ko'] = SystemLogicTrans.trans(ret['label'])

            elif label == '類別:':
                for tmp in value.split(','):
                    tmp = tmp.strip()
                    if tmp in _genre:
                        ret['genre'].append(_genre[tmp])
                        continue
                    tmp = SystemLogicTrans.trans(tmp).replace(' ', '')
                    if tmp not in ['고화질', '독점전달', '세트상품', '단체작품', '기간한정세일', '기리모자', '데지모', '슬림', '미소녀', '미유', '망상족', '거유', '에로스', '작은']:
                        ret['genre'].append(tmp)
            elif label == '演員:':
                nodes = tag.xpath('.//a')
                for node in nodes:
                    entity = {}
                    entity['id'] = ''
                    entity['name'] = node.text_content().strip()
                    entity = get_actor_info(entity)
                    ret['performer'].append(entity)

            """
            elif label == '类别:':
                nodes = tmp[1].xpath('.//a')
                for node in nodes:
                    tmp = node.text_content().strip()
                    if tmp in _genre:
                        ret['genre'].append(_genre[tmp])
                        continue
                
                    tmp = SystemLogicTrans.trans(tmp).replace(' ', '')
                    if tmp not in ['고화질', '독점전달', '세트상품', '단체작품', '기간한정세일', '기리모자', '데지모', '슬림', '미소녀', '미유', '망상족', '거유', '에로스', '작은']:
                        ret['genre'].append(tmp)
            """
            
        tag = tree.xpath('/html/body/section/div/h2/strong')[0]
        ret['title'] = tag.text_content().replace(ret['code'], '').strip()
        ret['title_ko'] = SystemLogicTrans.trans(ret['title'])
        ret['summary'] = ret['title']
        ret['summary_ko'] = ret['title_ko']

        tag = tree.xpath(base_full)[0]
        ret['poster_full'] = tag.attrib['src']
        from system.model import ModelSetting as SystemModelSetting
        ret['poster_full'] = '%s/av_agent/api/image_proxy?url=%s' % (SystemModelSetting.get('ddns'), ret['poster_full'])
        if SystemModelSetting.get_bool('auth_use_apikey'):
            ret['poster_full'] += '&apikey=%s' % SystemModelSetting.get('auth_apikey')


        search_data = javdb_search(ret['code'])
        logger.debug(search_data)
        target = None
        for s in search_data:
            if s['score'] == 100:
                target = s
                break

        #if len(search_data) == 1 and search_data[0]['score'] == 100:
        if target is not None:
            ret['poster'] = target['poster']
            from system.model import ModelSetting as SystemModelSetting
            ret['poster'] = '%s/av_agent/api/image?url=%s' % (SystemModelSetting.get('ddns'), ret['poster'])
            if SystemModelSetting.get_bool('auth_use_apikey'):
                ret['poster'] += '&apikey=%s' % SystemModelSetting.get('auth_apikey')
        else:
            ret['poster'] =  ret['poster_full']
        
        ret['sample_image'] = []
        try:
            tag = tree.xpath(SAMPLE_TAG)
            if tag:
                tag = tag[0]
                nodes = tag.xpath('.//a')
                
                for node in nodes:
                    entity = {}
                    entity['full'] = node.attrib['href']
                    #logger.debug(entity['full'])
                    tag = node.xpath('.//img')[0]
                    entity['thumb'] = tag.attrib['src']
                    from system.model import ModelSetting as SystemModelSetting
                    entity['full'] = '%s/av_agent/api/image_proxy?url=%s' % (SystemModelSetting.get('ddns'), entity['full'])
                    entity['thumb'] = '%s/av_agent/api/image_proxy?url=%s' % (SystemModelSetting.get('ddns'), entity['thumb'])
                    if SystemModelSetting.get_bool('auth_use_apikey'):
                        entity['full'] += '&apikey=%s' % SystemModelSetting.get('auth_apikey')
                        entity['thumb'] += '&apikey=%s' % SystemModelSetting.get('auth_apikey')

                    ret['sample_image'].append(entity)
        except:
            pass
        if insert_code != '':
            insert_code += ' '
        ret['code_show'] = insert_code + ret['code']
        ret['release'] = ''
        match = re.compile(r'(?P<real>[a-zA-Z]+)-(?P<no>\d+)').match(ret['code'])
        if match:
            ret['release'] = match.group('real')
        if ret['release'] == '':
            ret['release'] = ret['studio_ko']

        
        ret['rating'] = '0'
        ret['result'] = 'success'
        return ret
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
        return False        



# 파일처리시에 사용
# JAVDB 검색시에 사용
# 스튜디오, 검색용 타이틀
def uncensored_filename_analyze(filename):
    try:
        #logger.debug('get_plex_filename un:%s', filename)
        original_filename = filename
        #return file
        filename = filename.lower()
        ret = None

        # 1pondo
        if filename.find('1pon') != -1:
            match = re.search('(?P<code1>\d{6}).(?P<code2>\d{3})', filename)
            if match:
                return ['1pondo', '{code1}_{code2}'.format(code1=match.group('code1'), code2=match.group('code2')) ]
            return ['1pondo', None]

        # 10musume
        if filename.find('10mu') != -1:
            match = re.search('(?P<code1>\d{6}).(?P<code2>\d{2})', filename)
            if match:
                return ['10mu', '{code1}_{code2}'.format(code1=match.group('code1'), code2=match.group('code2')) ]
            return ['10mu', None]

        # caribpr 이건 메타 검색이 안된다. carib 때문에 먼저 찾는다.
        if filename.find('caribpr') != -1:
            #match = re.search('(?P<code1>\d{6}).(?P<code2>\d{3})', filename)
            #if match:
            #    return ['caribpr', None ]
            return None

        # carib  022320-001-carib-1080p
        if filename.find('carib') != -1:
            match = re.search('(?P<code1>\d{6}).(?P<code2>\d{3})', filename)
            if match:
                return ['carib', '{code1}_{code2}'.format(code1=match.group('code1'), code2=match.group('code2')) ]
            return ['carib', None]
        
        # pacopacomama
        if filename.find('paco') != -1:
            match = re.search('(?P<code1>\d{6}).(?P<code2>\d{3})', filename)
            if match:
                return ['paco', '{code1}_{code2}'.format(code1=match.group('code1'), code2=match.group('code2')) ]
            return ['paco', None]


        # heyzo
        if filename.find('heyzo') != -1:
            #match = re.search('(?P<code2>\d{4})', filename)
            match = re.findall('(?P<code2>\d{4})', filename)
            if match:
                #return ['heyzo', 'heyzo-{code2}'.format(code2=match.group('code2')) ]
                return ['heyzo', 'heyzo-{code2}'.format(code2=match[-1]) ]
            return ['heyzo', None]

        # xxx-av
        if filename.find('xxx-av') != -1:
            match = re.search('(?P<code2>\d{5})', filename)
            if match:
                return ['xxx-av', 'xxx-av-{code2}'.format(code2=match.group('code2')) ]
            return ['xxx-av', None]


        # fc2
        if filename.find('fc2') != -1:
            match = re.search('(?P<code2>\d{6,7})', filename)
            if match:
                return ['fc2', 'fc2-{code2}'.format(code2=match.group('code2')) ]
            return ['fc2', None]


        # ccdv
        if filename.find('ccdv') != -1:
            match = re.search('(?P<code2>\d{2})', filename)
            if match:
                return ['ccdv', 'ccdv-{code2}'.format(code2=match.group('code2')) ]
            return ['ccdv', None]
        if filename.find('mmdv') != -1:
            match = re.search('(?P<code2>\d{2})', filename)
            if match:
                return ['mmdv', 'mmdv-{code2}'.format(code2=match.group('code2')) ]
            return ['mmdv', None]
        if filename.find('ssdv') != -1:
            match = re.search('(?P<code2>\d{2})', filename)
            if match:
                return ['ssdv', 'ssdv-{code2}'.format(code2=match.group('code2')) ]
            return ['ssdv', None]


        # Tokyo-Hot
        match = re.search('(?P<code2>n\d{4})', filename, re.IGNORECASE)
        if match:
            return ['tokyo-hot', '{code2}'.format(code2=match.group('code2')) ]
        #return ['tokyo-hot', None]

        #############################################
        # 메타는 없지만 분류는 가능
        # heydouga
        """
        ## nyoshin 메타 검색 안됨 tokyo-hot 때문에 먼저 오도록
        if filename.find('nyoshin') != -1:
            #match = re.search('(?P<code2>n\d{4})', filename)
            #if match:
                return ['nyoshin', None ]
            #return ['nyoshin', None]

        if filename.find('hey') != -1:
            match = re.search(r'(?P<code>\d{4}\-\d{3,5})', filename)
            if match:
                return ['heydouga', None ]

        # kb
        if filename.startswith('kb'):
            #match = re.search(r'(?P<code>\d{4})\_(?P<desc>.*?)', filename)
            #if match:
                return ['kb', None ]
            
        # c0930
        if filename.startswith('c0930'):
            #match = re.search(r'(?P<code2>\d{6})', filename)
            #if match:
                return ['c0930', None ]

        # h0930
        if filename.startswith('h0930'):
            #match = re.search(r'(?P<code>[a-zA-Z]*\d*)', filename)
            #if match:
                return ['h0930', None ]

        # h4610
        if filename.startswith('h4610'):
            #match = re.search(r'(?P<code>[a-zA-Z]*\d*)', filename)
            #if match:
                return ['h4610', None ]
        """
        return

    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def _javdb_prefer_keyword(keyword):
    try:
        tmp =  uncensored_filename_analyze(keyword)
        if tmp is not None:
            return tmp[1]

        #vixen.20.02.28.angel.emily.4k
        match = re.match(r'(?P<code>\w+\.\d{2}\.\d{2}.\d{2})\.', keyword, re.IGNORECASE)
        if match:
            return match.group('code')

        return keyword
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def test_dmm(keyword, use_discord_proxy=False):
    try:
        ret = {}
        ret['search'] = dmm_search(keyword)
        if len(ret['search']) == 1:
            ret['update'] = dmm_update(ret['search'][0]['id'], use_discord_proxy=use_discord_proxy)
        else:
            for tmp in ret['search']:
                if tmp['score'] == 100:
                    ret['update'] = dmm_update(tmp['id'], use_discord_proxy=use_discord_proxy)
                    break
        return ret
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def test_javdb(keyword):
    try:
        ret = {}
        ret['search'] = javdb_search(keyword)
        if len(ret['search']) == 1:
            ret['update'] = javdb_update(ret['search'][0]['id'])
        else:
            for tmp in ret['search']:
                if tmp['score'] == 100:
                    ret['update'] = javdb_update(tmp['id'])
                    break
        return ret
    except Exception as exception: 
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def is_uncensored(filename):
    if filename.startswith('nyoshin'):
        #match = re.search('(?P<code2>n\d{4})', filename)
        #if match:
            return ['nyoshin', None ]
        #return ['nyoshin', None]

    if filename.startswith('heydouga'):
        match = re.search(r'(?P<code>\d{4}\-\d{3,5})', filename)
        if match:
            return ['heydouga', None ]

    # kb
    if filename.startswith('kb'):
        #match = re.search(r'(?P<code>\d{4})\_(?P<desc>.*?)', filename)
        #if match:
            return ['kb', None ]
        
    # c0930
    if filename.startswith('c0930'):
        #match = re.search(r'(?P<code2>\d{6})', filename)
        #if match:
            return ['c0930', None ]

    # h0930
    if filename.startswith('h0930'):
        #match = re.search(r'(?P<code>[a-zA-Z]*\d*)', filename)
        #if match:
            return ['h0930', None ]

    # h4610
    if filename.startswith('h4610'):
        #match = re.search(r'(?P<code>[a-zA-Z]*\d*)', filename)
        #if match:
            return ['h4610', None ]
    