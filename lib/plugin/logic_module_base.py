# -*- coding: utf-8 -*-
import os

class LogicModuleBase(object):
    db_default = None
 
    def __init__(self, P, first_menu, scheduler_desc=None):
        self.P = P
        self.scheduler_desc = scheduler_desc
        self.first_menu = first_menu
        self.name = None
        self.socketio_list = None
        self.sub_list = None


    def process_menu(self, sub):
        pass

    def process_ajax(self, sub, req):
        pass
    
    def process_api(self, sub, req):
        pass

    def process_normal(self, sub, req):
        pass

    def scheduler_function(self):
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





class LogicSubModuleBase(object):
    db_default = None

    def __init__(self, P, parent, name, scheduler_desc=None):
        self.P = P
        self.parent = parent
        self.name = name
        self.scheduler_desc = scheduler_desc
        self.socketio_list = None


    def process_ajax(self, sub, req):
        pass

    def scheduler_function(self):
        pass
    
    def plugin_load(self):
        pass
    
    def plugin_unload(self):
        pass


    def get_scheduler_desc(self):
        return self.scheduler_desc 
    
    def get_scheduler_interval(self):
        if self.P is not None and self.P.ModelSetting is not None and self.parent.name is not None and self.name is not None:
            return self.P.ModelSetting.get(f'{self.parent.name}_{self.name}_interval')

    def get_scheduler_name(self):
        return f'{self.P.package_name}_{self.parent.name}_{self.name}'









    
    
    def process_api(self, sub, req):
        pass

    def process_normal(self, sub, req):
        pass

    

    def reset_db(self):
        pass

    
    
    def setting_save_after(self):
        pass

    def process_telegram_data(self, data, target=None):
        pass

    def migration(self):
        pass
    
    #################################################################
    

    def process_menu(self, sub):
        pass

