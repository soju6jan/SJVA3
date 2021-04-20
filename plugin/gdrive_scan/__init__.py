import os, sys
from framework import app
try:
    import oauth2client
except ImportError:
    try:
        os.system("{} install oauth2client".format(app.config['config']['pip']))
        import oauth2client
    except:
        pass
try:
    from apiclient.discovery import build
except ImportError:
    try:
        os.system("{} install google-api-python-client".format(app.config['config']['pip']))
        from apiclient.discovery import build
    except:
        pass

from .plugin import blueprint, menu, plugin_load, plugin_unload
from .logic import Logic