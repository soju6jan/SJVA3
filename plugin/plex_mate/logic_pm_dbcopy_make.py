# -*- coding: utf-8 -*-
#########################################################
# python
import os, sys, traceback, re, json, threading, time, shutil, platform
from datetime import datetime
# third-party
import requests, xmltodict
from flask import request, render_template, jsonify, redirect
# sjva 공용
from framework import db, scheduler, path_data, socketio, SystemModelSetting, app, celery, Util
from plugin import default_route_socketio_sub, LogicSubModuleBase
from tool_base import ToolBaseFile, d, ToolSubprocess
# 패키지
from .plugin import P
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting

from .plex_db import PlexDBHandle
from .plex_web import PlexWebHandle
from .logic_pm_base import LogicPMBase
#########################################################


class LogicPMDbCopyMake(LogicSubModuleBase):


    def __init__(self, P, parent, name):
        super(LogicPMDbCopyMake, self).__init__(P, parent, name)
        self.db_default = {
            f'{self.parent.name}_{self.name}_db_version' : '1',
            f'{self.parent.name}_{self.name}_path_create' : os.path.join(path_data, package_name),
            f'{self.parent.name}_{self.name}_path_section_id' : '',
        }
        

    def process_ajax(self, sub, req):
        try:
            ret = {'ret':'success'}
            if sub == 'command':
                command = req.form['command']
                if command.startswith('start'):
                    logger.warning(req.form['arg1'])
                    logger.warning(req.form['arg2'])
                    newpath = self.start(req.form['arg1'], req.form['arg2'])
                    if newpath is not None:
                        ret['msg'] = f"{newpath}<br>생성하였습니다."
                    else:
                        ret['ret'] = 'warning'
                        ret['msg'] = f"실패하였습니다."
            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
    
    def plugin_load(self):
        if os.path.exists(ModelSetting.get(f'{self.parent.name}_{self.name}_path_create')) == False:
            os.makedirs(ModelSetting.get(f'{self.parent.name}_{self.name}_path_create'))

    #########################################################


    def start(self, folderpath, section_id):
        
        try:
            ModelSetting.set(f'{self.parent.name}_{self.name}_path_create', folderpath)
            section = PlexDBHandle.library_section(section_id)
            logger.warning(d(section))

            
            db_path = ModelSetting.get(f'base_path_db')
            if os.path.exists(db_path):
                basename = os.path.basename(db_path)
                tmp = os.path.splitext(basename)
                newfilename = f"{section['name']}_{section['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{tmp[1]}"
                newpath = os.path.join(ModelSetting.get(f'{self.parent.name}_{self.name}_path_create'), newfilename)
                shutil.copy(db_path, newpath)
            logger.debug(newpath)
            
            query = ''
            if section['section_type'] == 1:
                query += f'''
DELETE FROM metadata_items WHERE not (library_section_id = {section_id} AND metadata_type = 1);'''
            elif section['section_type'] == 2:
                query += f'''
DELETE FROM metadata_items WHERE not (library_section_id = {section_id} AND metadata_type BETWEEN 2 AND 4);'''
            query += f'''
DELETE FROM media_streams WHERE media_item_id not in (SELECT id FROM media_items WHERE library_section_id = {section_id});
DELETE FROM media_parts WHERE media_item_id not in (SELECT id FROM media_items WHERE library_section_id = {section_id});
DELETE FROM media_items WHERE library_section_id is null OR library_section_id != {section_id};
DELETE FROM directories WHERE library_section_id is null OR library_section_id != {section_id};
DELETE FROM section_locations WHERE library_section_id is null OR library_section_id != {section_id};
DELETE FROM library_sections WHERE id is null OR id != {section_id};
DROP TABLE accounts;
DROP TABLE activities;
DROP TABLE blobs;
DROP TABLE cloudsync_files;
DROP TABLE devices;
DROP TABLE external_metadata_items;
DROP TABLE external_metadata_sources;
DROP TABLE fts4_metadata_titles;
DROP TABLE fts4_tag_titles;
DROP TABLE fts4_metadata_titles_icu;
DROP TABLE fts4_tag_titles_icu;
DROP TABLE hub_templates;
DROP TABLE locations;
DROP TABLE hub_templates;
DROP TABLE library_section_permissions;
DROP TABLE library_timeline_entries;
DROP TABLE locatables;
DROP TABLE location_places;
DROP TABLE media_grabs;
DROP TABLE media_item_settings;
DROP TABLE media_metadata_mappings;
DROP TABLE media_part_settings;
DROP TABLE media_provider_resources;
DROP TABLE media_stream_settings;
DROP TABLE media_subscriptions;
DROP TABLE metadata_item_accounts;
DROP TABLE metadata_item_clusterings;
DROP TABLE metadata_item_clusters;
DROP TABLE metadata_item_settings;
DROP TABLE metadata_item_views;
DROP TABLE metadata_relations;
DROP TABLE metadata_subscription_desired_items;
DROP TABLE play_queue_generators;
DROP TABLE play_queue_items;
DROP TABLE play_queues;
DROP TABLE plugin_permissions;
DROP TABLE plugin_prefixes;
DROP TABLE plugins;
DROP TABLE preferences;
DROP TABLE remote_id_translation;
DROP TABLE schema_migrations;
DROP TABLE spellfix_metadata_titles;
DROP TABLE spellfix_tag_titles;
DROP TABLE sqlite_sequence;
DROP TABLE sqlite_stat1;
DROP TABLE statistics_bandwidth;
DROP TABLE statistics_media;
DROP TABLE statistics_resources;
DROP TABLE stream_types;
DROP TABLE sync_schema_versions;
DROP TABLE synced_ancestor_items;
DROP TABLE synced_library_sections;
DROP TABLE synced_metadata_items;
DROP TABLE synced_play_queue_generators;
DROP TABLE synchronization_files;
DROP TABLE taggings;
DROP TABLE tags;
DROP TABLE versioned_metadata_items;
DROP TABLE view_settings;
DROP INDEX index_directories_on_deleted_at;
DROP INDEX index_directories_on_parent_directory_id;
DROP INDEX index_directories_on_path;
DROP INDEX index_media_items_on_begins_at;
DROP INDEX index_media_items_on_channel_id;
DROP INDEX index_media_items_on_channel_id_and_begins_at;
DROP INDEX index_media_items_on_deleted_at;
DROP INDEX index_media_items_on_ends_at;
DROP INDEX index_media_items_on_library_section_id;
DROP INDEX index_media_items_on_media_analysis_version;
DROP INDEX index_media_items_on_metadata_item_id;
DROP INDEX index_media_parts_on_deleted_at;
DROP INDEX index_media_parts_on_directory_id;
DROP INDEX index_media_parts_on_file;
DROP INDEX index_media_parts_on_hash;
DROP INDEX index_media_parts_on_media_item_id;
DROP INDEX index_media_parts_on_size;
DROP INDEX index_media_streams_on_language;
DROP INDEX index_media_streams_on_media_item_id;
DROP INDEX index_media_streams_on_media_part_id;
DROP INDEX index_metadata_items_on_absolute_index;
DROP INDEX index_metadata_items_on_added_at;
DROP INDEX index_metadata_items_on_changed_at;
DROP INDEX index_metadata_items_on_created_at;
DROP INDEX index_metadata_items_on_deleted_at;
DROP INDEX index_metadata_items_on_guid;
DROP INDEX index_metadata_items_on_hash;
DROP INDEX index_metadata_items_on_index;
DROP INDEX index_metadata_items_on_library_section_id;
DROP INDEX index_metadata_items_on_library_section_id_and_metadata_type_and_added_at;
DROP INDEX index_metadata_items_on_metadata_type;
DROP INDEX index_metadata_items_on_original_title;
DROP INDEX index_metadata_items_on_originally_available_at;
DROP INDEX index_metadata_items_on_parent_id;
DROP INDEX index_metadata_items_on_remote;
DROP INDEX index_metadata_items_on_resources_changed_at;
DROP INDEX index_metadata_items_on_title;
DROP INDEX index_metadata_items_on_title_sort;
DROP INDEX index_title_sort_icu;
DROP INDEX index_library_sections_on_changed_at;
DROP INDEX index_library_sections_on_name;
DROP INDEX index_library_sections_on_name_sort;
DROP TRIGGER fts4_metadata_titles_after_insert_icu;
DROP TRIGGER fts4_metadata_titles_after_update_icu;
DROP TRIGGER fts4_metadata_titles_before_delete_icu;
DROP TRIGGER fts4_metadata_titles_before_update_icu;
VACUUM;
            '''

            
            PlexDBHandle.execute_query_with_db_filepath(query, newpath)

            return newpath
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
        return