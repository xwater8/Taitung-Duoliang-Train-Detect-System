"""
測試上傳功能腳本
"""
import os
import sys
from datetime import datetime
from train_detect.uploader import TrainDetectionUploader

def test_upload():
    """測試上傳功能"""
    
    print("=" * 60)
    print("開始測試上傳功能")
    print("=" * 60)
    
    # 從環境變數讀取設定
    imgbb_api_key = os.environ.get('IMGBB_API_KEY', '')
    gsheet_credentials_path = os.environ.get('GSHEET_CREDENTIALS_PATH', './credentials.json')
    gsheet_spreadsheet_id = os.environ.get('GSHEET_SPREADSHEET_ID', '')
    gsheet_worksheet_name = os.environ.get('GSHEET_WORKSHEET_NAME', '工作表1')
    
    # 檢查設定
    print("\n1. 檢查設定：")
    print(f"   - IMGBB_API_KEY: {'已設定 ✓' if imgbb_api_key else '未設定 ✗'}")
    print(f"   - GSHEET_CREDENTIALS_PATH: {gsheet_credentials_path}")
    print(f"   - GSHEET_SPREADSHEET_ID: {'已設定 ✓' if gsheet_spreadsheet_id else '未設定 ✗'}")
    print(f"   - GSHEET_WORKSHEET_NAME: {gsheet_worksheet_name}")
    
    # 檢查認證檔案
    creds_exists = os.path.exists(gsheet_credentials_path)
    print(f"   - credentials.json 存在: {'是 ✓' if creds_exists else '否 ✗'}")
    
    if not imgbb_api_key or not gsheet_spreadsheet_id or not creds_exists:
        print("\n✗ 設定不完整，無法進行測試")
        return False
    
    # 初始化上傳器
    print("\n2. 初始化上傳器...")
    try:
        uploader = TrainDetectionUploader(
            imgbb_api_key=imgbb_api_key,
            gsheet_credentials_path=gsheet_credentials_path,
            gsheet_spreadsheet_id=gsheet_spreadsheet_id,
            gsheet_worksheet_name=gsheet_worksheet_name
        )
        print("   ✓ 上傳器初始化成功")
    except Exception as e:
        print(f"   ✗ 上傳器初始化失敗: {e}")
        return False
    
    # 查找測試圖片
    print("\n3. 查找測試圖片...")
    test_image_folders = [
        './output_images/train_img',
        './output/train_img'
    ]
    
    test_image_path = None
    for folder in test_image_folders:
        if os.path.exists(folder):
            images = [f for f in os.listdir(folder) if f.endswith(('.jpg', '.png', '.jpeg'))]
            if images:
                test_image_path = os.path.join(folder, images[0])
                print(f"   ✓ 找到測試圖片: {test_image_path}")
                break
    
    if not test_image_path:
        print("   ✗ 找不到測試圖片")
        print("   提示: 請確保 ./output_images/train_img 或 ./output/train_img 資料夾中有圖片")
        return False
    
    # 測試 Google Sheets 連線
    print("\n4. 測試 Google Sheets 連線...")
    connect_result = uploader.gsheet_writer.connect()
    if connect_result['success']:
        print("   ✓ Google Sheets 連線成功")
    else:
        print(f"   ✗ Google Sheets 連線失敗: {connect_result['error']}")
        return False
    
    # 測試上傳
    print("\n5. 開始測試上傳...")
    print(f"   圖片路徑: {test_image_path}")
    print(f"   圖片大小: {os.path.getsize(test_image_path) / 1024:.2f} KB")
    
    result = uploader.upload_train_event(
        image_path=test_image_path,
        timestamp=datetime.now(),
        note='測試上傳 - 自動化測試'
    )
    
    print("\n6. 測試結果：")
    print(f"   - 整體成功: {'是 ✓' if result['success'] else '否 ✗'}")
    print(f"   - 圖片 URL: {result.get('image_url', 'N/A')}")
    print(f"   - Sheet 已更新: {'是 ✓' if result.get('sheet_updated') else '否 ✗'}")
    
    if result.get('errors'):
        print(f"   - 錯誤訊息:")
        for error in result['errors']:
            print(f"     • {error}")
    
    print("\n" + "=" * 60)
    if result['success']:
        print("✓ 上傳功能測試通過！")
        print(f"\n請檢查 Google Sheets 確認資料是否已寫入：")
        print(f"https://docs.google.com/spreadsheets/d/{gsheet_spreadsheet_id}/edit")
    else:
        print("✗ 上傳功能測試失敗")
    print("=" * 60)
    
    return result['success']


if __name__ == '__main__':
    # 載入 .env 檔案
    if os.path.exists('.env'):
        print("載入 .env 檔案...")
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    success = test_upload()
    sys.exit(0 if success else 1)
