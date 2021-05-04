# -*- coding: utf-8 -*-
import os
import copy

MENU_MAP = [
    {
        'category' : u'토렌트',
        'name' : 'torrent',
        'type' : 'plugin',
        'position' : 'left',
        'list' : [
            {'type':'plugin', 'plugin' : 'rss2', 'name' : 'RSS2'},
            {'type':'divider'},
            {'type':'plugin', 'plugin' : 'downloader', 'name' : u'다운로드'},
            {'type':'plugin', 'plugin' : 'rss_downloader', 'name' : u'RSS 다운로드'},
            {'type':'plugin', 'plugin' : 'bot_downloader_ktv', 'name' : u'봇 다운로드 - TV'},
            {'type':'plugin', 'plugin' : 'bot_downloader_movie', 'name' : u'봇 다운로드 - 영화'},
            {'type':'plugin', 'plugin' : 'bot_downloader_av', 'name' : u'봇 다운로드 - AV'},
            {'type':'divider'},
            {'type':'plugin', 'plugin' : 'offcloud2', 'name' : u'Offcloud2'},
            {'type':'plugin', 'plugin' : 'torrent_info', 'name' : u'토렌트 정보'},
        ],
        'count' : 0,
    },
    {
        'category' : 'VOD',
        'name' : 'vod',
        'type' : 'plugin',
        'position' : 'left',
        'list' : [
            {'type':'plugin', 'plugin' : 'ffmpeg', 'name' : u'FFMPEG'},
            {'type':'divider'},
            {'type':'plugin', 'plugin' : 'wavve', 'name' : u'웨이브'},
            {'type':'plugin', 'plugin' : 'tving', 'name' : u'티빙'},
            {'type':'plugin', 'plugin' : 'nsearch', 'name' : u'검색'},
            {'type':'divider'},
            {'type':'plugin', 'plugin' : 'ani24', 'name' : u'애니24'},
            {'type':'plugin', 'plugin' : 'youtube-dl', 'name' : u'youtube-dl'},
            
        ],
        'count' : 0,
    },
    {
        'category' : u'파일처리',
        'name' : 'fileprocess',
        'type' : 'plugin',
        'position' : 'left',
        'list' : [
            {'type':'plugin', 'plugin' : 'ktv', 'name' : u'국내방송'},
            {'type':'plugin', 'plugin' : 'fileprocess_movie', 'name' : u'영화'},
            {'type':'plugin', 'plugin' : 'fileprocess_av', 'name' : u'AV'},
            {'type':'plugin', 'plugin' : 'musicProc', 'name' : u'음악'},            
            {'type':'divider'},
            {'type':'plugin', 'plugin' : 'smi2srt', 'name' : u'SMI to SRT'},
             {'type':'plugin', 'plugin' : 'synoindex', 'name' : u'Synoindex'},
        ],
        'count' : 0,
    },
    {
        'category' : 'PLEX',
        'name' : 'plex',
        'type' : 'plugin',
        'position' : 'left',
        'list' : [
            {'type':'plugin', 'plugin' : 'plex', 'name' : u'PLEX'},
            {'type':'divider'},
            {'type':'plugin', 'plugin' : 'gdrive_scan', 'name' : u'GDrive 스캔'},
            {'type':'divider'},
            {'type':'plugin', 'plugin' : 'av_agent', 'name' : u'AV Agent'},
        ],
        'count' : 0,
    },
    {
        'category' : u'TV',
        'name' : 'tv',
        'type' : 'plugin',
        'position' : 'left',
        'list' : [
            {'type':'plugin', 'plugin' : 'klive', 'name' : u'KLive'},
            {'type':'plugin', 'plugin' : 'tvheadend', 'name' : u'Tvheadend'},
            {'type':'plugin', 'plugin' : 'hdhomerun', 'name' : u'HDHomerun'},
            {'type':'divider'},
            {'type':'plugin', 'plugin' : 'epg', 'name' : u'EPG'},

        ],
        'count' : 0,
    },
    {
        'category' : u'서비스',
        'name' : 'service',
        'type' : 'plugin',
        'position' : 'left',
        'list' : [
            {'type':'plugin', 'plugin' : 'kthoom', 'name' : u'kthoom'},
            {'type':'plugin', 'plugin' : 'manamoa', 'name' : u'manamoa'},
            {'type':'plugin', 'plugin' : 'webtoon_naver', 'name' : u'webtoon_naver'},
            {'type':'plugin', 'plugin' : 'webtoon_daum', 'name' : u'webtoon_daum'},
            {'type':'divider'},
            {'type':'plugin', 'plugin' : 'podcast_rss_maker', 'name' : u'podcast_rss_maker'},
            {'type':'plugin', 'plugin' : 'gd_share_client', 'name' : u'gd_share_client'},
        ],
        'count' : 0,
    },
    {
        'category' : u'툴',
        'name' : 'tool',
        'type' : 'plugin',
        'position' : 'left',
        'list' : [
            {'type':'plugin', 'plugin' : 'rclone', 'name' : u'Rclone'},
            {'type':'plugin', 'plugin' : 'vnStat', 'name' : u'vnStat'},
            {'type':'plugin', 'plugin' : 'aria2', 'name' : u'aria2'},
            {'type':'divider'},
            {'type':'plugin', 'plugin' : 'daum_tv', 'name' : u'Daum TV'},
        ],
        'count' : 0,
    },
    {
        'category' : u'런처',
        'name' : 'launcher',
        'type' : 'plugin',
        'position' : 'left',
        'list' : [
        ],
        'count' : 0,
    },
    {
        'category' : u'Beta',
        'name' : 'beta',
        'type' : 'plugin',
        'position' : 'left',
        'list' : [
        ],
        'count' : 0,
    },
    {
        'category' : 'Custom',
        'name' : 'custom',
        'type' : 'custom',
        'position' : 'left',
        'list' : [],
        'count' : 0,
    },
    
    {
        'category' : u'링크',
        'name' : 'link',
        'type' : 'link',
        'position' : 'right',
        'list' : [
            {'type':'link', 'name':u'PLEX', 'link':'https://app.plex.tv'},
            {'type':'divider'},
            {'type':'link', 'name':u'나스당', 'link':'https://www.clien.net/service/board/cm_nas'},
            {'type':'link', 'name':u'mk802카페', 'link':'https://cafe.naver.com/mk802'},
        ],
        'count' : 0,
    },
    {
        'category' : u'시스템',
        'name' : 'system',
        'type' : 'system',
        'position' : 'right',
        'list' : [
            {'type':'plugin', 'plugin' : 'system', 'name' : u'설정'},
            #{'type':'direct', 'name' : u'설정', 'link':'/system/setting'},
            #{'type':'direct', 'name' : u'플러그인', 'link':'/system/plugin'},
            #{'type':'direct', 'name' : u'정보', 'link':'/system/information'},
            {'type':'plugin', 'plugin' : 'command', 'name' : u'Command'},
            {'type':'direct', 'name' : u'파일 매니저', 'link':'/iframe/file_manager'},
            {'type':'divider'},
            #{'type':'link', 'name' : u'FileManager', 'link':'/iframe/file_manager'},
            #{'type':'system_value', 'name' : u'FileBrowser.xyz', 'link':'url_filebrowser'},
            #{'type':'system_value', 'name' : u'Celery Monitoring', 'link':'url_celery_monitoring'},
            #{'type':'divider'},
            #{'type':'link', 'name':u'위키', 'link':'https://sjva.me/wiki/public/start'},
            #{'type':'divider'},
            {'type':'direct', 'name' : u'로그아웃', 'link':'/logout'},
            {'type':'direct', 'name' : u'재시작(업데이트)', 'link':'/system/restart'},
            {'type':'direct', 'name' : u'종료', 'link':'javascript:shutdown_confirm();'},
        ],
        'count' : 0,
    }
]

DEFINE_MENU_MAP = copy.deepcopy(MENU_MAP)

def init_menu(plugin_menus):
    global MENU_MAP
    from framework import logger

    for plugin_menu in plugin_menus:
        find = False
        for category in MENU_MAP:
            for category_child in category['list']:
                if category_child['type'] != 'plugin':
                    continue
                if category_child['plugin'] == plugin_menu['main'][0]:
                    find = True
                    category_child['name'] = plugin_menu['main'][1]
                    category_child['sub'] = plugin_menu['sub']
                    category_child['sub2'] = plugin_menu['sub2'] if 'sub2' in plugin_menu else None
                    category_child['exist'] = True
                    category['count'] += 1
                    break
            if find:
                break
            else:
                if 'category' in plugin_menu and plugin_menu['category'] == category['name']:
                    cc = {}
                    cc['type'] = 'plugin'
                    cc['plugin'] = plugin_menu['main'][0]
                    cc['name'] = plugin_menu['main'][1]
                    cc['sub'] = plugin_menu['sub']
                    cc['sub2'] = plugin_menu['sub2'] if 'sub2' in plugin_menu else None
                    cc['exist'] = True
                    category['count'] += 1
                    category['list'].append(cc)
                    find = True



        if find:
            continue
        else:
            # 카테고리를 발견하지 못하였다면..
            c = MENU_MAP[9]
            cc = {}
            cc['type'] = 'plugin'
            cc['plugin'] = plugin_menu['main'][0]
            cc['name'] = plugin_menu['main'][1]
            cc['sub'] = plugin_menu['sub']
            cc['sub2'] = plugin_menu['sub2'] if 'sub2' in plugin_menu else None
            cc['exist'] = True
            c['count'] += 1
            c['list'].append(cc)
    
    
    tmp = copy.deepcopy(MENU_MAP)
    MENU_MAP = []
    for category in tmp:
        if category['type'] in ['link']:
            MENU_MAP.append(category) 
        elif category['type'] in ['system']:
            from system.model import ModelSetting as SystemModelSetting
            for t in category['list']:
                if t['type'] == 'system_value':
                    t['type'] = 'link'
                    t['link'] = SystemModelSetting.get(t['link'])
            MENU_MAP.append(category) 
        else:
            if category['count'] > 0:
                MENU_MAP.append(category) 

    for category in MENU_MAP:
        if category['category'] in ['system', 'link', 'custom']:
            continue
        flag_custom = False
        total_plugin_count  = 0
        exist_plugin_count  = 0
        for category_child in category['list']:
            total_plugin_count += 1
            if category_child['type'] == 'plugin':
                if 'exist' not in category_child or category_child['exist'] == False:
                    flag_custom = True
                else:
                    exist_plugin_count += 1
        if exist_plugin_count == 0:
            #올수없다
            
            continue
         
        if flag_custom:
            tmp = copy.deepcopy(category['list'])
            category['list'] = []
            for category_child in tmp:
                if category_child['type'] != 'plugin':
                    category['list'].append(category_child)
                if 'exist' in category_child and category_child['exist'] == True:
                    category['list'].append(category_child)
    
    try:
        import flaskfilemanager
    except:
        #del MENU_MAP[-1]['list'][2]
        try:
            index = -1
            for idx, item in enumerate(MENU_MAP[-1]['list']):
                if 'name' in item and item['link'].find('file_manager') != -1:
                    index = idx
                    break
            if index != -1:
                del MENU_MAP[-1]['list'][index]
        except:
            pass
    

    try:
        ## 선 제거
        for category in MENU_MAP:
            new_category = []
            flag = -1
            first = False
            for idx, item in enumerate(category['list']):
                if (idx == 0 or idx == len(category['list']) -1) and item['type'] == 'divider':
                    continue
                if first == False and item['type'] == 'divider':
                    continue
                if item['type'] == 'divider':
                    if flag == 1:
                        continue
                    else:
                        flag = 1
                else:
                    first = True
                    flag = 0
                new_category.append(item)
            if new_category[-1]['type'] == 'divider':
                new_category = new_category[:-1]
            category['list'] = new_category
    except:
        pass
      

def get_menu_map():
    global MENU_MAP
    return MENU_MAP

def get_plugin_menu(plugin_name):
    global MENU_MAP
    for category in MENU_MAP:
        for category_child in category['list']:
            if category_child['type'] != 'plugin':
                    continue
            if category_child['plugin'] == plugin_name:
                return category_child

