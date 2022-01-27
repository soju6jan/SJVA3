try:
    import yaml
    a = yaml.FullLoader
except:
    from framework import app
    import os
    try: os.system(f"{app.config['config']['pip']} install --upgrade pyyaml")
    except: pass

import os, sys, traceback, json
from framework import path_data
from flask import request, render_template, redirect, jsonify
from .plugin import logger


class SystemLogicTerminal(object):
    yaml_path = os.path.join(path_data, 'db', 'terminal.yaml')
    
    @classmethod
    def process_ajax(cls, sub, req):
        logger.error(sub)
        logger.error(req)
        try:
            if sub == 'get_info':
               ret = cls.get_info()
            elif sub == 'run':
                data = cls.get_info()
                idx = int(req.form['index'])
                from terminal.logic_terminal import LogicTerminal
                LogicTerminal.wait_input(data['commands'][idx]['command'])
                return jsonify({'ret':'success'})
            return jsonify(ret)
        except Exception as e: 
            logger.error(f'Exception: {str(e)}')
            logger.error(traceback.format_exc())

    @classmethod
    def get_info(cls):
        if os.path.exists(cls.yaml_path) == False:
            with open(cls.yaml_path, 'w', encoding='utf8') as f:
                f.write(yaml_templete)
        with open(cls.yaml_path) as f:
            info = yaml.load(f, Loader=yaml.FullLoader)
        return info




yaml_templete = '''

commands: 
  - title: SJVA 데이터 폴더별 크기 확인
    command: |
      cd ./data
      du -h -d 1

  - title: SJVA 도커 재시작
    command: |
      ssh -i MY.pem ubuntu@172.17.0.1
      sudo docker restart sjva

'''