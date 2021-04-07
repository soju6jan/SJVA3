# -*- coding: utf-8 -*-
import os
import re
import datetime
import shutil
from enum import Enum
#from daum_tv import DaumTV
from pytz import timezone
import plex
import daum_tv
from framework.logger import get_logger
package_name = __name__.split('.')[0]
logger = get_logger(package_name)

class EntityLibraryPathRoot(object):
    class DriveType(Enum):
        # 로컬을 의미한다.
        LOCAL = 0 
        # RCLONE으로 직접 올리는 폴더이다. rclone_path가 있어야 하며 sync_path는 없어도 된다.
        # 임시폴더는 mount_path 아래 rclone 폴더를 만들고 수행한다.
        RCLONE = 1
        # 사용자가 직접 올리는 폴더를 의미한다. rclone_path 없어도 되며, sync_path가 mount_path과 같은 depth를 의미한다. 파일을 sync_path로 옮기는 것까지가 
        CLOUD = 2
        def __int__(self):
            return self.value
    drive_type = -1 
    mount_path = ''
    rclone_path = '' 
    sync_path = ''
    depth = -1
    replace_for_plex = None

    def __init__(self, drive_type, mount_path, depth, rclone_path=None, sync_path=None, replace_for_plex=None):
        self.drive_type = drive_type
        self.mount_path = mount_path
        self.rclone_path = rclone_path
        self.sync_path = sync_path
        self.depth = depth
        self.replace_for_plex = replace_for_plex
    
    def _get_rclone_remove(self):
        return self.rclone_path.split(':')[0]
    
    def get_local_temp(self):
        return 'rclone_' + self._get_rclone_remove()

    def is_rclone(self):
        return self.drive_type == EntityLibraryPathRoot.DriveType.RCLONE
    
    def get_genre_list(self):
        return os.listdir(self.mount_path)



class EntityLibraryPath(object):
    RENAME_REGEX = r'[\s\.\,\-\[\]\?\:\!\_\=\+]'
    entity_library_root = None
    basename = ''   # 폴더명
    abspath = ''    # 절대경로
    compare_name = '' # 특수문자 공백제거 비교시 사용되는 이름
    
    def __init__(self, entity_library_root, basename, abspath):
        self.entity_library_root = entity_library_root
        self.basename = basename
        self.abspath = abspath
        self.compare_name = re.sub(self.RENAME_REGEX, '', basename)

    def __str__(self):
        return "RootType: {0}\tBasename: {1}\tAbspath: {2}\tCompareName: {3} ".format(self.entity_library_root.drive_type, self.basename.encode('cp949'), self.abspath.encode('cp949'), self.compare_name.encode('cp949'))
        
        

class EntityShow(object):
    idx = -1
    
    class VideoType(Enum):
        KOREA_TV = 0
        SUBS = 1
        def __int__(self):
            return self.value

    video_type = -1             # 방송, 자막등
    filename = ''               # 파일명만
    original_filename = ''      # 오리지널 파일명
    download_time = ''          # 다운로드시간
    move_type = -1              # 로컬이냐 클라우드냐
    match_folder_name = ''      # 방송명 set_find_library_path 때 scan_abspath와 같이 설정
    move_abspath_local = ''     # 옮겨질 절대경로 sef_find_library_path 
    move_abspath_sync = ''      # 업로드 할 절대경로. rclone일때 다운로드폴더내, sync일때 지정된
    move_abspath_cloud = ''     # 업로드 완료후 보여질 폴더. root의 마운트 폴더
    send_command_time = ''     # XXXXXXXXXXX 삭제
    scan_status = -1              # 스캔플래그 
    scan_time = ''              # 스캔완료시 입력
    scan_abspath = ''           # 스캔한 폴더. 로컬일때 move_abspath_local / 그외move_abspath_cloud
    plex_section_id = -1        # 섹션ID
    plex_show_id = -1           # 쇼ID
    plex_daum_id = -1           # 다음ID
    plex_title = ''             # 
    plex_image = ''             #
    plex_abspath = ''

    # NOT DB
    nd_compare_name = ''        # 비교시 사용할 이름
    nd_download_path = ''    # 다운로드 폴더명
    nd_download_abspath = '' # 파일명을 포함한 절대경로
    nd_find_library_path = None   # 찾은 EntityLibraryPath
    nd_plex_show = ''
    modelfile = None
    log = ''
    class ScanStatus(Enum):
        DEFAULT = -1
        MOVED = 1
        EXIST_IN_LIBRARY = 2
        SCAN_COMPLETED = 3
        DELETE_FILE = 9

        def __int__(self):
            return self.value


    #전통적, deresisi, 회차없음
    # 회차없읍임 제목 E01 을 제목으로 인식해버림
    _REGEX_FILENAME = [
        r'^(?P<name>.*?)\.E(?P<no>\d+)(\-E\d{1,4})?\.?(END\.)?(?P<date>\d{6})\.(?P<etc>.*?)(?P<quality>\d+)[p|P](\-?(?P<release>.*?))?(\.(.*?))?$',
        r'^(?P<name>.*?)\sE(?P<no>\d+)(\-E\d{1,4})?\.?(END\.)?(?P<date>\d{6})\.(?P<etc>.*?)(?P<quality>\d+)[p|P](?P<more>\..*?)(?P<ext>\.[\w|\d]{3})$',
        r'^(?P<name>.*?)\.(E(?P<no>\d+)\.?)?(END\.)?(?P<date>\d{6})\.(?P<etc>.*?)(?P<quality>\d+)[p|P](\-?(?P<release>.*?))?(\.(.*?))?$',

    ]

    _REGEX_FILENAME_RENAME = r'(?P<title>.*?)[\s\.]E?(?P<no>\d{1,2})[\-\~\s\.]?E?\d{1,2}'

    filename_name = ''
    filename_no = ''
    filename_date = ''
    filename_etc = ''
    filename_quality = ''
    filename_release = ''
    filename_more = ''
    daum_info = None

    def __init__(self, filename, by=0, nd_download_path=None, daum_info=None, except_genre_remove_epi_number=None):
        #if nd_download_path != None:
        # 파일처리 모듈에서 호출
        self.original_filename = filename
        self.filename = filename
        self.analyze_filename()
        self.except_genre_remove_epi_number = except_genre_remove_epi_number
        if by == 0:
            if self.video_type == -1:
                return None            
            self.nd_download_path = nd_download_path
            self.nd_download_abspath = os.path.join(nd_download_path, filename)
            self.download_time = datetime.datetime.now()
            self.change_filename_continous_episode()
            #self.nd_compare_name = re.sub(EntityLibraryPath.RENAME_REGEX, '', self.filename)
            # 2019-05-28
            self.nd_compare_name = re.sub(EntityLibraryPath.RENAME_REGEX, '', self.filename_name)
            
            #self.daum_info = DaumTV.get_daum_tv_info_from_daum(self.filename_name)
            self.daum_info = daum_tv.Logic.get_daum_tv_info(self.filename_name)
            logger.debug('<Daum>')
            self.log += '<Daum>\n'
            if self.daum_info:
                logger.debug(' - 파일명으로 매칭된 Daum 정보: %s(%s)\n', self.daum_info.title, self.daum_info.genre)
                self.log += '매칭된 Daum 정보: %s(%s)\n' % (self.daum_info.title, self.daum_info.genre)
            else:
                logger.debug(' - 파일명으로 매칭된 Daum 정보 없음\n')
                self.log += 'Daum 정보 없음\n'
            # 파일명 고치는 옵션이 켜져있다면
            # 스튜디오 추가 : [tvn]
            # 파일명에 에피소드 정보가 있지만, 다음에 없을 경우 파일명에서 에피소드 정보 제외
            if True and self.daum_info is not None:
                self.change_filename_by_rule()
            logger.debug('<Info>')
            logger.debug(' - 방송명: %s', self.filename_name)
            logger.debug(' - 방송일: %s', self.filename_date)
            logger.debug(' - 에피소드넘버: %s', self.filename_no)
            logger.debug(' - quality: %s %s', self.filename_quality, self.filename_release)

            self.log += '<파일명 정보>\n'
            self.log += ' - 방송명: %s\n' % self.filename_name
            self.log += ' - 방송일: %s\n' % self.filename_date
            self.log += ' - 에피소드넘버: %s\n' % self.filename_no
            self.log += ' - quality: %s %s\n' % (self.filename_quality, self.filename_release)

        #기존파일
        elif by == 1:
            pass
        elif by == 2:
            self.change_filename_continous_episode(move=False)
            self.daum_info = daum_info
            self.change_filename_by_rule(move=False)
        
        #통합하고 다시 작성함. 파일 title 생성할때.. rss 에서
        elif by == 'only_filename':
            if self.video_type == -1:
                return None
            self.change_filename_continous_episode(move=False)
            if self.video_type == EntityShow.VideoType.KOREA_TV:
                self.daum_info = daum_tv.Logic.get_daum_tv_info(self.filename_name)
                if self.daum_info is not None:
                    self.change_filename_by_rule(move=False)
            else:
                self.daum_info = None


    def analyze_filename(self):
        for idx, regex in enumerate(self._REGEX_FILENAME):
            match = re.compile(regex).match(self.filename)
            if match:
                logger.debug('매칭:%s %s', regex, self.filename)
                self.video_type = EntityShow.VideoType.KOREA_TV
                self.filename_name = match.group('name')
                self.filename_no = match.group('no')
                self.filename_date = match.group('date')
                self.filename_etc = match.group('etc').replace('.', '')
                self.filename_quality = match.group('quality')
                self.filename_release = match.group('release') if 'release' in match.groupdict() else ''
                self.filename_more = match.group('more') if 'more' in match.groupdict() else ''
                if self.filename_no is not None and self.filename_no != '': 
                    self.filename_no = int(self.filename_no)
                else: 
                    self.filename_no = -1
                if idx == 1:
                    self.filename = EntityShow.make_filename(self)
                break
    
    def change_filename_continous_episode(self, move=True):
        if self.filename_name.find('합') == -1:
            return
        match = re.compile(self._REGEX_FILENAME_RENAME).match(self.filename_name)
        if match:
            logger.debug('<합본 처리>')
            self.log += '<합본 파일 처리>\n'
            self.filename_name = match.group('title').strip()
            self.filename_no = int(match.group('no'))
            self.filename = EntityShow.make_filename(self)
            if move:
                _ = os.path.join(self.nd_download_path, self.filename)
                shutil.move(self.nd_download_abspath, _)
                self.nd_download_abspath = _
                logger.debug(' - 파일명 변경:%s -> %s', self.original_filename, self.filename)
                self.log += ' - 파일명변경\nFrom : %s\nTo : %s\n' % (self.original_filename, self.filename)

    def change_filename_by_rule(self, move=True):
        logger.debug('<Daum 정보 기반으로 파일명 변경>')
        flag_need_rename = False
        # 무조건 다음에 회차정보가 있어야한다. 없으면 무시

        if self.daum_info.has_episode_info():
            self.log += '1-1. Daum 에피소드 정보 있음\n'
            key = '20' +self.filename_date
            if key in self.daum_info.episode_list:
                self.log += '2-1. 파일명 방송일과 일치하는 Daum 에피소드 정보 있음\n'
                flag = False
                # 파일명에 회차정보가 없을 수 있다.
                logger.debug(' - 파일정보 Episode Date:%s No:%s', self.filename_date, self.filename_no)
                self.log += ' - 파일명 정보. 방송일:%s 회차:%s\n' % (self.filename_date, self.filename_no)
                if self.filename_no != -1:
                    self.log += '3-1. 파일명에 회차 정보 있음 : %s\n' % self.filename_no
                    for _ in self.daum_info.episode_list[key]:
                        if int(_) == self.filename_no:
                            flag = True
                            break
                    if flag:
                        logger.debug(' - Daum 정보와 일치')
                        self.log += '4-1. 회차 정보 Daum과 일치\n'
                    else:
                        logger.debug(' - Daum 정보와 불일치')
                        self.log += '4-2. 회차 정보 Daum과 불일치\n'
                        # 날짜가 잘못되어 있을 수 있다. 에피정보는 정확하나

                        logger.debug(' - Daum 정보 Date:%s Count:%s No:%s', key, len(self.daum_info.episode_list[key]), self.daum_info.episode_list[key][0])
                        self.log += ' - Daum 정보. 방송일:%s 회차:%s Count:%s\n' % (key, self.daum_info.episode_list[key][0], len(self.daum_info.episode_list[key]))

                        # 멀티에피소드는 고려하지 않는다
                        # 1일 4회차 방송은 고려한다 운명과 분노
                        # 2019-03-25 무엇이든 물어보살.. 파일럿 끝나고 정규시 문제. 푹 4회, 다음 1회
                        logger.debug(' - episode_count_one_day : %s', self.daum_info.episode_count_one_day)
                        if self.daum_info.episode_count_one_day == 4:
                            if self.filename_no * 2  == int(self.daum_info.episode_list[key][1]):
                                self.filename_no = int(self.daum_info.episode_list[key][0])
                            elif self.filename_no * 2  == int(self.daum_info.episode_list[key][3]):
                                self.filename_no = int(self.daum_info.episode_list[key][2])
                            flag_need_rename = True
                        else:
                            self.filename_no = int(self.daum_info.episode_list[key][0])
                            flag_need_rename = True
                else:
                    self.log += '3-2. 파일명에 회차 정보 없음\n'
                    self.log += ' - 파일명에 회차정보 삽입. Daum 정보. 방송일:%s 회차:%s Count:%s\n' % (key, self.daum_info.episode_list[key][0], len(self.daum_info.episode_list[key]))
                    logger.debug(' - 파일정보 Epi no : %s date: %s', self.filename_no, self.filename_date)
                    logger.debug(' - 파일명에 회차정보 삽입. Daum 정보 - date:%s count:%s %s', key, len(self.daum_info.episode_list[key]), self.daum_info.episode_list[key][0])
                    self.filename_no = int(self.daum_info.episode_list[key][0])
                    flag_need_rename = True
            else:
                self.log += '2-2. 파일명 방송일과 일치하는 Daum 에피소드 정보 없음\n'
        else:
            self.log += '1-2. Daum에 에피소드 정보 없음\n'
            logger.debug(' - 다음 회차 정보 없음')
            if True and self.filename_no != -1:
                """
                if self.except_genre_remove_epi_number is not None and ('all' in self.except_genre_remove_epi_number or self.daum_info.genre in self.except_genre_remove_epi_number):
                    self.log += ' 1-2-1. 파일명에 회차는 있지만 Daum에 정보가 없어서 회차정보 삭제. 삭제 제외 장르\n'
                else:
                    self.log += ' 1-2-1. 파일명에 회차는 있지만 Daum에 정보가 없어서 회차정보 삭제\n'
                    self.filename_no = -1 
                    flag_need_rename = True
                """
                pass
            else:
                self.log += '1-2-2. 파일명과 Daum 모두 회차 정보 없음\n'
        
        if flag_need_rename:
            self.log += '<파일명 변경>\n'
            logger.debug(' - 파일명 변경')
            logger.debug('  * From : %s', self.filename)
            self.log += '  * From : %s\n' % self.filename
            self.filename = EntityShow.make_filename(self)
            logger.debug('  * To : %s', self.filename)
            self.log += '  * To : %s\n' % self.filename
            if move:
                _ = os.path.join(self.nd_download_path, self.filename)
                shutil.move(self.nd_download_abspath, _)
                self.nd_download_abspath = _
                

    @classmethod
    def make_filename(cls, _entity):
        ext = os.path.splitext(_entity.filename)[1]
        ret = _entity.filename_name
        if _entity.filename_no != -1:
            if _entity.filename_no < 10:
                ret = '%s.E0%s' % (ret, _entity.filename_no)
            else:
                ret = '%s.E%s' % (ret, _entity.filename_no)
        ret = '%s.%s' % (ret, _entity.filename_date)
        if _entity.filename_etc: 
            ret = '%s.%s' % (ret, _entity.filename_etc)
        if _entity.filename_quality: 
            ret = '%s.%sp' % (ret, _entity.filename_quality)
        if _entity.filename_release != '' and _entity.filename_release is not None: 
            ret = '%s-%s' % (ret, _entity.filename_release)
        ret = '%s%s%s' % (ret, _entity.filename_more, ext)  
        return ret

        
    # 이동할 폴더정보를 가지고, 정보들을 세팅한다.    
    def set_find_library_path(self, nd_find_library_path):
        self.nd_find_library_path = nd_find_library_path
        if nd_find_library_path.entity_library_root.drive_type == EntityLibraryPathRoot.DriveType.LOCAL:
            self.move_abspath_local = os.path.join(self.nd_find_library_path.abspath, self.filename)
            if nd_find_library_path.entity_library_root.replace_for_plex is not None:
                self.plex_abspath = self.move_abspath_local.replace(nd_find_library_path.entity_library_root.replace_for_plex[0], nd_find_library_path.entity_library_root.replace_for_plex[1])
                #2019-01-11 윈도우에서 리눅스로 plex서버로
                if nd_find_library_path.entity_library_root.replace_for_plex[1][0] == '/':
                    self.plex_abspath = self.plex_abspath.replace('\\', '/')
                else:
                    self.plex_abspath = self.plex_abspath.replace('/', '\\')
            else:
                self.plex_abspath = self.move_abspath_local
        elif nd_find_library_path.entity_library_root.drive_type == EntityLibraryPathRoot.DriveType.RCLONE:
            self.move_abspath_cloud = os.path.join(self.nd_find_library_path.abspath, self.filename)
            if nd_find_library_path.entity_library_root.replace_for_plex is not None:
                self.plex_abspath = self.move_abspath_cloud.replace(nd_find_library_path.entity_library_root.replace_for_plex[0], nd_find_library_path.entity_library_root.replace_for_plex[1])
                if nd_find_library_path.entity_library_root.replace_for_plex[1][0] == '/':
                    self.plex_abspath = self.plex_abspath.replace('\\', '/')
                else:
                    self.plex_abspath = self.plex_abspath.replace('/', '\\')
            else:
                self.plex_abspath = self.move_abspath_cloud         
        self.scan_abspath = self.nd_find_library_path.abspath
        self.match_folder_name = self.nd_find_library_path.basename 
        self.move_type = nd_find_library_path.entity_library_root.drive_type
        
        if self.scan_abspath != '':
            plex.Logic.get_section_id(self)

    # 파일을 이동한다.
    def move_file(self):
        self.log += '<파일이동>\n'
        if self.nd_find_library_path.entity_library_root.drive_type == EntityLibraryPathRoot.DriveType.LOCAL:
            logger.debug(' * 로컬 폴더임')
            logger.debug(' * 파일 이동')
            self.log += '- 로컬 이동 처리\n'
            self._move_file_local()
        else:
            logger.debug(' * 클라우드 폴더임')
            self.log += '- 원격 동기화 폴더 이동 처리\n'
            self._move_file_for_cloud()

    def _move_file_local(self):
        try:
            flag_move_file = True
            logger.debug('_move_file_local move_abspath_local :%s', self.move_abspath_local)
            if os.path.exists(self.move_abspath_local):
                self.log += '- 로컬 같은 파일 있음\n'
                logger.debug('같은 파일 있음')
                if os.path.getsize(self.nd_download_abspath) == os.path.getsize(self.move_abspath_local):
                    logger.debug('사이즈가 같아 그냥 삭제')
                    self.log += '- 사이즈가 같아 삭제\n'
                    os.remove(self.nd_download_abspath)
                    flag_move_file = False
                    self.set_scan_status(EntityShow.ScanStatus.DELETE_FILE)
                else:
                    logger.debug('사이즈가 달라 기존 파일 삭제')
                    self.log += '- 사이즈가 달라 기존 파일 삭제\n'
                    os.remove(self.move_abspath_local)
            if flag_move_file:
                #shutil.move(self.nd_download_abspath, os.path.dirname(self.move_abspath_local))
                if os.path.exists(self.nd_download_abspath):
                    shutil.move(self.nd_download_abspath, self.move_abspath_local)
                self.set_scan_status(EntityShow.ScanStatus.MOVED)
                self.log += ' * src:%s\n * dest:%s\n' % (self.nd_download_abspath, os.path.dirname(self.move_abspath_local))
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    def _move_file_for_cloud(self):
        try:
            flag_move_file = True
            if os.path.exists(self.move_abspath_cloud):
                logger.debug('같은 파일 있음')
                self.log += '- 원격폴더 같은 파일 있음\n'
                if os.path.getsize(self.nd_download_abspath) == os.path.getsize(self.move_abspath_cloud):
                    logger.debug('사이즈가 같아 그냥 삭제')
                    self.log += '- 사이즈가 같아 삭제\n'
                    os.remove(self.nd_download_abspath)
                    flag_move_file = False
                else:
                    logger.debug('사이즈가 달라 기존 파일 삭제')
                    self.log += '- 사이즈가 달라 기존 파일 삭제\n'
                    try:
                        os.remove(self.move_abspath_cloud)
                    except:
                        logger.debug('원격파일 삭제 실패')
                    self.set_scan_status(EntityShow.ScanStatus.DELETE_FILE)
            if flag_move_file:
                sync_path = os.path.join(self.nd_download_path, self.nd_find_library_path.entity_library_root.get_local_temp())
                logger.debug('sync_path : %s', sync_path)
                if not os.path.exists(sync_path):
                    os.mkdir(sync_path)
                basename = os.path.basename(self.nd_find_library_path.entity_library_root.mount_path) #[방송중]
                splits = self._path_split(self.scan_abspath)
                idx = splits.index(basename)
                for _ in splits[idx:]:
                    sync_path = os.path.join(sync_path, _)
                    if not os.path.exists(sync_path):
                        if not os.path.exists(sync_path):
                            os.mkdir(sync_path)
                            logger.debug('sync_path2 mkdir: %s', sync_path)
                
                self.move_abspath_sync = os.path.join(sync_path, self.filename)
                logger.debug('Movefile for cloud %s %s', self.nd_download_abspath, sync_path)
                if os.path.exists(os.path.join(sync_path, self.filename)):
                    logger.debug('already file exist.. exist file remove : %s', os.path.join(sync_path, self.filename))
                    os.remove(os.path.join(sync_path, self.filename))
                if os.path.exists(self.nd_download_abspath):
                    
                    shutil.move(self.nd_download_abspath, sync_path)
                    logger.debug('Real move..')
                self.set_scan_status(EntityShow.ScanStatus.MOVED)
                self.log += ' * src:%s\n * dest:%s\n' % (self.nd_download_abspath, sync_path)
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    def set_scan_status(self, status):
        self.scan_status = status
        if status == EntityShow.ScanStatus.SCAN_COMPLETED:
            self.scan_time = datetime.datetime.now()
    
    def get_finalpath(self):
        if self.move_type == EntityLibraryPathRoot.DriveType.LOCAL:
            return self.move_abspath_local
        else:
            return self.move_abspath_cloud          

    def _path_split(self, p, l=None):
        if l is None: 
            l = []
        if p == os.path.dirname(p):
            l.insert(0, os.path.dirname(p))    
            return l
        else:
            l.insert(0, os.path.basename(p))
        return self._path_split(os.path.dirname(p), l)

if __name__ == '__main__':
    pass
    