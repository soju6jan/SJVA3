import traceback
import os
import platform
import pty
import subprocess
import base64
import select
import struct
import fcntl
import termios
from shlex import split
from flask import request, render_template, jsonify

from .plugin import P
name = 'terminal'
logger = P.logger
package_name = P.package_name
from framework import socketio, login_required, current_user


class LogicTerminal:
    pty_list = {}
    sid_list = []

    @P.blueprint.route('/')
    @login_required
    def home():
        arg = {'package_name': package_name}
        return render_template(f'{package_name}_terminal.html', arg=arg)

    
    # 터미널 실행
    @staticmethod
    @login_required
    @socketio.on('connect', namespace=f'/{package_name}')
    def connect():
        try:
            #logger.debug(current_user)
            #logger.debug(current_user.authenticated)

            logger.debug('socketio: /%s/%s, connect, %s',
                         package_name, name, request.sid)
            #cmd = split(ModelSetting.get(f'{name}_shell'))
            cmd = 'bash' if platform.system() != 'Windows' else 'cmd.exe'
            (master, slave) = pty.openpty()  # 터미널 생성
            popen = subprocess.Popen(
                cmd, stdin=slave, stdout=slave, stderr=slave, start_new_session=True)  # 셸 실행
            logger.debug('cmd: %s, child pid: %s', cmd, popen.pid)
            LogicTerminal.pty_list[request.sid] = {
                'popen': popen, 'master': master, 'slave': slave}
            LogicTerminal.sid_list.append(request.sid)
            socketio.start_background_task(
                LogicTerminal.output_emit, master, request.sid)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    # 터미널 종료
    @staticmethod
    @socketio.on('disconnect', namespace=f'/{package_name}')
    def disconnect():
        try:
            logger.debug('socketio: /%s/%s, disconnect, %s', package_name, name, request.sid)
            popen = LogicTerminal.pty_list[request.sid]['popen']
            if popen.poll():
                popen.kill()
            os.close(LogicTerminal.pty_list[request.sid]['master'])
            os.close(LogicTerminal.pty_list[request.sid]['slave'])
            del LogicTerminal.pty_list[request.sid]
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    # 커맨드 입력
    @staticmethod
    @socketio.on('input', namespace=f'/{package_name}')
    def input(data):
        try:
            #logger.debug('socketio: /%s/%s, input, %s, %s', package_name, name, request.sid, data)
            fd = LogicTerminal.pty_list[request.sid]['master']
            os.write(fd, base64.b64decode(data))
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    # 크기조절
    @staticmethod
    @socketio.on('resize', namespace=f'/{package_name}')
    def resize(data):
        try:
            logger.debug('socketio: /%s/%s, resize, %s, %s',
                         package_name, name, request.sid, data)
            fd = LogicTerminal.pty_list[request.sid]['master']
            LogicTerminal.set_winsize(fd, data['rows'], data['cols'])
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    # 출력 전송
    @staticmethod
    def output_emit(fd, room):
        try:
            max_read_bytes = 1024 * 20
            while True:
                socketio.sleep(0.01)
                if select.select([fd], [], [], 0)[0]:
                    output = os.read(fd, max_read_bytes).decode()
                    socketio.emit(
                        'output', output, namespace=f'/{package_name}', room=room)
        except OSError as e:    # 터미널 종료
            pass
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    # 터미널 사이즈 설정
    @staticmethod
    def set_winsize(fd, row, col, xpix=0, ypix=0):
        winsize = struct.pack('HHHH', row, col, xpix, ypix)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


    @staticmethod
    def plugin_unload():
        for key, value in LogicTerminal.pty_list.items():
            try:
                popen = value['popen']
                if popen.poll():
                    popen.kill()
                os.close(value['master'])
                os.close(value['slave'])
            except Exception as e:
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
