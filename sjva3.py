# -*- coding: utf-8 -*-
#########################################################
import os, sys, platform, traceback, shutil
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
print('[SJVA3] sys.path : %s' % sys.path)
print('[SJVA3] sys.argv : %s' % sys.argv)

def prepare_starting():
    try:
        from gevent import monkey;monkey.patch_all()
        print('[SJVA3] gevent mokey patch!!')
    except:
        print('[SJVA3] gevent not installed!!')
    ######################################

    try:
        av_agent = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'custom', 'av_agent')
        if os.path.exists(av_agent):
            shutil.rmtree(av_agent)
    except Exception as exception:
        print('Exception:%s' % exception)
        print(traceback.format_exc())



def start_app():
    import framework
    import system
    
    app = framework.app
    celery = framework.celery
   
    for i in range(10):
        try:
            framework.socketio.run(app, host='0.0.0.0', port=app.config['config']['port'])
            print('EXIT CODE : %s' % framework.exit_code)
            if framework.exit_code != -1:
                sys.exit(framework.exit_code)
                break
            else:
                print('framework.exit_code is -1')
            break
        except Exception as exception:
            print(str(exception))
            import time
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

