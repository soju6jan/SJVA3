import os, sys, traceback, subprocess, json, platform, time
import shutil
from . import logger


class SupportFfmpeg(object):

    @classmethod
    def download_m3u8(cls, config):
        try:
            
            if config.get('proxy') == None:
                if config.get('headers') == None:
                    command = [config.get('ffmpeg_path'), '-y', '-correct_ts_overflow', '0', '-i', config['url'], '-c', 'copy', '-bsf:a', 'aac_adtstoasc']
                else:
                    headers_command = []
                    for key, value in config.get('headers').items():
                        if key.lower() == 'user-agent':
                            headers_command.append('-user_agent')
                            headers_command.append(value)
                            pass
                        else:
                            headers_command.append('-headers')
                            headers_command.append('\'%s:%s\''%(key,value))
                    command = [config.get('ffmpeg_path'), '-y', '-correct_ts_overflow', '0'] + headers_command + ['-i', config['url'], '-c', 'copy', '-bsf:a', 'aac_adtstoasc']
            else:
                command = [config.get('ffmpeg_path'), '-y', '-correct_ts_overflow', '0', '-http_proxy', config.get('proxy'), '-i', config['url'], '-c', 'copy', '-bsf:a', 'aac_adtstoasc']

            filename = str(int(time.time())) + '.mp4'
            tmp = config.get('tmp_dir')
            if tmp == None:
                tmp = os.getcwd()
            tmp_filepath = os.path.join(tmp, filename)
            command.append(tmp_filepath)
            logger.debug(' '.join(command))
            from . import SupportSubprocess
            ret = SupportSubprocess.execute(command, timeout=10)
            logger.error(ret)
            if os.path.exists(tmp_filepath):
                shutil.move(tmp_filepath, config.get('output_filepath'))


        except Exception as e: 
            logger.error(f'Exception:{str(e)}', )
            logger.error(traceback.format_exc())
            logger.error('command : %s', command)
            