# python
import os, sys, traceback, re, json, threading, time, shutil, fnmatch, fnmatch, sqlite3
from .plugin import P, d, logger, package_name, ModelSetting, app, celery
from .logic_pm_base import LogicPMBase
from .plex_db import PlexDBHandle, dict_factory
from .plex_web import PlexWebHandle
from .plex_bin_scanner import PlexBinaryScanner


subtitle_exts  = ['*.srt', '*.smi', '*.ass', '*.ssa']
SUBTITLE_EXTS  = r'|'.join([fnmatch.translate(x) for x in subtitle_exts])


class Task(object):
    


    @staticmethod
    @celery.task(bind=True)
    def start(self, command, section_id, section_location):
        #config = LogicPMBase.load_config()

        #logger.debug('22222222222222')
        logger.error(section_location)

        #return
        db_file = ModelSetting.get('base_path_db')
        con = sqlite3.connect(db_file)
        cur = con.cursor()
        #ce = con.execute('SELECT * FROM metadata_items WHERE metadata_type = 1 AND library_section_id = ? ORDER BY title', (section_id,))
        #ce = con.execute('SELECT * FROM metadata_items WHERE metadata_type = 1 AND library_section_id = ? AND user_thumb_url NOT LIKE "upload%" AND (user_thumb_url NOT LIKE "http%" OR refreshed_at is NULL) ORDER BY title', (section_id,))

        logger.error(section_id)
        
        locations = PlexDBHandle.section_location(library_id=section_id)
        if section_location != 'all':
            for tmp in locations:
                if tmp['root_path'] == section_location:
                    break
            locations = [tmp]

        logger.error(d(locations))

        status = {'is_working':'run', 'subtitle_count':0, 
            'subtitle_exist_in_meta_count':0, # 자막이 db에서 검색됨.
            'not_subtitle_exist_in_meta_count':0, # 자막이 db에서 검색되지 않음
            
            'videofile_exist_count':0,  #자막에 맞는 비디오 파일 있음
            'not_videofile_exist_count':0, # 자막만 있고 자막 파일명에 맞는 비디오 없음
            
            'videofile_exist_not_in_meta_count':0, # 자막에 맞는 비디오 파일이 메타에 없음. 스캔필요
            'videofile_exist_in_meta_count':0, #자막에 맞는 비디오 파일이 메타에 이미 있음. 메타새로고침 필요
            'smi_count':0, 
            'smi2srt_count':0, 
            'meta_refresh_show_metadata_item_id': None,
            'meta_refresh_show_metadata_item_title': None,
            'meta_refresh_show_count':0,
        }

        smi2srt = ModelSetting.get_bool('subtitle_use_smi_to_srt')
        
        for location in locations:
            section_type = 'movie' if location['section_type'] == 1 else 'show'
            root = location['root_path']
            #root = '/mnt/gds/외국TV/외국/0Z/CSI 마이애미 (2002) [CSI Miami]'

            for base, dirs, files in os.walk(root):
                ignore = False
                for rx in IGNORE_DIRS:
                    if re.match(rx, os.path.basename(base), re.IGNORECASE):
                        #logger.debug(f"IGNORE : {base}")
                        ignore = True
                        break
                if ignore:
                    continue

                files = [f for f in files if re.match(SUBTITLE_EXTS, f)]
                #process_base = False
                for fname in files:
                    if ModelSetting.get_bool('subtitle_task_stop_flag'):
                        return 'stop'
                    try:
                        status['subtitle_count'] += 1
                        data = {'status':status, 'need_smi2srt': False, 'section_type':section_type, 'dir':base, 'filename':fname, 'subtitle_filepath':os.path.join(base, fname), 'ret':{}, 'meta_subtitle':{}, 'meta_videofile':{}}
                        if os.path.splitext(fname)[-1].lower() == '.smi':
                            status['smi_count'] += 1
                            if smi2srt:
                                data['need_smi2srt'] = True

                        #logger.debug(data['subtitle_filepath'])
                        tmp = f"file://{data['subtitle_filepath'].replace('%', '%25').replace(' ', '%20')}"

                        #tmp = 'file:///mnt/gds/외국TV/다큐/펭귄%20타운%20(2021)%20[Penguin%20Town]%'

                        ce = con.execute(QUERY, (tmp,))
                        ce.row_factory = dict_factory
                        rows = ce.fetchall()

                        if len(rows) > 0:
                            status['subtitle_exist_in_meta_count'] += 1
                            data['ret']['find_meta'] = True
                            data['meta_subtitle']['video_file'] = rows[0]['file']
                            if section_type == 'movie':
                                data['meta_subtitle']['title'] = rows[0]['title']
                                data['meta_subtitle']['metadata_items_id'] = rows[0]['metadata_items_id']
                            elif section_type == 'show':
                                Task.get_show_meda(con, data['meta_subtitle'], rows[0])

                            if data['need_smi2srt']:
                                Task.smi2srt(data)
                                if section_type == 'movie':
                                    logger.warning(f"영화 smi2srt 메타 새로고침1 : {rows[0]['title']}")
                                    PlexWebHandle.refresh_by_id(rows[0]['metadata_items_id'])
                                elif section_type == 'show':
                                    Task.meta_refresh_show(data, data['meta_subtitle']['show_metadata_items_id'], data['meta_subtitle']['show_title'])
                            continue

                        logger.debug(f"==> 자막 DB에 없음 : {tmp}")

                        status['not_subtitle_exist_in_meta_count'] += 1
                        data['ret']['find_meta'] = False

                        data['ret']['find_video'],  data['ret']['find_videofilename'] = Task.find_video(base, fname)
                        logger.warning(f"비디오 파일 탐색 결과 : {data['ret']['find_video']}")

                        if data['ret']['find_video']:
                            if data['need_smi2srt']:
                                Task.smi2srt(data)
                            status['videofile_exist_count'] +=1
                            ce = con.execute(QUERY_VIDEO, (os.path.join(base, data['ret']['find_videofilename']),))
                            ce.row_factory = dict_factory
                            rows = ce.fetchall()
                            logger.error(rows)
                            
                            if len(rows) == 0:
                                # 비디오 파일이 없다면 스캔
                                status['videofile_exist_not_in_meta_count'] += 1
                                data['ret']['meta_by_videofile'] = False
                                if section_type == 'movie':
                                    logger.warning(f'영화 스캔 : {base}')
                                    PlexBinaryScanner.scan_refresh2(section_id, base)
                                elif section_type == 'show':
                                    # 쇼는 쇼폴더에서 스캔해야한다.
                                    tmp = base.replace(root, '')
                                    tmps = tmp.split(os.sep)  # tmps[0] == ''
                                    if len(tmps) > 1:
                                        logger.warning(f'쇼 스캔 : {base} {os.path.join(root, tmps[1])}')
                                        PlexBinaryScanner.scan_refresh2(section_id, os.path.join(root, tmps[1]))
                                ##process_base = True
                                #return
                            else:
                                status['videofile_exist_in_meta_count'] += 1
                                data['ret']['meta_by_videofile'] = True
                                # 비디오 파일이 이미 있다면 메타새로고침
                                if section_type == 'movie':
                                    data['meta_videofile']['title'] = rows[0]['title']
                                    data['meta_videofile']['metadata_items_id'] = rows[0]['metadata_items_id']
                                    logger.warning(f"영화 메타 새로고침2 : {rows[0]['title']}")
                                    PlexWebHandle.refresh_by_id(rows[0]['metadata_items_id'])
                                elif section_type == 'show':
                                    Task.get_show_meda(con, data['meta_videofile'], rows[0], is_video=True)
                                   
                                    Task.meta_refresh_show(data, data['meta_videofile']['show_metadata_items_id'], data['meta_videofile']['show_title'])
                                    #
                                    try:
                                        if data['meta_videofile']['episode_subtitle'][0]['sub'] != '':
                                            PlexWebHandle.refresh_by_id(rows[0]['metadata_items_id'])
                                            logger.debug(f"에피소드 메타새로고침 : {rows[0]['metadata_items_id']}")
                                    except Exception as e:
                                        #logger.error(f'Exception:{str(e)}')
                                        #logger.error(traceback.format_exc())
                                        pass
                                    
                                #return 'stop'
                                #process_base = True
                                #return
                                #break
                        else:
                            status['not_videofile_exist_count'] +=1
                            #return
                    except Exception as e:
                        logger.error(f'Exception:{str(e)}')
                        logger.error(traceback.format_exc())
                        #logger.error(show['title'])
                    finally:
                        #logger.debug(d(data))
                        if app.config['config']['use_celery']:
                            self.update_state(state='PROGRESS', meta=data)
                        else:
                            self.receive_from_task(data, celery=False)
                        #if process_base:
                        #    break
            # 남아 있는 것을 갱신하기 위해
            Task.meta_refresh_show({'status':status}, None, None)
        return 'wait'

    """
    - 니미 일드에서 에피소드별 메타 새로고침으로 자막 갱신되지 않음. 중드, 외국 다큐, 예능에는 문제 없없음. 버리기 아까운데........
      ERROR (model:205) - Cannot read model from /var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Metadata/TV Shows/a/7ef956be45b59550bb4324550f39aba689c6eab.bundle/Contents/com.plexapp.agents.localmedia
      이게 스캔과정에서 실패해서 나오는지, 파일정리에 나오는지 모르겠음.
    - 에피소드 갱신시마다 쇼 전체 데이터를 가져오는 것도 부담이기도 하니 쇼 기준으로 날리는 것으로 함
    - 에피소드 메타새로고침시 메타 info argument 확인 필요. 예전에는 시즌, 에피 index가 없는게 확실한데 언제 생겼을지도 모름
    - info.json 있을텐데 sjva에 데이터 요청하는 경우도 있음. 확인 필요
    """

    @staticmethod
    def meta_refresh_show(data, new_item_id, new_item_title):
        if data['status']['meta_refresh_show_metadata_item_id'] == None:
            data['status']['meta_refresh_show_metadata_item_id'] = new_item_id
            data['status']['meta_refresh_show_metadata_item_title'] = new_item_title
            
        elif data['status']['meta_refresh_show_metadata_item_id'] == new_item_id:
            logger.debug(f"동일 쇼 : {data['status']['meta_refresh_show_metadata_item_id']}")
        elif data['status']['meta_refresh_show_metadata_item_id'] != new_item_id:
            logger.warning(f"쇼 전체 메타 새로고침 : {data['status']['meta_refresh_show_metadata_item_id']} {data['status']['meta_refresh_show_metadata_item_title']}")
            PlexWebHandle.refresh_by_id(data['status']['meta_refresh_show_metadata_item_id'])
            data['status']['meta_refresh_show_metadata_item_id'] = new_item_id
            data['status']['meta_refresh_show_metadata_item_title'] = new_item_title
            data['status']['meta_refresh_show_count'] += 1


    @staticmethod
    def smi2srt(data):
        try:
            if data['need_smi2srt']:
                from smi2srt.smi2srt_handle import SMI2SRTHandle
                ret = SMI2SRTHandle.start(data['subtitle_filepath'], remake=False, no_remove_smi=False, no_append_ko=False, no_change_ko_srt=False, fail_move_path=None)
                data['status']['smi2srt_count'] += 1
                data['ret']['smi2srt'] = True
                if ret['list']:
                    data['smi2srt'] = ret['list'][0]
                #logger.debug(ret)
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            logger.error('smi2srt 플러그인 설치 필요')





    @staticmethod
    def get_show_meda(con, data, episode_data, is_video=False):

        data['epidode_title'] = episode_data['title']
        data['episode_index'] = episode_data['metadata_items_index']
        data['epidose_metadata_items_id'] = episode_data['metadata_items_id']

        query = '''SELECT id, parent_id, title, metadata_items.'index' AS metadata_items_index FROM metadata_items WHERE id = ?'''
        ce = con.execute(query, (episode_data['metadata_items_parent_id'],))
        ce.row_factory = dict_factory
        season_data = ce.fetchall()[0]

        data['season_title'] = season_data['title']
        data['season_index'] = season_data['metadata_items_index']
        data['season_metadata_items_id'] = season_data['metadata_items_index']
        
        ce = con.execute(query, (season_data['parent_id'],))
        ce.row_factory = dict_factory
        show_data = ce.fetchall()[0]
        data['show_title'] = show_data['title']
        data['show_metadata_items_id'] = show_data['id']

        if is_video:
            query = """SELECT url, codec, language FROM media_streams WHERE media_item_id = ? AND stream_type_id = 3 AND url != ''"""
            ce = con.execute(query, (episode_data['media_items_id'],))
            ce.row_factory = dict_factory
            rows = ce.fetchall()
            for row in rows:
                row['sub'] = row['url'][7:].replace('%20', ' ').replace('%25', '%')
                #logger.debug(row['sub'])
                row['sub'] = os.path.basename(row['sub'])
            data['episode_subtitle'] = rows
            







    @staticmethod
    def find_video(dir_path, fname):
        fn, ext  = os.path.splitext(fname)
        #logger.error((fn, ext))
        tmps = fn.rsplit('.', 1)
        search_filename = fn
        search_filename2 = None
        if len(tmps[-1]) == 2 or len(tmps[-1]) == 3:
            search_filename = tmps[0]
            search_filename2 = fn
        elif tmps[-1] in ['forced', 'normal', 'default']:
            search_filename = tmps[0]

        files = os.listdir(dir_path)
        #logger.error(files)
        
        files = [f for f in files if not re.match(SUBTITLE_EXTS, f)]
        #logger.error(files)
        for f in files:
            #logger.debug(f)
            #logger.debug(search_filename in f)
            if search_filename in f and os.path.splitext(f)[-1].lstrip('.') in VIDEO_EXTS:
                return True, f

        """
        files_1 = [f for f in files if re.match(search_filename, f)]
        for f in files_1:
            if os.path.splitext(f)[-1].lstrip('.') in VIDEO_EXTS:
                return True, f
        
        # org.srt
        files_2 = None
        if search_filename2 is not None:
            files_2 = [f for f in files if re.match(search_filename2, f)]
            for f in files_2:
                if os.path.splitext(f)[-1].lstrip('.') in VIDEO_EXTS:
                    return True, f

        logger.warning("비디오 파일 찾기 실패")
        """
        logger.warning(search_filename)
        logger.warning(files)
        #logger.warning(files_1)
        #logger.warning(files_2)

        return False, None



































QUERY = f'''
SELECT
    metadata_items.id AS metadata_items_id, 
    metadata_items.parent_id AS metadata_items_parent_id, 
    metadata_items.library_section_id AS library_section_id, 
    metadata_items.metadata_type AS metadata_type, 
    metadata_items.guid AS guid,
    metadata_items.media_item_count AS media_item_count,
    metadata_items.title AS title,
    metadata_items.year AS year,
    metadata_items.'index' AS metadata_items_index,
    metadata_items.hash AS metadata_items_hash,
    media_items.id AS media_items_id,
    media_items.section_location_id AS section_location_id,
    media_items.width AS width,
    media_items.height AS height,
    media_items.size AS size,
    media_items.duration AS duration,
    media_items.bitrate AS bitrate,
    media_items.container AS container,
    media_items.video_codec AS video_codec,
    media_items.audio_codec AS audio_codec,
    media_parts.id AS media_parts_id,
    media_parts.directory_id AS media_parts_directory_id,
    media_parts.hash AS media_parts_hash,
    media_parts.file AS file,
    media_streams.id AS media_streams_id,
    media_streams.url AS url
FROM metadata_items, media_items, media_parts, media_streams
WHERE metadata_items.id = media_items.metadata_item_id AND media_items.id = media_parts.media_item_id AND media_items.id == media_streams.media_item_id AND media_streams.url = ?'''


QUERY_VIDEO = f'''
SELECT
    metadata_items.id AS metadata_items_id, 
    metadata_items.parent_id AS metadata_items_parent_id, 
    metadata_items.library_section_id AS library_section_id, 
    metadata_items.metadata_type AS metadata_type, 
    metadata_items.guid AS guid,
    metadata_items.media_item_count AS media_item_count,
    metadata_items.title AS title,
    metadata_items.year AS year,
    metadata_items.'index' AS metadata_items_index,
    metadata_items.hash AS metadata_items_hash,
    media_items.id AS media_items_id,
    media_items.section_location_id AS section_location_id,
    media_items.width AS width,
    media_items.height AS height,
    media_items.size AS size,
    media_items.duration AS duration,
    media_items.bitrate AS bitrate,
    media_items.container AS container,
    media_items.video_codec AS video_codec,
    media_items.audio_codec AS audio_codec,
    media_parts.id AS media_parts_id,
    media_parts.directory_id AS media_parts_directory_id,
    media_parts.hash AS media_parts_hash,
    media_parts.file AS file
FROM metadata_items, media_items, media_parts
WHERE metadata_items.id = media_items.metadata_item_id AND media_items.id = media_parts.media_item_id AND file = ?'''



VIDEO_EXTS = ['3g2', '3gp', 'asf', 'asx', 'avc', 'avi', 'avs', 'bivx', 'bup', 'divx', 'dv', 'dvr-ms', 'evo', 'fli', 'flv', 'm2t', 'm2ts', 'm2v', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'mts', 'nsv', 'nuv', 'ogm', 'ogv', 'tp', 'pva', 'qt', 'rm', 'rmvb', 'sdp', 'svq3', 'strm', 'ts', 'ty', 'vdr', 'viv', 'vob', 'vp3', 'wmv', 'wtv', 'xsp', 'xvid', 'webm']

#SUBTITLE_EXTS =  ['ass', 'ssa', 'smi', 'srt', 'psb']

#Task.start('start', '23')


IGNORE_DIRS =  ['\\bextras?\\b', '!?samples?', 'bonus', '.*bonus disc.*', 'bdmv', 'video_ts', '^interview.?$', '^scene.?$', '^trailer.?$', '^deleted.?(scene.?)?$', '^behind.?the.?scenes$', '^featurette.?$', '^short.?$', '^other.?$', 'extras', 'sub']