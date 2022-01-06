try:
    from framework import logger
except:
    import logging
    logger = logging.getLogger(__name__)

from .file import ToolFile