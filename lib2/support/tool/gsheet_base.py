import os, sys, traceback

import oauth2client
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client import tools
from oauth2client.client import flow_from_clientsecrets
import gspread, time
from gspread_formatting  import cellFormat, textFormat, color, format_cell_range

from support.base import get_logger, d

logger = get_logger()




        
class GoogleSheetBase:
        
    current_flow = None

    color_format = {
        'green' : cellFormat(
            backgroundColor=color(0, 1, 0), #set it to yellow
            textFormat=textFormat(foregroundColor=color(0, 0, 0)),
        ),
        'yellow' : cellFormat(
            backgroundColor=color(1, 1, 0), #set it to yellow
            textFormat=textFormat(foregroundColor=color(0, 0, 0)),
        ),
        'white' : cellFormat(
            backgroundColor=color(1, 1, 1), #set it to yellow
            textFormat=textFormat(foregroundColor=color(0, 0, 0)),
        )
    }


    def __init__(self, doc_id, credentials_filepath, tab_index, unique_header):
        self.credentials_filepath = credentials_filepath
        self.credentials = self.get_credentials()
        self.doc_id = doc_id
        doc_url = f'https://docs.google.com/spreadsheets/d/{doc_id}'
        gsp = gspread.authorize(self.credentials)
        doc = gsp.open_by_url(doc_url)
        self.ws = doc.get_worksheet(tab_index)
        self.header_info = None
        self.header_info_reverse = None
        self.unique_header = unique_header


    def get_credentials(self, project_filepath=None):
        if os.path.exists(self.credentials_filepath) == False:
            url = self.__make_token_cli(project_filepath)
            logger.debug(f"Auth URL : {url}")
            code = input("Input Code : ")
            self.__save_token(self.credentials_filepath, code)

        store = Storage(self.credentials_filepath)
        credentials = store.get()
        if not credentials or credentials.invalid:
            logger.warning('credentials error')
            #flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
            #creds = tools.run_flow(flow, store)
            os.remove(self.credentials_filepath)
            return self.get_credentials(self.credentials_filepath)
        return credentials
    
    
    def __make_token_cli(self, project_filepath):
        try:
            if project_filepath == None:
                project_filepath = os.path.join(os.path.dirname(__file__), 'cs.json')
            self.current_flow  = flow_from_clientsecrets(
                project_filepath,  # downloaded file
                'https://www.googleapis.com/auth/drive',  # scope
                redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            return self.current_flow.step1_get_authorize_url()
        except Exception as e:
            logger.error(f"Exception: {e}")
            logger.error(traceback.format_exc())


    def __save_token(self, credentials_filepath, code):
        try:
            credentials = self.current_flow.step2_exchange(code)
            storage = Storage(credentials_filepath)
            storage.put(credentials)
            return True
        except Exception as e:
            logger.error(f"Exception: {e}")
            logger.error(traceback.format_exc())
            return False
    

    def get_sheet_data(self):
        tmp = self.ws.get_all_values()#[:-1]
        self.set_sheet_header(tmp[0])
        rows = tmp[1:]
        ret = []
        for row in rows:
            item = {}
            for idx, col in enumerate(row):
                item[self.header_info_reverse[idx+1]] = col
            ret.append(item)
        return ret


    def set_sheet_header(self, row):
        self.header_info = {}
        self.header_info_reverse = {}
        for idx, col in enumerate(row):
            self.header_info[col] = idx + 1
            self.header_info_reverse[idx+1] = col
        logger.debug(self.header_info)

    
    def find_row_index(self, total_data, data):
        find_row_index = -1
        #find = False
        #data['IDX'] = len(total_data)+1
        for idx, item in enumerate(total_data):
            if item[self.unique_header] == str(data[self.unique_header]):
                #find = True
                find_row_index = idx
                #data['IDX'] = find_row_index + 1
                break
        
        if find_row_index == -1:
            data['IDX'] = len(total_data)+1

        return find_row_index
    

    def sleep(self):
        time.sleep(0.5)

    def sleep_exception(self):
        time.sleep(10)

    
    def after_update_cell(self, sheet_row_index, sheet_col_index, key, value, old_value):
        pass
    

    def set_color(self, sheet_row, sheet_col1, sheet_col2, color):
        format_cell_range(self.ws, gspread.utils.rowcol_to_a1(sheet_row,sheet_col1)+':' + gspread.utils.rowcol_to_a1(sheet_row,sheet_col2), color)

    def write_data(self, total_data, data):
        find_row_index = self.find_row_index(total_data, data)

        write_count = 0
        for key, value in data.items():
            if key.startswith('_'):
                continue
            if value == None:
                continue
            if key not in self.header_info:
                continue
            while True:
                try:
                    if find_row_index != -1 and str(total_data[find_row_index][key]) != str(value):
                        logger.warning(f"업데이트 : {key} {total_data[find_row_index][key]} ==> {value}")
                        self.ws.update_cell(find_row_index+2, self.header_info[key], value)
                        self.after_update_cell(find_row_index+2, self.header_info[key], key, value, total_data[find_row_index][key])
                        write_count += 1
                        self.sleep()
                    elif find_row_index == -1 and value != '':
                        logger.warning(f"추가 : {key} {value}")
                        self.ws.update_cell(len(total_data)+2, self.header_info[key], value)
                        self.after_update_cell(len(total_data)+2, self.header_info[key], key, value, None)
                        write_count += 1
                        self.sleep()
                    break
                except gspread.exceptions.APIError:
                    self.sleep_exception()
                except Exception as exception: 
                    logger.error(f"{key} - {value}")
                    logger.error('Exception:%s', exception)
                    logger.error(traceback.format_exc())
                    logger.error(self.header_info)
                    self.sleep_exception()
          
        if find_row_index == -1:
            total_data.append(data)
        else:
            total_data[find_row_index] = data
        return write_count
