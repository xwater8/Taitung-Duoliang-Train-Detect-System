"""
上傳模組 - 處理圖片上傳至 imgbb 及資料寫入 Google Sheets
"""
import os
import requests
import base64
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time


class ImgbbUploader:
    """imgbb 圖片上傳類別"""
    
    def __init__(self, api_key):
        """
        初始化 imgbb 上傳器
        
        Args:
            api_key: imgbb API Key
        """
        self.api_key = api_key
        self.api_url = "https://api.imgbb.com/1/upload"
    
    def upload_image(self, image_path, max_retries=3):
        """
        上傳圖片至 imgbb
        
        Args:
            image_path: 圖片檔案路徑
            max_retries: 最大重試次數
            
        Returns:
            dict: {'success': bool, 'url': str, 'error': str}
        """
        if not os.path.exists(image_path):
            return {
                'success': False,
                'url': None,
                'error': f'File not found: {image_path}'
            }
        
        # 檢查檔案大小（imgbb 限制 32MB）
        file_size = os.path.getsize(image_path)
        if file_size > 32 * 1024 * 1024:
            return {
                'success': False,
                'url': None,
                'error': f'File size ({file_size / 1024 / 1024:.2f}MB) exceeds 32MB limit'
            }
        
        for attempt in range(max_retries):
            try:
                # 讀取圖片並轉換為 base64
                with open(image_path, 'rb') as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                # 產生圖片名稱
                filename = os.path.basename(image_path)
                name = os.path.splitext(filename)[0]
                
                payload = {
                    'key': self.api_key,
                    'image': image_data,
                    'name': name
                }
                
                response = requests.post(
                    self.api_url,
                    data=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        return {
                            'success': True,
                            'url': data['data']['url'],
                            'error': None
                        }
                    else:
                        return {
                            'success': False,
                            'url': None,
                            'error': f"imgbb API error: {data.get('error', {}).get('message', 'Unknown error')}"
                        }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    if attempt < max_retries - 1:
                        print(f"Upload failed (attempt {attempt + 1}/{max_retries}): {error_msg}")
                        time.sleep(2 ** attempt)  # 指數退避
                        continue
                    return {
                        'success': False,
                        'url': None,
                        'error': error_msg
                    }
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Request exception: {str(e)}"
                if attempt < max_retries - 1:
                    print(f"Upload failed (attempt {attempt + 1}/{max_retries}): {error_msg}")
                    time.sleep(2 ** attempt)
                    continue
                return {
                    'success': False,
                    'url': None,
                    'error': error_msg
                }
            except Exception as e:
                return {
                    'success': False,
                    'url': None,
                    'error': f"Unexpected error: {str(e)}"
                }
        
        return {
            'success': False,
            'url': None,
            'error': 'Max retries exceeded'
        }


class GoogleSheetsWriter:
    """Google Sheets 資料寫入類別"""
    
    def __init__(self, credentials_path, spreadsheet_id, worksheet_name='工作表1'):
        """
        初始化 Google Sheets 寫入器
        
        Args:
            credentials_path: Service Account JSON 金鑰檔案路徑
            spreadsheet_id: Google Sheet ID
            worksheet_name: 工作表名稱
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        self.client = None
        self.worksheet = None
    
    def connect(self):
        """建立連線至 Google Sheets"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scopes
            )
            
            self.client = gspread.authorize(creds)
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            self.worksheet = spreadsheet.worksheet(self.worksheet_name)
            
            return {'success': True, 'error': None}
            
        except FileNotFoundError:
            return {
                'success': False,
                'error': f'Credentials file not found: {self.credentials_path}'
            }
        except gspread.exceptions.SpreadsheetNotFound:
            return {
                'success': False,
                'error': f'Spreadsheet not found: {self.spreadsheet_id}'
            }
        except gspread.exceptions.WorksheetNotFound:
            return {
                'success': False,
                'error': f'Worksheet not found: {self.worksheet_name}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection error: {str(e)}'
            }
    
    def append_row(self, date_str, time_str, imgur_url, note='', max_retries=3):
        """
        新增一列資料至 Google Sheets
        
        Args:
            date_str: 日期字串 (YYYY-MM-DD)
            time_str: 時間字串 (HH:MM:SS)
            imgur_url: imgur 圖片連結
            note: 備註
            max_retries: 最大重試次數
            
        Returns:
            dict: {'success': bool, 'error': str}
        """
        if self.worksheet is None:
            connect_result = self.connect()
            if not connect_result['success']:
                return connect_result
        
        row_data = [date_str, time_str, imgur_url, note]
        
        for attempt in range(max_retries):
            try:
                self.worksheet.append_row(row_data, value_input_option='USER_ENTERED')
                return {'success': True, 'error': None}
                
            except gspread.exceptions.APIError as e:
                error_msg = f"Google Sheets API error: {str(e)}"
                if attempt < max_retries - 1:
                    print(f"Append row failed (attempt {attempt + 1}/{max_retries}): {error_msg}")
                    time.sleep(2 ** attempt)
                    # 重新連線
                    self.connect()
                    continue
                return {'success': False, 'error': error_msg}
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Unexpected error: {str(e)}"
                }
        
        return {
            'success': False,
            'error': 'Max retries exceeded'
        }


class TrainDetectionUploader:
    """整合上傳類別 - 處理火車偵測結果的完整上傳流程"""
    
    def __init__(self, imgbb_api_key, gsheet_credentials_path, gsheet_spreadsheet_id, 
                 gsheet_worksheet_name='工作表1'):
        """
        初始化上傳器
        
        Args:
            imgbb_api_key: imgbb API Key
            gsheet_credentials_path: Google Sheets Service Account 金鑰路徑
            gsheet_spreadsheet_id: Google Sheet ID
            gsheet_worksheet_name: 工作表名稱
        """
        self.imgbb_uploader = ImgbbUploader(imgbb_api_key)
        self.gsheet_writer = GoogleSheetsWriter(
            gsheet_credentials_path,
            gsheet_spreadsheet_id,
            gsheet_worksheet_name
        )
        self.last_upload_time = {}  # 用於去重
    
    def should_upload(self, event_id, min_interval=60):
        """
        檢查是否應該上傳（去重機制）
        
        Args:
            event_id: 事件識別碼（例如：train_event_20260124_123045）
            min_interval: 最小間隔秒數
            
        Returns:
            bool: 是否應該上傳
        """
        current_time = time.time()
        
        if event_id in self.last_upload_time:
            time_diff = current_time - self.last_upload_time[event_id]
            if time_diff < min_interval:
                return False
        
        self.last_upload_time[event_id] = current_time
        return True
    
    def upload_train_event(self, image_path, timestamp=None, note=''):
        """
        上傳火車偵測事件
        
        Args:
            image_path: 火車圖片路徑
            timestamp: 時間戳記（datetime 物件），若為 None 則使用當前時間
            note: 備註
            
        Returns:
            dict: {
                'success': bool,
                'imgur_url': str,
                'sheet_updated': bool,
                'errors': list
            }
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # 產生事件 ID
        event_id = os.path.splitext(os.path.basename(image_path))[0]
        
        # 檢查是否應該上傳（去重）
        if not self.should_upload(event_id):
            return {
                'success': False,
                'image_url': None,
                'sheet_updated': False,
                'errors': ['Duplicate event - skipped to prevent redundant uploads']
            }
        
        errors = []
        image_url = None
        sheet_updated = False
        
        # 步驟 1: 上傳圖片至 imgbb
        print(f"Uploading image to imgbb: {image_path}")
        imgbb_result = self.imgbb_uploader.upload_image(image_path)
        
        if imgbb_result['success']:
            image_url = imgbb_result['url']
            print(f"✓ Image uploaded successfully: {image_url}")
        else:
            errors.append(f"imgbb upload failed: {imgbb_result['error']}")
            print(f"✗ imgbb upload failed: {imgbb_result['error']}")
            # 如果圖片上傳失敗，不繼續寫入 Google Sheets
            return {
                'success': False,
                'image_url': None,
                'sheet_updated': False,
                'errors': errors
            }
        
        # 步驟 2: 寫入資料至 Google Sheets
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H:%M:%S')
        
        print(f"Writing data to Google Sheets...")
        sheet_result = self.gsheet_writer.append_row(date_str, time_str, image_url, note)
        
        if sheet_result['success']:
            sheet_updated = True
            print(f"✓ Data written to Google Sheets successfully")
        else:
            errors.append(f"Google Sheets write failed: {sheet_result['error']}")
            print(f"✗ Google Sheets write failed: {sheet_result['error']}")
        
        # 整體成功：圖片上傳成功且 Sheet 寫入成功
        overall_success = imgbb_result['success'] and sheet_result['success']
        
        return {
            'success': overall_success,
            'image_url': image_url,
            'sheet_updated': sheet_updated,
            'errors': errors if errors else None
        }
