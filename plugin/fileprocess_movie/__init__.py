import os, sys
from framework import app
try:
    from guessit import guessit
except:
    try:
        os.system("{} install guessit".format(app.config['config']['pip']))
        from guessit import guessit
    except:
        pass

from .plugin import blueprint, menu, plugin_load, plugin_unload
from .logic import Logic
from .logic_movie import LogicMovie


