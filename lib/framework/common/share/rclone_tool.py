# -*- coding: utf-8 -*-
#########################################################
# python
import os
from datetime import datetime
import traceback
import subprocess
import time
import re
import threading
import json


# sjva 공용
from framework import app, path_data, socketio
from system.logic_command import SystemLogicCommand
from tool_base import ToolSubprocess

from . import logger, Vars

#########################################################

REMOTE_NAME_SJVA_SHARE_TEMP = 'SJVA_SHARE_TEMP' 

class RcloneTool(object):
    @staticmethod
    def lsjson(rclone_path, config_path, remote_path, option=None):
        try:
            command = [rclone_path, '--config', config_path, 'lsjson', remote_path]
            logger.debug(command)
            if option is not None:
                command += option
            logger.debug(command)
            ret = ToolSubprocess.execute_command_return(command, format='json')
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def size(rclone_path, config_path, remote_path, option=None):
        try:
            command = [rclone_path, '--config', config_path, 'size', remote_path, '--json']
            if option is not None:
                command += option
            ret = ToolSubprocess.execute_command_return(command, format='json')
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def rmdir(rclone_path, config_path, remote_path, option=None):
        try:
            command = [rclone_path, '--config', config_path, 'rmdir', remote_path]
            logger.debug(command)
            if option is not None:
                command += option
            logger.debug(command)
            ret = ToolSubprocess.execute_command_return(command)
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())


    



    @staticmethod
    def do_action(rclone_path, config_path, mode, server_type, folder_id, folder_name, server_filename, remote_path, action, folder_id_encrypted=False, listener=None, dry=False, option=None, remove_config=True, show_modal=True, force_remote_name=None):
        # folder_name : 다운로드 일때만 사용한다. root_folder_id 의 이름이다. content 일때 로컬에 폴더를 만들어주는 역할을 한다.
        # 2020-08-12 업로드도 사용
        # server_filname : 다운로드 일때만 사용한다. 루트폴더id 안의 파일명이다. 자막만 고려했다
        #rclone_conf_filepath = None
        try:
            logger.debug('%s %s %s %s %s %s', mode, server_type, folder_id, remote_path, action, folder_id_encrypted)
            if folder_id_encrypted:
                from framework.common.util import AESCipher
                folder_id = AESCipher.decrypt(str(folder_id), Vars.key)
                #logger.debug(folder_id)
            rclone_upload_remote = remote_path.split(':')[0]
            #rclone_conf_filepath = RcloneTool.__make_rclone_conf(config_path, rclone_upload_remote, folder_id)
            #logger.debug(os.path.exists(rclone_conf_filepath))
            return_folder_id = False
            # mode : download, upload
            # server_type : category, content

            if mode == 'download':
                src_remote = remote_path.split(':')[0] if force_remote_name is None or force_remote_name == '' else force_remote_name
            else:
                src_remote = remote_path.split(':')[0]
            server_remote = '{src_remote}:{{{folderid}}}'.format(src_remote=src_remote, folderid=folder_id)

            if mode == 'download':
                #server_remote = '%s:/' % REMOTE_NAME_SJVA_SHARE_TEMP
                #my_remote_path = remote_path
                if server_filename != '':
                    server_remote += '/%s' % server_filename
                else:
                    # 폴더채로 받을때 폴더명 입력해줌
                    remote_path += '/%s' % folder_name
                #command = [rclone_path, '--config', rclone_conf_filepath, 'copyto', server_remote, my_remote_path, '--drive-server-side-across-configs=true', '-v']
                command = [rclone_path, '--config', config_path, 'copyto', server_remote, remote_path, '--drive-server-side-across-configs=true', '-v']

            elif mode == 'upload':
                #server_remote = '%s:/' % REMOTE_NAME_SJVA_SHARE_TEMP
                #my_remote_path = remote_path
                if server_type == 'category':
                    # my_remote_path눈 무조건 폴더여야함
                    #category_server_remote = server_remote
                    #server_remote += my_remote_path.split('/')[-1]
                    #2020-08-12
                    if folder_name != '':
                        server_remote += '/%s' % folder_name
                    else:
                        server_remote += '/%s' % remote_path.split('/')[-1]
                    return_folder_id = True
                elif server_type == 'content':
                    # my_remote_path 폴더, 파일
                    pass
                    #my_remote_path += '/%s' % folder_name
                command = [rclone_path, '--config', config_path, 'copy', remote_path, server_remote, '--drive-server-side-across-configs=true', '-v']
            elif mode == 'move':
                #server_remote = '%s:/' % REMOTE_NAME_SJVA_SHARE_TEMP
                #my_remote_path = remote_path
                if server_type == 'category':
                    #category_server_remote = server_remote
                    #server_remote += my_remote_path.split('/')[-1]
                    if folder_name != '':
                        server_remote += '/%s' % folder_name
                    else:
                        server_remote += '/%s' % remote_path.split('/')[-1]
                    return_folder_id = True
                command = [rclone_path, '--config', config_path, 'move', remote_path, server_remote, '--drive-server-side-across-configs=true', '-v']
            if dry:
            #if True:
                command.append('--dry-run')
            if option is not None:
                command += option
            
            logger.debug(command)

            from system.logic_command2 import SystemLogicCommand2
            from system.logic_command import SystemLogicCommand
            #ret  = SystemLogicCommand.execute_command_return(command, format='json')
            #ret  = SystemLogicCommand.execute_command_return(command)
            #['hide', 'rm', '-rf', rclone_conf_filepath],      
            ret = {'percent':0, 'folder_id':'', 'config_path':config_path, 'server_remote':server_remote}
            return_log = SystemLogicCommand2('공유', [
                ['msg', '잠시만 기다리세요'],
                command,
                ['msg', 'Rclone 명령을 완료하였습니다.'],
            ], wait=True, show_modal=show_modal).start()
            for tmp in return_log:
                if tmp.find('Transferred') != -1 and tmp.find('100%') != -1:
                    logger.debug(tmp)
                    ret['percent'] = 100
                    break
                elif mode == 'move' and tmp.find('Checks:') != -1 and tmp.find('100%') != -1:
                    ret['percent'] = 100
                    break
                elif tmp.find('Checks:') != -1 and tmp.find('100%') != -1:
                    ret['percent'] = 100
                    break

            if return_folder_id:
                #logger.debug(return_log)
                
                #ret['percent'] = 100
                if ret['percent'] == 100:
                #if ret['percent'] > -1:
                    parent_remote = '/'.join(server_remote.split('/')[:-1])
                    logger.debug('parent_remote : %s', parent_remote)
                    for i in range(20):
                        command = [rclone_path, '--config', config_path, 'lsjson', parent_remote, '--dirs-only']
                        logger.debug(command)
                        ret['lsjson'] = SystemLogicCommand.execute_command_return(command, format='json')
                        logger.debug(ret)
                        tmp = server_remote.split('/')[-1]
                        for item in ret['lsjson']:
                            if item['Name'] == tmp:
                                from framework.common.util import AESCipher
                                ret['folder_id'] = AESCipher.encrypt(str(item['ID']), Vars.key)
                                command = [rclone_path, '--config', config_path, 'lsjson', parent_remote +'/'+ item['Name'], '-R', '--files-only']

                                logger.debug (command)
                                ret['lsjson'] = SystemLogicCommand.execute_command_return(command, format='json')
                                ret['lsjson'] = sorted(ret['lsjson'], key=lambda k:k['Path'])
                                break
                        logger.debug('folderid:%s', ret['folder_id'])
                        if ret['folder_id'] == '': 
                            logger.debug('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                            logger.debug('CCCCCRRRRRRRIIIIIIITTTTTIIIIICCCCCCAAAAAAALLLLL...... : %s', i)
                            logger.debug(ret)
                        else:
                            break
                        time.sleep(30)
                        logger.debug('GET FOLDERID : %s', i)
                            
            return ret
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        """
        finally:
            try:
                if rclone_conf_filepath is not None and os.path.exists(rclone_conf_filepath):
                    if remove_config:
                        os.remove(rclone_conf_filepath)
                        pass
                pass
            except Exception as exception: 
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc())
        """
    
    
    @staticmethod
    def fileid_copy(rclone_path, config_path, fileid, remote_path):
        try:
            #logger.debug('fileid_copy %s %s %s %s', rclone_path, config_path, fileid, remote_path)
            from framework.common.util import AESCipher
            fileid = AESCipher.decrypt(str(fileid), Vars.key)

            command = [rclone_path, '--config', config_path, 'copy', '{remote}:{{{fileid}}}'.format(remote=remote_path.split(':')[0], fileid=fileid),remote_path, '--drive-server-side-across-configs', '-v']
            #logger.debug(command)
            from system.logic_command import SystemLogicCommand
            log = SystemLogicCommand.execute_command_return(command)
            logger.debug('fileid copy 결과 : %s', log)

            if log.find('100%') != -1:
                return True
            return False
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    

    #################################################################

    # inner
    @staticmethod
    def __make_rclone_conf(config_path, rclone_upload_remote, folder_id):
        try:
            #logger.debug(rclone_upload_remote)
            from framework.common.util import read_file
            if os.path.exists(config_path):
                rclone_info = read_file(config_path)

            from framework import path_data
            import time
            filename = '%s.conf' % (str(time.time()).split('.')[0])
            conf_filepath = os.path.join(path_data, 'tmp', filename)
            #logger.debug('conf_filepath:%s', conf_filepath)

            #logger.debug(rclone_info)
            start = -1
            dest_remote = None
            match = None
            first_rclone_info = None
            while True:
                start = rclone_info.find('[', start+1)
                if start == -1:
                    break
                next_start = rclone_info.find('[', start+1)
                if next_start == -1:
                    dest_remote = rclone_info[start:]
                else:
                    dest_remote = rclone_info[start:next_start]
                #dest_remote = dest_remote.replace('team_drive', 'team_drive_dummy')
                #logger.debug(dest_remote)
                if first_rclone_info is None and dest_remote.find('access_token') != -1:
                    first_rclone_info = dest_remote

                import re
                match = re.compile(r'\[(?P<remote_name>.*?)\]').search(dest_remote.strip())

                if match.group('remote_name') == rclone_upload_remote:
                    break
                else:
                    dest_remote = None
                    match = None
                #공유드라이브는 삭제

            #dest_remote : 찾은 리모트
            #rclone_info : 서버리모트가 될 리모트

            if rclone_upload_remote is not None:
                if dest_remote is None:
                    raise Exception('cannot find remote_name')
                else:
                    # 로컬등 구글게 아니면?
                    #if dest_remote.find('access_token') == -1:
                    if dest_remote.find('type = drive') == -1:
                        if first_rclone_info is not None:
                            src_remote_ready = first_rclone_info
                        else:
                            raise Exception('cannot find google remote_name')
                    else:
                        # 정상인 경우
                        pass
                        src_remote_ready = dest_remote
            else:
                src_remote_ready = first_rclone_info

            src_remote_ready = src_remote_ready.replace('team_drive', 'team_drive_dummy')
            # gclone이나 로컬이라면 rclone

            match = re.compile(r'\[(?P<remote_name>.*?)\]').search(src_remote_ready.strip())
            server_rclone = src_remote_ready.replace('[%s]' % match.group('remote_name'), '[%s]' % REMOTE_NAME_SJVA_SHARE_TEMP)
            server_rclone += '\nroot_folder_id = %s' % folder_id
            filedata = '%s\n\n%s\n' % (dest_remote, server_rclone)
            #logger.debug(filedata)

            import framework.common.util as CommonUtil
            CommonUtil.write_file(filedata, conf_filepath) 
            return conf_filepath
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def folderid_decrypt(folderid):
        from framework.common.util import AESCipher
        folderid = AESCipher.decrypt(str(folderid), Vars.key)
        return folderid


    