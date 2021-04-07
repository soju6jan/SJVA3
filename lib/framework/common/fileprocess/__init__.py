# -*- coding: utf-8 -*-
#from framework.logger import get_logger
#logger = get_logger('framework.common.fileprocess')
from framework import logger

class Vars:
    proxies = None
    
#proxies = None

from .util import remove_small_file_and_move_target, remove_match_ext
from .av import change_filename_censored, change_filename_censored_by_save_original, search, update, dmm_search, dmm_update, javdb_search, javdb_update, uncensored_filename_analyze, test_dmm, test_javdb, is_uncensored


