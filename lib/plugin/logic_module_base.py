# -*- coding: utf-8 -*-
import os

class LogicModuleBase(object):
    name = None
    db_default = None
    P = None
    scheduler_desc = None
    first_menu = None
    socketio_list = None

    def __init__(self, P, first_menu, scheduler_desc=None):
        self.P = P
        self.scheduler_desc = scheduler_desc
        self.first_menu = first_menu

    def process_menu(self, sub):
        pass

    def process_ajax(self, sub, req):
        pass
    
    def process_api(self, sub, req):
        pass

    def process_normal(self, sub, req):
        pass

    def scheduler_function():
        pass

    def reset_db(self):
        pass

    def plugin_load(self):
        pass
    
    def plugin_unload(self):
        pass
    
    def setting_save_after(self):
        pass

    def process_telegram_data(self, data, target=None):
        pass

    def migration(self):
        pass
    
    #################################################################
    def get_scheduler_desc(self):
        return self.scheduler_desc 

    def get_scheduler_interval(self):
        if self.P is not None and self.P.ModelSetting is not None and self.name is not None:
            return self.P.ModelSetting.get('{module_name}_interval'.format(module_name=self.name))

    def get_first_menu(self):
        return self.first_menu

    def get_scheduler_name(self):
        return '%s_%s' % (self.P.package_name, self.name)

    def dump(self, data):
        if type(data) in [type({}), type([])]:
            import json
            return '\n' + json.dumps(data, indent=4, ensure_ascii=False)
        else:
            return str(data)
