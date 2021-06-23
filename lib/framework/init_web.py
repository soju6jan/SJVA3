# -*- coding: utf-8 -*-
###############################################################
#  웹 메뉴
###############################################################
import re
from flask_login import current_user

def get_menu(full_query):
    match = re.compile(r'\/(?P<menu>.*?)\/manual\/(?P<sub2>.*?)($|\?)').match(full_query)
    if match:
        return match.group('menu'), 'manual', match.group('sub2')

    match = re.compile(r'\/(?P<menu>.*?)\/(?P<sub>.*?)\/(?P<sub2>.*?)($|\/|\?)').match(full_query)
    if match:
        return match.group('menu'), match.group('sub'), match.group('sub2')

    match = re.compile(r'\/(?P<menu>.*?)\/(?P<sub>.*?)($|\/|\?)').match(full_query)
    if match: 
        return match.group('menu'), match.group('sub'), None

    match = re.compile(r'\/(?P<menu>.*?)($|\/|\?)').match(full_query)
    if match:
        return match.group('menu'), None , None
    return 'home', None, None



def get_theme():
    
    theme_list = {
        'Default' : 56,
        'Cerulean' : 56,
        'Cosmo' : 54,
        'Cyborg' : 54,
        'Darkly' : 70,
        'Flatly' : 70,
        'Journal' : 56,
        'Litera' : 57,
        'Lumen' : 56,
        'Lux' : 88,
        'Materia' : 80,
        'Minty' : 56,
        'Morph' : 56,
        'Pulse' : 75,
        'Quartz' : 92,
        'Sandstone' : 53,
        'Simplex' : 67,
        'Sketchy' : 56,
        'Slate' : 53,
        'Solar' : 56,
        'Spacelab' : 58,
        'Superhero' : 48,
        'United' : 56,
        'Vapor' : 56,
        'Yeti' : 54,
        'Zephyr' : 68,
    }
    from system.model import ModelSetting as SystemModelSetting
    theme = SystemModelSetting.get('theme')
    return [theme, theme_list[theme]]

def get_login_status():
    if current_user is None:
        return False
    return current_user.is_authenticated

def get_web_title():
    try:
        from system.model import ModelSetting as SystemModelSetting
        return SystemModelSetting.get('web_title')
    except:
        return 'SJ Video Assitant'


def show_menu():
    from flask import request
    from system.model import ModelSetting as SystemModelSetting
    if SystemModelSetting.get_bool('hide_menu'):
        if request.full_path.find('/login') != -1:
            return False
    return True

def is_https():
    from system.model import ModelSetting as SystemModelSetting
    return (SystemModelSetting.get('ddns').find('https://') != -1)


def jinja_initialize(app):
    from .menu import get_menu_map, get_plugin_menu
    app.jinja_env.globals.update(get_menu=get_menu)
    app.jinja_env.globals.update(get_theme=get_theme)
    app.jinja_env.globals.update(get_menu_map=get_menu_map)
    app.jinja_env.globals.update(get_login_status=get_login_status)
    app.jinja_env.globals.update(get_web_title=get_web_title)
    app.jinja_env.globals.update(get_plugin_menu=get_plugin_menu)
    app.jinja_env.globals.update(show_menu=show_menu)
    app.jinja_env.globals.update(is_https=is_https)
    app.jinja_env.filters['get_menu'] = get_menu
    app.jinja_env.filters['get_theme'] = get_theme
    app.jinja_env.filters['get_menu_map'] = get_menu_map
    app.jinja_env.filters['get_login_status'] = get_login_status
    app.jinja_env.filters['get_web_title'] = get_web_title
    app.jinja_env.filters['get_plugin_menu'] = get_plugin_menu
    app.jinja_env.filters['show_menu'] = show_menu
    app.jinja_env.filters['is_https'] = is_https

    app.jinja_env.add_extension('jinja2.ext.loopcontrols')
