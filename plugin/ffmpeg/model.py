# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
from datetime import datetime
import json

# third-party
from sqlalchemy import or_, and_, func, not_
from sqlalchemy.orm import backref

# sjva 공용
from framework import db, app, path_data
from framework.util import Util

# 패키지
from .plugin import logger, package_name
#########################################################
app.config['SQLALCHEMY_BINDS'][package_name] = 'sqlite:///%s' % (os.path.join(path_data, 'db', '%s.db' % package_name))
from plugin import get_model_setting
ModelSetting = get_model_setting(package_name, logger)

