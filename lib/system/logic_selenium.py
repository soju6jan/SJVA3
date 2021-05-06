# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import logging
import platform
import time
import base64

# third-party
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify

try:
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
except:
    pass
from io import BytesIO

# sjva 공용
from framework.logger import get_logger
from framework import path_app_root, path_data

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting

#########################################################
#apk --no-cache add --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing firefox
#https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz
#curl -s -L "$url" | tar -xz

class SystemLogicSelenium(object):
    chrome_driver = None
    chrome_driver_list = []
    
    @staticmethod
    def process_ajax(sub, req):
        try:
            if sub == 'selenium_test_go':
                driver = SystemLogicSelenium.get_driver()
                driver.get(req.form['url'])
                return jsonify('success')
            elif sub == 'capture':
                driver = SystemLogicSelenium.get_driver()
                img = Image.open(BytesIO((driver.get_screenshot_as_png())))

                timestamp = time.time()
                timestamp = str(timestamp).split('.')[0]
                tmp = os.path.join(path_data, 'tmp', '%s.png' % timestamp)
                img.save(tmp)
                from system.model import ModelSetting as SystemModelSetting
                ddns = SystemModelSetting.get('ddns')
                url = '%s/open_file%s' % (ddns, tmp)
                logger.debug(url)
                ret = {}
                ret['ret'] = 'success'
                ret['data'] = url
                return jsonify(ret)
            elif sub == 'full_capture':
                driver = SystemLogicSelenium.get_driver()
                img = SystemLogicSelenium.full_screenshot(driver)

                timestamp = time.time()
                timestamp = str(timestamp).split('.')[0]
                tmp = os.path.join(path_data, 'tmp', '%s.png' % timestamp)
                img.save(tmp)
                return send_file(tmp, mimetype='image/png')
            elif sub == 'cookie':
                driver = SystemLogicSelenium.get_driver()
                data = driver.get_cookies()
                return jsonify(data)
            elif sub == 'daum_capcha':
                daum_capcha = req.form['daum_capcha']
                driver = SystemLogicSelenium.get_driver()
                #driver.find_element_by_xpath('//div[@class="secret_viewer"]/p/img').screenshot("captcha.png")
                driver.find_element_by_xpath('//input[@id="answer"]').send_keys(daum_capcha)
                driver.find_element_by_xpath('//input[@value="%s"]' % u'확인').click()
                return jsonify({'ret':'success'})
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return jsonify('exception')

    @staticmethod
    def get_pagesoruce_by_selenium(url, wait_xpath, retry=True):
        try:
            logger.debug('get_pagesoruce_by_selenium:%s %s', url, wait_xpath)
            driver = SystemLogicSelenium.get_driver()
            #logger.debug('driver : %s', driver)
            driver.get(url)
            
            WebDriverWait(driver, 30).until(lambda driver: driver.find_element_by_xpath(wait_xpath))
            #import time
            #driver.save_screenshot('%s.png' % time.time())
            logger.debug('return page_source')    
            return driver.page_source
        except Exception as exception: 
            #logger.debug(driver.page_source)
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
            SystemLogicSelenium.chrome_driver = None
            if retry:
                return SystemLogicSelenium.get_pagesoruce_by_selenium(url, wait_xpath, retry=False)

    # 1회성 
    @staticmethod
    def get_driver(chrome_options=None):
        try:
            if SystemLogicSelenium.chrome_driver is None:
                SystemLogicSelenium.chrome_driver = SystemLogicSelenium.inner_create_driver(chrome_options)
            return SystemLogicSelenium.chrome_driver
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 

    # 플러그인이 점유
    @staticmethod
    def create_driver(chrome_options=None):
        try:
            driver = SystemLogicSelenium.inner_create_driver(chrome_options)
            if driver is not None:
                SystemLogicSelenium.chrome_driver_list.append(driver)
                return driver
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 

    @staticmethod
    def close_driver():
        try:
            if SystemLogicSelenium.chrome_driver is not None:
                SystemLogicSelenium.chrome_driver.quit()
                SystemLogicSelenium.chrome_driver = None
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 
    

    @staticmethod
    def inner_create_driver(chrome_options):
        try:
            driver = None
            remote_url = ModelSetting.get('selenium_remote_url')
            if remote_url.endswith('/wd/hub/'):
                remote_url = remote_url[:-1]
            if remote_url != '':
                if chrome_options is None:
                    chrome_options = webdriver.ChromeOptions()
                    tmp = ModelSetting.get_list('selenium_remote_default_option')
                    for t in tmp:
                        chrome_options.add_argument(t)
                driver = webdriver.Remote(command_executor=remote_url, desired_capabilities=chrome_options.to_capabilities())
                driver.set_window_size(1920, 1080)
                logger.debug('Using Remote :%s', driver)
            else:
                path_chrome = os.path.join(path_app_root, 'bin', platform.system(), 'chromedriver')
                if platform.system() == 'Windows':
                    path_chrome += '.exe'
                if chrome_options is None:
                    chrome_options = webdriver.ChromeOptions()
                    tmp = ModelSetting.get_list('selenium_binary_default_option')
                    for t in tmp:
                        chrome_options.add_argument(t)
                driver = webdriver.Chrome(path_chrome, chrome_options=chrome_options)
                logger.debug('Using local bin :%s', driver)
            if driver is not None:
                return driver
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 


    @staticmethod
    def plugin_unload():
        try:
            logger.debug(SystemLogicSelenium.chrome_driver)
            if SystemLogicSelenium.chrome_driver is not None:
                SystemLogicSelenium.chrome_driver.quit()
                logger.debug(SystemLogicSelenium.chrome_driver)

            for tmp in SystemLogicSelenium.chrome_driver_list:
                if tmp is not None:
                    tmp.quit()

        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 

    @staticmethod
    def get_text_excluding_children(driver, element):
        return driver.execute_script("""
        return jQuery(arguments[0]).contents().filter(function() {
            return this.nodeType == Node.TEXT_NODE;
        }).text();
        """, element)

    @staticmethod
    def full_screenshot(driver, low_offset = 0):
        try:
            # initiate value
            #save_path = save_path + '.png' if save_path[-4::] != '.png' else save_path
            img_li = []  # to store image fragment
            offset = 0  # where to start

            # js to get height
            height = driver.execute_script('return Math.max('
                                        'document.documentElement.clientHeight, window.innerHeight);')
            #height = height - low_offset
            # js to get the maximum scroll height
            # Ref--> https://stackoverflow.com/questions/17688595/finding-the-maximum-scroll-position-of-a-page
            max_window_height = driver.execute_script('return Math.max('
                                                    'document.body.scrollHeight, '
                                                    'document.body.offsetHeight, '
                                                    'document.documentElement.clientHeight, '
                                                    'document.documentElement.scrollHeight, '
                                                    'document.documentElement.offsetHeight);')

            # looping from top to bottom, append to img list
            # Ref--> https://gist.github.com/fabtho/13e4a2e7cfbfde671b8fa81bbe9359fb
            
            while offset < max_window_height:

                # Scroll to height
                driver.execute_script("""
                window.scrollTo(0, arguments[0]);
                """, offset)
                img = Image.open(BytesIO((driver.get_screenshot_as_png())))

                if low_offset != 0:
                    img = img.crop((0, 0, img.width, img.height-low_offset)) # defines crop points

                img_li.append(img)
                offset += height
                logger.debug('offset : %s / %s', offset, max_window_height)

            # Stitch image into one
            # Set up the full screen frame
            img_frame_height = sum([img_frag.size[1] for img_frag in img_li])
            img_frame = Image.new('RGB', (img_li[0].size[0], img_frame_height))
            offset = 0
            for img_frag in img_li:
                img_frame.paste(img_frag, (0, offset))
                offset += img_frag.size[1]
                logger.debug('paste offset : %s ', offset)
            #img_frame.save(save_path)
            #return 
            return img_frame
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc()) 

    @staticmethod
    def remove_element(driver, element):
        driver.execute_script("""
        var element = arguments[0];
        element.parentNode.removeChild(element);
        """, element)



    ######################################################################
    @staticmethod
    def __get_downloaded_files(driver=None):
        if driver is None:
            driver = SystemLogicSelenium.get_driver()
        if not driver.current_url.startswith("chrome://downloads"):
            driver.get("chrome://downloads/")
        #driver.implicitly_wait(4)
        return driver.execute_script( \
            "return downloads.Manager.get().items_   "
            "  .filter(e => e.state === 'COMPLETE')  "
            "  .map(e => e.filePath || e.file_path); " )



    @staticmethod
    def get_file_content(path, driver=None):
        if driver is None:
            driver = SystemLogicSelenium.get_driver()

        elem = driver.execute_script( \
            "var input = window.document.createElement('INPUT'); "
            "input.setAttribute('type', 'file'); "
            "input.hidden = true; "
            "input.onchange = function (e) { e.stopPropagation() }; "
            "return window.document.documentElement.appendChild(input); " )

        elem._execute('sendKeysToElement', {'value': [ path ], 'text': path})

        result = driver.execute_async_script( \
            "var input = arguments[0], callback = arguments[1]; "
            "var reader = new FileReader(); "
            "reader.onload = function (ev) { callback(reader.result) }; "
            "reader.onerror = function (ex) { callback(ex.message) }; "
            "reader.readAsDataURL(input.files[0]); "
            "input.remove(); "
            , elem)

        if not result.startswith('data:') :
            raise Exception("Failed to get file content: %s" % result)

        return base64.b64decode(result[result.find('base64,') + 7:])


    @staticmethod
    def get_downloaded_files(driver=None):
        if driver is None:
            driver = SystemLogicSelenium.get_driver()

        #files = WebDriverWait(driver, 20, 1).until(SystemLogicSelenium.__get_downloaded_files)
        files = SystemLogicSelenium.__get_downloaded_files()
        return files
    
    @staticmethod
    def waitUntilDownloadCompleted(maxTime=600, driver=None):
        if driver is None:
            driver = SystemLogicSelenium.get_driver()
        driver.execute_script("window.open()")
        # switch to new tab
        driver.switch_to.window(driver.window_handles[-1])
        # navigate to chrome downloads
        driver.get('chrome://downloads')
        # define the endTime
        endTime = time.time() + maxTime
        while True:
            try:
                # get the download percentage
                downloadPercentage = driver.execute_script(
                    "return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('#progress').value")
                # check if downloadPercentage is 100 (otherwise the script will keep waiting)
                if downloadPercentage == 100:
                    # exit the method once it's completed
                    return downloadPercentage
            except:
                pass
            # wait for 1 second before checking the percentage next time
            time.sleep(1)
            # exit method if the download not completed with in MaxTime.
            if time.time() > endTime:
                break

"""


driver = webdriver.Chrome(desired_capabilities=capabilities_chrome)
#driver = webdriver.Remote('http://127.0.0.1:5555/wd/hub', capabilities_chrome)

# download a pdf file
driver.get("https://www.mozilla.org/en-US/foundation/documents")
driver.find_element_by_css_selector("[href$='.pdf']").click()

# list all the completed remote files (waits for at least one)
files = WebDriverWait(driver, 20, 1).until(get_downloaded_files)

# get the content of the first file remotely
content = get_file_content(driver, files[0])

# save the content in a local file in the working directory
with open(os.path.basename(files[0]), 'wb') as f:
  f.write(content)


capabilities_chrome = { \
    'browserName': 'chrome',
    # 'proxy': { \
     # 'proxyType': 'manual',
     # 'sslProxy': '50.59.162.78:8088',
     # 'httpProxy': '50.59.162.78:8088'
    # },
    'goog:chromeOptions': { \
      'args': [
      ],
      'prefs': { \
        # 'download.default_directory': "",
        # 'download.directory_upgrade': True,
        'download.prompt_for_download': False,
        'plugins.always_open_pdf_externally': True,
        'safebrowsing_for_trusted_sources_enabled': False
      }
    }
  }
"""