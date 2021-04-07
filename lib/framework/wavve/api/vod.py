# -*- coding: utf-8 -*-
#from common.decorator import try_except
import traceback

import json
from framework.wavve.api import session, get_baseparameter, config, logger
from framework.util import Util
from framework import py_urllib


#https://apis.pooq.co.kr/cf/vod/newcontents?WeekDay=all&broadcastid=192669&came=broadcast&contenttype=program&genre=all&limit=20&offset=0&orderby=new&uiparent=FN0&uirank=0&uitype=VN1&apikey=E5F3E0D30947AA5440556471321BB6D9&credential=none&device=pc&drm=wm&partner=pooq&pooqzone=none&region=kor&targetage=auto

"""
'base_parameter' : {
    'apikey' : 'E5F3E0D30947AA5440556471321BB6D9',
    'credential' : 'none',
    'device' : 'pc',
    'partner' : 'pooq',
    'pooqzone' : 'none',
    'region' : 'kor',
    'drm' : 'wm',
    'targetage' : 'auto'
},
"""


def vod_newcontents(page=1, limit=20, genre='all'):
    try:
        page = int(page) if type(page) != int else page
        param = get_baseparameter()
        param['genre'] = 'all'
        param['channel'] = 'all'
        param['type'] = 'all'
        param['weekday'] = 'all'
        param['offset'] = (page-1)*limit
        param['limit'] = limit
        param['orderby'] = 'new' # 최신순 = new 과거순 = old
        url = "%s/vod/newcontents?%s" % (config['base_url'], py_urllib.urlencode(param))
        response = session.get(url, headers=config['headers'])
        data = response.json()
        #logger.debug(url)
        if response.status_code == 200:
            return data
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

# newcontents, popularcontents
# order viewtime
def vod_contents(page=1, limit=20, content_type='newcontents', genre='all', orderby='new', is_cf=False):
    try:
        page = int(page) if type(page) != int else page
        param = get_baseparameter()
        param['genre'] = genre
        param['channel'] = 'all'
        param['type'] = 'all'
        param['weekday'] = 'all'
        param['offset'] = (page-1)*limit
        param['limit'] = limit
        param['orderby'] = orderby # 최신순 = new 과거순 = old
        if is_cf:
            url = "%s/cf/vod/%s?%s" % (config['base_url'], content_type, py_urllib.urlencode(param))
        else:
            url = "%s/vod/%s?%s" % (config['base_url'], content_type, py_urllib.urlencode(param))
        response = session.get(url, headers=config['headers'])
        data = response.json()
        #logger.debug(url)
        if response.status_code == 200:
            return data
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


#http://apis.wavve.com/vod/allprograms?genre=09&orderby=new&contenttype=program&subgenre=vsgm09001&WeekDay=all&offset=0&limit=20
def vod_allprograms(page=1, limit=20, contenttype='program', genre='all', subgenre=None, orderby='new', is_cf=False):
    try:
        page = int(page) if type(page) != int else page
        param = get_baseparameter()
        param['genre'] = genre
        param['contenttype'] = contenttype

        param['type'] = 'all'
        param['weekday'] = 'all'
        param['offset'] = (page-1)*limit
        param['limit'] = limit
        param['orderby'] = orderby # 최신순 = new 과거순 = old
        if subgenre is not None:
            param['subgenre'] = subgenre
        if is_cf:
            url = "%s/cf/vod/allprograms?%s" % (config['base_url'], py_urllib.urlencode(param))
        else:
            url = "%s/vod/allprograms?%s" % (config['base_url'], py_urllib.urlencode(param))
        response = session.get(url, headers=config['headers'])
        data = response.json()
        #logger.debug(url)
        if response.status_code == 200:
            return data
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def vod_contents_contentid(contentid):
    try:
        param = get_baseparameter()
        #param['ishevc'] = 'all'
        url = "%s/vod/contents/%s?%s" % (config['base_url'], contentid, py_urllib.urlencode(param))
        response = session.get(url, headers=config['headers'])

        #logger.debug(url)
        data = response.json()
        #logger.debug(data)
        if response.status_code == 200:
            return data
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())


def vod_programs_programid(programid):
    try:
        param = get_baseparameter()
        #param['ishevc'] = 'all'
        url = "%s/vod/programs/%s?%s" % (config['base_url'], programid, py_urllib.urlencode(param))
        response = session.get(url, headers=config['headers'])

        #logger.debug(url)
        data = response.json()
        #logger.debug(data)
        if response.status_code == 200:
            return data
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
                logger.debug(url)
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())

def vod_program_contents_programid(programid, page=1, limit=20):
    try:
        page = int(page) if type(page) != int else page
        param = get_baseparameter()
        param['offset'] = (page-1)*limit
        param['limit'] = limit
        param['orderby'] = 'new'
        url = "%s/vod/programs-contents/%s?%s" % (config['base_url'], programid, py_urllib.urlencode(param))
        #logger.debug(url)
        response = session.get(url, headers=config['headers'])
        data = response.json()
        if response.status_code == 200:
            return data
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())



def get_filename(data, quality):
    try:
        if 'movieid' in data:
            title = Util.change_text_for_use_filename(data['title'])
            releasedate = data['releasedate'][:4]
            ret = "%s.%s.%s-SW.mp4" % (title, releasedate, quality)
            return ret
        else:
            title = Util.change_text_for_use_filename(data['programtitle'])
            tmp = data["episodenumber"]
            episodeno = ''
            if len(tmp):
                if tmp == u'특집':
                    episodeno = u'.특집'
                else:
                    tmps = tmp.split('-')
                    if len(tmps[0]) < 6:
                        try:
                            is_number = int(tmps[0])
                            episodeno = '.E0%s' % tmps[0] if len(tmps[0]) == 1 else '.E%s' % tmps[0]
                        except:
                            episodeno = u'.%s' % tmps[0]

            airdate = data["releasedate"].replace('-', '')[2:]
            release = "SW"
            if data['type'] == 'onair':
                release = 'SWQ'
            
            ret = "%s%s.%s.%s-%s.mp4" % (title, episodeno, airdate, quality, release)
            return ret

        if episode_data['result']['contentType'] == 'movie':
            title = episode_data["result"]["programTitle"]
            title = title.replace("<", "").replace(">", "").replace("\\", "").replace("/", "").replace(":", "").replace("*", "").replace("\"", "").replace("|", "").replace("?", "").replace("  ", " ").strip()
            currentQuality = episode_data["result"]["qualityList"]['qualityCurrent']
            qualityRes = PooqAPI.get_quality_to_res(currentQuality)
            airDate = episode_data["result"]["airDate"]
            ret = "%s.%s.%s-SP.mp4" % (title, airDate[:4], qualityRes)
            return ret
        else:
            title = episode_data["result"]["programTitle"]
            title = title.replace("<", "").replace(">", "").replace("\\", "").replace("/", "").replace(":", "").replace("*", "").replace("\"", "").replace("|", "").replace("?", "").replace("  ", " ").strip()
            episodeno = episode_data["result"]["episodeNo"]
            airdate = episode_data["result"]["airDate"].replace('-', '')[2:]

            currentQuality = episode_data["result"]["qualityList"]['qualityCurrent']
            qualityRes = PooqAPI.get_quality_to_res(currentQuality)
            #logger.debug('currentQuality : %s %s', currentQuality, qualityRes)
            release = "SP"
            if episode_data["result"]["contentType"] == 'qvod':
                release = 'SPQ'
        
            if len(episodeno):
                if len(episodeno) == 1:
                    episodeno = "0" + episodeno
                if episodeno == "특집":
                    ret = "%s.%s.%s.%s-%s.mp4" % (title, episodeno, airdate, qualityRes, release)
                else:
                    ret = "%s.E%s.%s.%s-%s.mp4" % (title, episodeno, airdate, qualityRes, release)
            else:
                ret = "%s.%s.%s-%s.mp4" % (title, airdate, qualityRes, release)
            #logger.debug('filename : %s', ret)
            return ret
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc()) 












def movie_contents_detail(movie_id):
    """영화 상세 정보"""
    #https://apis.pooq.co.kr/cf/movie/contents/MV_CA01_DY0000011394?apikey=E5F3E0D30947AA5440556471321BB6D9
    try:
        param = get_baseparameter()
        url = "%s/movie/contents/%s?%s" % (config['base_url'], movie_id, py_urllib.urlencode(param))
        response = session.get(url, headers=config['headers'])
        data = response.json()
        if response.status_code == 200:
            return data
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())
    

#https://apis.pooq.co.kr/vod/programs/M_1002345100000100000?credential=none&apikey=E5F3E0D30947AA5440556471321BB6D9&region=kor&targetage=auto&drm=wm&pooqzone=none&device=pc&partner=pooq    



#https://apis.wavve.com/search/instance/keywords?isplayymovie=n&keyword=%EB%AF%B8%EC%93%B0%EB%B0%B1&apikey=E5F3E0D30947AA5440556471321BB6D9&device=pc&drm=wm&partner=pooq&pooqzone=none&region=kor&targetage=all
#category=program
#apis.wavve.com/cf/search/band.js?type=program&keyword=브람스를 좋아하세요&offset=0&limit=20&orderby=score&isplayymovie=y


def search(keyword, search_type='all'):
    try:
        param = get_baseparameter()
        param['keyword'] = keyword
        url = "https://apis.wavve.com/search/instance/keywords?%s" % (py_urllib.urlencode(param))
        response = session.get(url, headers=config['headers'])
        data = response.json()
        logger.debug(url)
        if response.status_code == 200:
            if search_type == 'all':
                return data
            else:
                for item in data:
                    if item['type'] == search_type:
                        return item
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())    





def search2(keyword, type_name):
    #return search(keyword, search_type='vodkeywordlist')
    try:
        #param = get_baseparameter()
        #param['keyword'] = keyword

        url = 'https://apis.wavve.com/cf/search/band.js?type=%s&keyword=%s&offset=0&limit=20&orderby=score&isplayymovie=y&apikey=E5F3E0D30947AA5440556471321BB6D9&&device=pc&drm=wm&partner=pooq&pooqzone=none&region=kor&targetage=all' % (type_name, py_urllib.quote(str(keyword)))

        response = session.get(url, headers=config['headers'])
        data = response.json()
        #logger.debug(url)
        if response.status_code == 200:
            if 'celllist' in data['band']:
                return data['band']['celllist']
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())  


def search_tv(keyword):
    #return search(keyword, search_type='vodkeywordlist')
    try:
        return search2(keyword, 'program')
        #param = get_baseparameter()
        #param['keyword'] = keyword

        url = 'https://apis.wavve.com/cf/search/band.js?type=program&keyword=%s&offset=0&limit=20&orderby=score&isplayymovie=y&apikey=E5F3E0D30947AA5440556471321BB6D9&&device=pc&drm=wm&partner=pooq&pooqzone=none&region=kor&targetage=all' % (py_urllib.quote(str(keyword)))

        response = session.get(url, headers=config['headers'])
        data = response.json()
        #logger.debug(url)
        if response.status_code == 200:
            if 'celllist' in data['band']:
                return data['band']['celllist']
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())    

    


def search_movie(keyword):
    try:
        url = 'https://apis.wavve.com/cf/search/list.js?keyword=%s&limit=20&offset=0&orderby=score&type=movie' % (py_urllib.quote(str(keyword)))
        response = session.get(url, headers=config['headers'])
        data = response.json()
        #logger.debug(url)
        if response.status_code == 200:
            if 'celllist' in data['cell_toplist']:
                return data['cell_toplist']['celllist']
        else:
            if 'resultcode' in data:
                logger.debug(data['resultmessage'])
    except Exception as exception:
        logger.error('Exception:%s', exception)
        logger.error(traceback.format_exc())    

    
    return search2(keyword, 'all')
    #return search(keyword, search_type='moviekeywordlist')


