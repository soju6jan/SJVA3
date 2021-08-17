# -*- coding: utf-8 -*-
#########################################################
# python
import os
from datetime import datetime
# third-party

# sjva 공용
from framework import db, app, path_data

# 패키지
from .plugin import logger, package_name
#########################################################
app.config['SQLALCHEMY_BINDS'][package_name] = 'sqlite:///%s' % (os.path.join(path_data, 'db', '%s.db' % package_name))
from plugin import get_model_setting
ModelSetting = get_model_setting(package_name, logger)
