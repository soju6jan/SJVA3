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
from framework import path_app_root, path_data
from tool_base import ToolBaseNotify
# 패키지
from .plugin import logger, package_name
from .model import ModelSetting


class SystemLogicNotify(object):
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
        except Exception as exception: 
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return jsonify('exception')

