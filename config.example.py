from easydict import EasyDict
import numpy as np

import os

def get_config():
    conf= EasyDict()

    # video_path="data/台東多良車站即時影像_20251010_1457_1508.mp4"#影片的07:20有火車經過
    # video_path="data/台東多良車站即時影像_20251010_1900_1905.mp4"
    # video_path= "/home/mingming/01.Projects/999.youtube_video_analysis/data/KC Zoo Polar Bear Cam_20251010_1519_1529.mp4"
    # video_path= "rtsp://192.168.1.108:8554/youtube_train"
    # conf.video_path= "data/台東多良車站即時影像_20251026_0713.mkv"
    # cap.set(cv2.CAP_PROP_POS_FRAMES, 8700)
    
    conf.video_path= "rtsp://mediamtx:8554/youtube_train"
    
    conf.resize_ratio= 0.7
    conf.output_root= "./output"
    conf.output_train_img_folder= os.path.join(conf.output_root, "train_img")
    conf.output_background_img_folder= os.path.join(conf.output_root, "background_img")
    
    conf.ssim_threshold= 0.70  #SSIM相似度閾值
    conf.vote_count= 10  #投票法的窗口大小
    conf.too_light_pixel_threshold= 210  #過亮像素的閾值
    
    #火車polygon座標, 1920x1080解析度下的座標
    conf.train_polygon= np.asarray(
        [ [1089, 720],
        [1578, 429],
        [1652, 481],
        [1116, 823]], dtype=np.float32       
    )
    conf.train_polygon[:,0]/=1920.0
    conf.train_polygon[:,1]/=1080.0
    conf.show_img= True
    conf.show_debug_img= False
    
    # API 配置 - 從環境變數讀取
    # 使用方式：
    # 1. 在系統中設定環境變數，或
    # 2. 在 Docker Compose 中設定環境變數
    # 3. 使用 .env 檔案（需安裝 python-dotenv）
    
    # imgbb API Key
    # 取得方式：
    # 1. 註冊 https://imgbb.com/
    # 2. 前往 https://api.imgbb.com/ 取得 API Key
    conf.imgbb_api_key = os.environ.get('IMGBB_API_KEY', '')
    
    # Google Sheets Service Account 金鑰檔案路徑
    # 取得方式：
    # 1. 前往 Google Cloud Console (https://console.cloud.google.com/)
    # 2. 建立專案並啟用 Google Sheets API 和 Google Drive API
    # 3. 建立 Service Account 並下載 JSON 金鑰檔案
    # 4. 將金鑰檔案放在專案目錄並設定路徑
    conf.gsheet_credentials_path = os.environ.get('GSHEET_CREDENTIALS_PATH', './credentials.json')
    
    # Google Spreadsheet ID
    # 從 Google Sheets 網址取得：
    # https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
    conf.gsheet_spreadsheet_id = os.environ.get('GSHEET_SPREADSHEET_ID', '')
    
    # Google Sheets 工作表名稱
    conf.gsheet_worksheet_name = os.environ.get('GSHEET_WORKSHEET_NAME', '工作表1')
    
    # 上傳功能開關
    # 設定為 'true' 啟用上傳，'false' 停用（僅本地儲存）
    conf.enable_upload = os.environ.get('ENABLE_UPLOAD', 'false').lower() == 'true'

    return conf
