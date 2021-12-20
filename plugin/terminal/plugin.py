import os, traceback
from flask import Blueprint
from framework import get_logger
from plugin import get_model_setting, Logic, default_route, PluginUtil

class P(object):
    package_name = __name__.split('.')[0]
    logger = get_logger(package_name)
    blueprint = Blueprint(package_name, package_name, url_prefix=f'/{package_name}', template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    plugin_unload = None
    plugin_load = None

from .logic_terminal import LogicTerminal
P.plugin_unload = LogicTerminal.plugin_unload