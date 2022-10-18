import os, sys, platform, traceback, shutil, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
sys.path.insert(1, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib2'))
if platform.system() == 'Linux':
    if (platform.platform().find('86') == -1 and platform.platform().find('64') == -1) or platform.platform().find('arch') != -1 or platform.platform().find('arm') != -1:
        sys.path.insert(2, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib', 'sc', 'LinuxArm'))
    else:
        sys.path.insert(2, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib', 'sc', 'Linux'))
if platform.system() == 'Windows':
    sys.path.insert(2, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib', 'sc', 'Windows'))


print('[SJVA3] sys.path : %s' % sys.path)
print('[SJVA3] sys.argv : %s' % sys.argv)

def prepare_starting():
    try:
        from gevent import monkey;monkey.patch_all()
        print('[SJVA3] gevent mokey patch!!')
        sys.getfilesystemencoding = lambda: 'UTF-8'
    except:
        print('[SJVA3] gevent not installed!!')
    ######################################

    try:
        """
        remove_plugins = ['av_agent', 'aria2', 'kthoom', 'synoindex', 'nginx', 'launcher_calibre_web', 'launcher_gateone', 'launcher_greentunnel', 'launcher_guacamole', 'launcher_ivViewer', 'launcher_tautulli', 'launcher_torrssen2', 'launcher_xteve']
        for plugin in remove_plugins:
            plugin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'custom', plugin)
            plugin_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'db', f"{plugin}.db")
            if os.path.exists(plugin_path):
                shutil.rmtree(plugin_path)
            if os.path.exists(plugin_db_path):
                os.remove(plugin_db_path)
        """
        remove_plugins = ['klive', 'klive_plus']
        for plugin in remove_plugins:
            try:
                plugin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'custom', plugin)
                if os.path.exists(plugin_path):
                    shutil.rmtree(os.path.join(plugin_path, '.git'))
            except Exception as exception:
                print('Exception:%s' % exception)
                print(traceback.format_exc())

    except Exception as exception:
        print('Exception:%s' % exception)
        print(traceback.format_exc())



def start_app():
    import framework
    import system
    
    app = framework.app
    celery = framework.celery
    host = '0.0.0.0'
    for i in range(10):
        try:
            framework.socketio.run(app, host=host, port=app.config['config']['port'])
            print('EXIT CODE : %s' % framework.exit_code)
            # 2021-05-18
            if app.config['config']['running_type'] in ['termux', 'entware']:
                os._exit(framework.exit_code)
            else:
                if framework.exit_code != -1:
                    sys.exit(framework.exit_code)
                else:
                    print('framework.exit_code is -1')
            break
        except Exception as exception:
            print(f'SJVA Start ERROR : {str(exception)}')
            host = '127.0.0.1'
            time.sleep(10*i)
            continue
        except KeyboardInterrupt:
            print('KeyboardInterrupt !!')
    print('start_app() end')


def process_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, help=u'If this value is set, ignore the DB value and use it')
    parser.add_argument('--use_gevent', choices=['true', 'false'], default='true', help=u'If true, use gevent. (WCGI, scheduler, socketio)')
    parser.add_argument('--use_celery', choices=['true', 'false'], default='true', help=u'If true, use celery.\nThis value is set to False by force on Windows10')
    parser.add_argument('--repeat', default=0, type=int, help=u'Do not set. This value is set by automatic')
    args = parser.parse_args()
    args.use_gevent = (args.use_gevent == 'true')
    args.use_celery = (args.use_celery == 'true')
    print('[SJVA3] args : %s' % args)
    return args


if __name__ == '__main__':
    try:
        # --help 때문에 여기 있다. 실제 args 처리는 Framework에서 한다 ;;
        process_args()
        prepare_starting()
        start_app()
    except Exception as exception:
        print(str(exception))
        print(traceback.format_exc())
        
if sys.argv[0] != 'sjva3.py':
    import framework
    import system
    app = framework.app
    celery = framework.celery

