from framework import logger
from .notify import ToolBaseNotify
from .file import ToolBaseFile
from .aes_cipher import ToolAESCipher
from .celery_shutil import ToolShutil
from .subprocess import ToolSubprocess
from .rclone import ToolRclone
from .ffmpeg import ToolFfmpeg
from .util import ToolUtil
from .hangul import ToolHangul
from .os_command import ToolOSCommand


def d(data):
    if type(data) in [type({}), type([])]:
        import json
        return '\n' + json.dumps(data, indent=4, ensure_ascii=False)
    else:
        return str(data)
