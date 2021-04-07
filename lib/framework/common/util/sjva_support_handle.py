# -*- coding: utf-8 -*-
import os
import io
import traceback

from framework import app, logger, path_data

git_name = 'sjva_support'
class SJVASupportControl:
    @staticmethod
    def epg_upload():
        try:
            logger.debug('vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv')
            from epg.model import ModelEpgMakerSetting
            data = {'updated' : ModelEpgMakerSetting.get('updated')}
            from framework.util import Util
            Util.save_from_dict_to_json(data, os.path.join(path_data, 'sjva_support', 'epg_updated.json'))
            
            epg_sh = os.path.join(path_data, 'sjva_support', 'epg_commit.sh')
            os.system(epg_sh)
            #os.remove()
            return True
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        return False

    @staticmethod
    def epg_refresh():
        # epg.db가 없으면 받는다
        # 파일이 있다면, epg.db에 있는 시간과, sjva_support에 있는 생성시간을 비교해서 다르면 받고 "refresh"를 리턴한다
        # 같다면 "recent" 를 리턴한다.
        try:
            logger.debug('epg_refresh.....')
            if app.config['config']['server']:
                return 'server'
            from framework.common.util import download
            epg_db_filepath = os.path.join(path_data, 'db', 'epg.db')
            try:
                from epg import ModelEpgMakerSetting
            except:
                return 'no_epg_plugin'

            if os.path.exists(epg_db_filepath):
                import requests
                url = 'https://raw.githubusercontent.com/soju6jan/sjva_support/master/epg_updated.json'
                data = requests.get(url).json()
                if data['updated'] == ModelEpgMakerSetting.get('updated'):
                    return 'recent'

            url = 'https://raw.githubusercontent.com/soju6jan/sjva_support/master/epg.db'
            tmp = os.path.join(path_data, 'db', '_epg.db')
            download(url, tmp)
            if os.path.exists(epg_db_filepath):
                os.remove(epg_db_filepath)
            import shutil
            if os.path.exists(tmp):
                shutil.move(tmp, epg_db_filepath)
                logger.debug('Download epg.db.....')
            return 'refresh'
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            