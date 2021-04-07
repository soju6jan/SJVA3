# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import logging
import platform
import time

# third-party
from flask import Blueprint, request, Response, send_file, render_template, redirect, jsonify


# sjva 공용
from framework.logger import get_logger
from framework import app, path_app_root, path_data, scheduler
from framework.job import Job
from tool_base import ToolBaseNotify
# 패키지
from .plugin import logger, package_name
from .model import ModelSetting


class SystemLogicTelegramBot(object):
    @staticmethod
    def process_ajax(sub, req):
        try:
            if sub == 'telegram_test':
                ret = ToolBaseNotify.send_telegram_message(req.form['text'], bot_token=req.form['bot_token'], chat_id=req.form['chat_id'])
                return jsonify(ret)
            elif sub == 'discord_test':
                ret = ToolBaseNotify.send_discord_message(req.form['text'], webhook_url=req.form['url'])
                return jsonify(ret)
            elif sub == 'advanced_test':
                ret = ToolBaseNotify.send_advanced_message(req.form['text'], policy=req.form['policy'], message_id=req.form['message_id'])
                return jsonify(ret)
            elif sub == 'scheduler':
                go = request.form['scheduler']
                logger.debug('scheduler :%s', go)
                if go == 'true':
                    SystemLogicTelegramBot.scheduler_start()
                else:
                    SystemLogicTelegramBot.scheduler_stop()
                return jsonify(go)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return jsonify('exception')

    @staticmethod
    def plugin_load():
        try:
            if app.config['config']['run_by_worker']:
                return
                
            if ModelSetting.get_bool('telegram_bot_auto_start'):
                SystemLogicTelegramBot.scheduler_start()
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def scheduler_start():
        try:
            interval = 60*24
            job = Job(package_name, '%s_telegram_bot' % (package_name), 9999, SystemLogicTelegramBot.scheduler_function, u"시스템 - 텔레그램 봇", False)
            scheduler.add_job_instance(job)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())

    @staticmethod
    def scheduler_function():
        try:
            bot_token = ModelSetting.get('telegram_bot_token')
            from framework.common.telegram_bot import TelegramBot
            TelegramBot.start(bot_token)
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())