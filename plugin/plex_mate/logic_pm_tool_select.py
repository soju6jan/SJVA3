# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, re, json, threading, time, shutil, platform
from datetime import datetime
# third-party
import requests, xmltodict
from flask import request, render_template, jsonify, redirect
# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from plugin import default_route_socketio_sub, LogicSubModuleBase
from tool_base import ToolBaseFile, d, ToolSubprocess, ToolShutil
# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting


from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
from .plex_bin_scanner import PlexBinaryScanner
#########################################################


class LogicPMDBToolSelect(LogicSubModuleBase):
    preset = [
        ['템플릿 : 키워드 입력 필요', ''],
        ['제목 포함 검색', "(metadata_items.title LIKE '% __ %' AND metadata_type BETWEEN 1 and 4)"],
        ['제목 일치 검색', "(metadata_items.title = ' __ ' AND metadata_type BETWEEN 1 and 2)"],
        ['메타제공 사이트 일치 검색', "(metadata_items.guid LIKE '%sjva_agent://__%' AND metadata_type BETWEEN 1 and 2)"],
        ['메타제공 사이트 불일치 검색', "(metadata_items.guid NOT LIKE '%sjva_agent://__%' AND metadata_type BETWEEN 1 and 2)"],
        ['휴지통', "(metadata_items.deleted_at != '')"],
        ['-------------', ''],
        ['제목 정렬시 한글 초성이 아닌 것들', "(metadata_type in (1,2,8,9) AND substr(metadata_items.title_sort, 1, 1) >= '가' and substr(metadata_items.title_sort, 1, 1) <= '힣')"],
        ['메타 없는 것', 'metadata_items.guid LIKE "local://%"'],
        ['미분석', '(metadata_type BETWEEN 1 and 4 AND width is null)'],
        ['불일치 상태', "(metadata_type BETWEEN 1 and 4 AND guid LIKE 'com.plexapp.agents.none%')"],
        ['Poster가 없거나, media이거나, upload 인 경우', "(metadata_type BETWEEN 1 and 4 AND (user_thumb_url == '' OR user_thumb_url LIKE 'media%' OR user_thumb_url LIKE 'upload%'))"],
        ['Art가 없거나, media이거나, upload 인 경우', "(metadata_type BETWEEN 1 and 4 AND (user_art_url == '' OR user_art_url LIKE 'media%' OR user_art_url LIKE 'upload%'))"],
    ]

    def __init__(self, P, parent, name):
        super(LogicPMDBToolSelect, self).__init__(P, parent, name)
        self.db_default = {
            f'{self.parent.name}_{self.name}_db_version' : '1',
            f'{self.parent.name}_{self.name}_query' : '',
        }
        


    def process_ajax(self, sub, req):
        try:
            ret = {'ret':'success'}
            if sub == 'command':
                command = req.form['command']
                logger.error(f"sub : {sub}  /  command : {command}")
                if command == 'select':
                    ModelSetting.set(f'{self.parent.name}_{self.name}_query', req.form['arg1'])
                    ret['select'] = PlexDBHandle.tool_select(req.form['arg1'])
                elif command == 'refresh_web':
                    PlexWebHandle.refresh_by_id(req.form['arg1'])
                    ret['msg'] = '명령을 전송하였습니다.'
                elif command == 'refresh_bin':
                    PlexBinaryScanner.scan_refresh2(req.form['arg1'], os.path.dirname(req.form['arg2']))
                    ret['msg'] = '완료'
                elif command == 'analyze_web':
                    PlexWebHandle.analyze_by_id(req.form['arg1'])
                    ret['msg'] = '명령을 전송하였습니다.'
                elif command == 'analyze_bin':
                    PlexBinaryScanner.analyze(req.form['arg1'], metadata_item_id=req.form['arg2'])
                    ret['msg'] = '완료'
                elif command == 'remove_metadata':
                    folder_path = os.path.join(
                        ModelSetting.get('base_path_metadata'),
                        'Movies' if req.form['arg1'] == '1' else 'TV Shows',
                        req.form['arg2'][0],
                        f"{req.form['arg2'][1:]}.bundle"
                    )
                    if os.path.exists(folder_path):
                        if ToolBaseFile.rmtree(folder_path):
                            ret['msg'] = '삭제하였습니다.'
                        else:
                            ret['ret'] = 'warning'
                            ret['msg'] = '삭제 실패'
                    else:
                        ret['ret'] = 'warning'
                        ret['msg'] = f'{folder_path} 없음'
            elif sub == 'get_preset':
                ret['preset'] = self.preset
            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
  


    #########################################################
