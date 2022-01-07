#try:
#    from framework import logger
#except:
from  .logger import get_logger
logger = get_logger(__name__)

def d(data):
    if type(data) in [type({}), type([])]:
        import json
        return '\n' + json.dumps(data, indent=4, ensure_ascii=False)
    else:
        return str(data)

from .file import SupportFile
from .discord import SupportDiscord
from .image import SupportImage
from .process import SupportProcess
from .ffmpeg import SupportFfmpeg



