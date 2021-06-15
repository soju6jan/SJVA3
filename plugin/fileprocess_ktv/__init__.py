# -*- coding: utf-8 -*-
try:
    import yaml
except:
    from framework import app
    import os
    try: os.system(f"{app.config['config']['pip']} install pyyaml")
    except: pass

from .plugin import P
blueprint = P.blueprint
menu = P.menu
plugin_load = P.logic.plugin_load
plugin_unload = P.logic.plugin_unload
plugin_info = P.plugin_info
