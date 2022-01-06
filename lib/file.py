import os, traceback, io, re, json, codecs
from . import logger

class ToolFile(object):

    @classmethod
    def read(cls, filepath, mode='r'):
        try:
            import codecs
            ifp = codecs.open(filepath, mode, encoding='utf8')
            data = ifp.read()
            ifp.close()
            if isinstance(data, bytes):
                data = data.decode('utf-8') 
            return data
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            

    @classmethod
    def download(cls, url, filepath):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
                'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Connection': 'Keep-Alive',
            }

            import requests
            with open(filepath, "wb") as file_is:   # open in binary mode
                response = requests.get(url, headers=headers)               # get request
                file_is.write(response.content)      # write to file
                return True
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())   
        return False


    @classmethod
    def write(cls, data, filepath, mode='w'):
        try:
            import codecs
            ofp = codecs.open(filepath, mode, encoding='utf8')
            if isinstance(data, bytes) and mode == 'w':
                data = data.decode('utf-8') 
            ofp.write(data)
            ofp.close()
            return True
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())
        return False


    @classmethod
    def text_for_filename(cls, text):
        #text = text.replace('/', '')
        # 2021-07-31 X:X
        #text = text.replace(':', ' ')
        text = re.sub('[\\/:*?\"<>|]', ' ', text).strip()
        text = re.sub("\s{2,}", ' ', text)
        return text


    @classmethod
    def size(cls, start_path = '.'):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    @classmethod
    def file_move(cls, source_path, target_dir, target_filename):
        try:
            import time, shutil
            if os.path.exists(target_dir) == False:
                os.makedirs(target_dir)
            target_path = os.path.join(target_dir, target_filename)
            if source_path != target_path:
                if os.path.exists(target_path):
                    tmp = os.path.splitext(target_filename)
                    new_target_filename = f"{tmp[0]} {str(time.time()).split('.')[0]}{tmp[1]}"
                    target_path = os.path.join(target_dir, new_target_filename)
                shutil.move(source_path, target_path)
        except Exception as exception:
            logger.debug('Exception:%s', exception)
            logger.debug(traceback.format_exc())


    @classmethod
    def makezip(cls, zip_path, zip_folder=None, zip_extension='zip', remove_folder=False):
        import zipfile
        try:
            zip_path = zip_path.rstrip('/')
            if zip_folder is None:
                zip_folder = os.path.dirname(zip_path)
            elif zip_folder == 'tmp':
                from framework import path_data
                zip_folder = os.path.join(path_data, 'tmp')
            if os.path.isdir(zip_path):
                zipfilepath = os.path.join(zip_folder, f"{os.path.basename(zip_path)}.{zip_extension}")
                fantasy_zip = zipfile.ZipFile(zipfilepath, 'w')
                for f in os.listdir(zip_path):
                    src = os.path.join(zip_path, f)
                    fantasy_zip.write(src, os.path.basename(src), compress_type = zipfile.ZIP_DEFLATED)
                fantasy_zip.close()
            if remove_folder:
                import shutil
                shutil.rmtree(zip_path)
            return zipfilepath
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
        return

    @classmethod
    def rmtree(cls, folderpath):
        import shutil
        try:
            shutil.rmtree(folderpath)
            return True
        except:
            try:
                os.system("rm -rf '{folderpath}'")
                return True
            except:
                return False
            
                
    @classmethod
    def rmtree2(cls, folderpath):
        import shutil
        try:
            for root, dirs, files in os.walk(folderpath):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    shutil.rmtree(os.path.join(root, name))
        except:
            return False
          
    
    @classmethod
    def write_json(cls, filepath, data):
        try:
            if os.path.exists(os.path.dirname(filepath)) == False:
                os.makedirs(os.path.dirname(filepath))
            with open(filepath, "w", encoding='utf8') as json_file:
                json.dump(data, json_file, indent=4, ensure_ascii=False)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 

    @classmethod
    def read_json(cls, filepath):
        try:
            with open(filepath, "r", encoding='utf8') as json_file:
                data = json.load(json_file)
                return data
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
    

    @classmethod
    def write_file(cls, filename, data):
        try:
            import codecs
            ofp = codecs.open(filename, 'w', encoding='utf8')
            ofp.write(data)
            ofp.close()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 

    @classmethod
    def read_file(cls, filename):
        try:
            ifp = codecs.open(filename, 'r', encoding='utf8')
            data = ifp.read()
            ifp.close()
            return data
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    

    @classmethod
    def makezip_simple(cls, zip_path, zip_extension='cbz', remove_zip_path=True):
        import zipfile, shutil
        try:
            if os.path.exists(zip_path) == False:
                return False
            zipfilepath = os.path.join(os.path.dirname(zip_path), f"{os.path.basename(zip_path)}.{zip_extension}")
            if os.path.exists(zipfilepath):
                return True
            zip = zipfile.ZipFile(zipfilepath, 'w')
            for f in os.listdir(zip_path):
                src = os.path.join(zip_path, f)
                zip.write(src, f, compress_type = zipfile.ZIP_DEFLATED)
            zip.close()
            if remove_zip_path:
                shutil.rmtree(zip_path)
            return zipfilepath
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
        return None
        