# Introduction - 台東多良車站火車偵測系統(SideProject)

本專案是來偵測台東多良車站的火車何時出現在畫面中，方便觀察有哪些種類的火車。讓喜歡火車的網友可以根據時間去youtube進行回放，以及觀察到有部分火車沒有出現在網友提供的時刻表上！例如有時候可以觀察到單節火車頭在鐵軌上。本次挑戰在 RaspberryPi4 上面運作，所以嘗試使用傳統影像處理。

本專案目前目標是盡可能不要漏掉每輛火車，所以短時間內畫面變化大會被誤判為有火車是正常情況。

p.s本專案並非官方提供的服務，所以可能會隨時終止，但是有興趣的人可以把專案fork回去自行部屬使用。

台東多良車站即時影像 Taitung Duoliang Station Live Camera
https://www.youtube.com/watch?v=UCG1aXVO8H8

本專案使用 Docker 環境下確定可以在 x86 與 Raspberry Pi 4 上面正常運行

![alt text](./docs/image.png)

[Youtube Demo影片](https://youtu.be/V8ZHeCWi8-8)

[報表系統網址](https://xwater8.github.io/Taitung-Duoliang-Train-Detect-System/)

## 專案結構

```
train_detect/
├── web/                              # 前端網頁儀表板
│   ├── index.html                    # 主要頁面
│   ├── app.js                        # JavaScript 邏輯
│   ├── styles.css                    # CSS 樣式
│   ├── web_readme.md                 # 前端說明
│   └── DEPLOYMENT.md                 # 部署指南
├── train_detect/                     # 後端偵測系統
│   ├── __init__.py                   # 模組初始化
│   ├── main.py                       # 主程式（包含 EMA 背景建模與火車偵測邏輯）
│   ├── uploader.py                   # 上傳模組（imgbb + Google Sheets）
│   └── toolbox/                      # 工具函式庫
│       ├── __init__.py               # 工具模組初始化
│       ├── bbox.py                   # 邊界框處理
│       ├── log.py                    # 日誌記錄
│       ├── utils.py                  # 通用工具函式
│       └── video_stream.py           # 影像串流處理
├── docker/                           # Docker 相關檔案
│   ├── train_detect.dockerfile       # 辨識服務 Dockerfile
│   ├── mediamtx.dockerfile           # MediaMTX 串流服務 Dockerfile
│   ├── mediamtx.yml                  # MediaMTX 設定檔
│   ├── detect_train.service          # Systemd 服務檔
│   └── requirements.txt              # Python 依賴套件
├── output/                           # 輸出資料夾
│   ├── train_img/                    # 火車偵測圖片
│   └── background_img/               # 背景圖片
├── logs/                             # 日誌資料夾
│   └── Log.txt                       # 運行日誌
├── docs/                             # 文件資料夾
├── config.example.py                 # 設定檔範例
├── config.py                         # 實際設定檔（需自行建立）
├── credentials.json                  # Google Sheets 認證檔（需自行建立）
├── docker-compose.yml                # Docker Compose 設定
├── test_upload.py                    # 上傳功能測試
└── README.md                         # 本檔案
```


## 如何安裝與使用
### 方法1: docker啟動服務(youtube轉rtsp串流+辨識服務)
```
$xhost + #開啟xhost權限, 讓opencv視窗可以從docker內部開啟
$docker compose up -d
```

### 方法2:使用python安裝

#### youtube轉rtsp服務
透過mediamtx、yt-dlp服務將youtube串流轉成rtsp，方便opencv進行讀取。並且配合systemctl讓服務可以自動重啟，避免死掉
```
#從yt-dlp github上下載執行檔, 並且放在docker資料夾中
官網: https://github.com/yt-dlp/yt-dlp/releases/latest/download/

從mediamtx官方網站下載mediamtx檔案, 並且放在docker資料夾中
官網: https://github.com/bluenviron/mediamtx/releases/tag/v1.15.6

進入到docker資料夾內部運行mediamtx, p.s須確保與mediamtx.yml在同一層目錄下
$cd docker
$mediamtx
```


#### 辨識服務
安裝辨識環境
```
# 建立虛擬環境
$pip3 install virtualenv
$virtualenv venv
$source ./venv/bin/activate

# 安裝辨識所需環境
$source ./venv/bin/activate
$pip3 install docker/requirements.txt
```

開啟辨識服務
```
$source ./venv/bin/activate
$python3 main.py
```

## 系統說明
1. 透過yt-dlp將youtube直播轉成串流, 並且透過mediamtx輸出成rtsp串流供opencv使用
2. opencv讀取mediamtx輸出的串流
3. 透過EMA_BackgroundModel建立畫面背景圖
4. 使用SSIM演算法比較background_frame與 frame的差異, 判斷出在指定polygon區域中是否有變化
5. 若變化超過一定的門檻值認為是有火車, 否則視為正常。 會進行連續判斷並且挑選變化最大的圖片作為火車圖片。 並且判斷圖片中的區域是否過亮, 若過亮被排除在計算相似度分數的範圍外。


## config.py 參數說明

本專案透過 `config.py` 的 `get_config()` 函式統一管理所有參數設定。請複製 `config.example.py` 為 `config.py` 並根據需求調整。主要配置項目如下：

### 資料來源與輸出

| 參數 | 說明 | 預設值 | 範例 |
|------|------|--------|------|
| `video_path` | 影片來源，可為本地路徑或 RTSP 串流 | `rtsp://mediamtx:8554/youtube_train` | 本地：`data/video.mp4`<br>串流：`rtsp://192.168.1.108:8554/youtube_train` |
| `resize_ratio` | 影像縮放比例，用於降低運算負擔 | `0.7` | 0.5 ~ 1.0 |
| `output_root` | 輸出資料夾根目錄 | `./output` | 可設為絕對路徑 |
| `output_train_img_folder` | 檢測到火車時的圖片保存路徑 | `./output/train_img` | 自動從 `output_root` 組合 |
| `output_background_img_folder` | 背景圖片定期保存路徑 | `./output/background_img` | 自動從 `output_root` 組合 |

### 演算法參數

| 參數 | 說明 | 預設值 | 調整建議 |
|------|------|--------|----------|
| `ssim_threshold` | SSIM 相似度門檻，低於此值判定為火車經過 | `0.70` | 範圍 0.0 ~ 1.0，降低可減少漏報但增加誤報 |
| `vote_count` | 投票法窗口大小，用於平滑化判斷結果 | `10` | 增加可減少誤報，但會延遲反應時間 |
| `too_light_pixel_threshold` | 過亮像素判斷閾值（0-255） | `210` | 過亮區域不納入相似度計算，避免反光干擾 |

### 火車偵測區域

| 參數 | 說明 |
|------|------|
| `train_polygon` | 火車偵測區域的多邊形座標（四個頂點：左上、右上、右下、左下），以 1920×1080 解析度為基準進行正規化（座標值除以寬高），實際執行時會根據影像大小自動縮放 |

> [!TIP]
> 可在執行時開啟視窗，根據實際畫面調整多邊形區域，只偵測鐵軌所在區域以減少誤報。

### 顯示選項

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `show_img` | 是否顯示主處理畫面（含偵測框與資訊） | `True` |
| `show_debug_img` | 是否顯示除錯畫面（差異圖、二值化圖等） | `False` |

> [!NOTE]
> Docker 環境下若需顯示視窗，請確保已執行 `xhost +` 開啟 X11 權限。

### API 與上傳設定

| 參數 | 說明 | 環境變數 | 取得方式 |
|------|------|----------|----------|
| `imgbb_api_key` | imgbb 圖片上傳 API Key | `IMGBB_API_KEY` | 註冊 [imgbb.com](https://imgbb.com/) 並至 [API 頁面](https://api.imgbb.com/) 取得 |
| `gsheet_credentials_path` | Google Sheets Service Account JSON 金鑰路徑 | `GSHEET_CREDENTIALS_PATH` | 至 [Google Cloud Console](https://console.cloud.google.com/) 建立 Service Account 並下載 JSON 金鑰 |
| `gsheet_spreadsheet_id` | Google Spreadsheet ID | `GSHEET_SPREADSHEET_ID` | 從試算表網址取得：`https://docs.google.com/spreadsheets/d/{ID}/edit` |
| `gsheet_worksheet_name` | Google Sheets 工作表名稱 | `GSHEET_WORKSHEET_NAME` | 預設 `工作表1` |
| `enable_upload` | 是否啟用上傳功能 | `ENABLE_UPLOAD` | 設為 `true` 啟用，`false` 則僅本地儲存 |

> [!IMPORTANT]
> 使用 Google Sheets 功能前，需先在 Google Cloud Console 啟用 **Google Sheets API** 和 **Google Drive API**，並將 Service Account 的電子郵件地址加入試算表的共用權限。

### 配置範例

```python
# 基本使用（僅本地偵測）
conf.video_path = "rtsp://mediamtx:8554/youtube_train"
conf.enable_upload = False

# 啟用上傳功能
conf.enable_upload = True
conf.imgbb_api_key = "your_imgbb_api_key"
conf.gsheet_spreadsheet_id = "your_spreadsheet_id"
```

根據實際使用環境與需求，可調整上述參數以優化偵測效果。



## TODO:
- [x] 根據觀察誤報大部分都在ssim>0.7情況下
    - 因此調低conf.simm_threshold到0.7-->有效果
- [x] mediamtx撥放youtube每4~5個小時就會斷線
    - 在mediamtx.yml中加入以下參數試試-->有效果
        ```
        runOnInitRestart: yes
        ```
- [] 解決晚上的時候因為汽車大燈造成指定區域中SSIM變化過大的問題
- [x] 將background與train分開, 都存在output_root下面
    - background: output_root/background
    - train: output_root/train
    - train_ori: output_root/train_ori(暫時不用train_ori)



## 參考資料:
多良車站班次:
https://fullfenblog.tw/2016-08-14-628/#%E5%A4%9A%E8%89%AF%E8%BB%8A%E7%AB%99%EF%BD%9C%E6%9C%80%E6%96%B0%E7%81%AB%E8%BB%8A%E9%80%9A%E8%A1%8C%E6%99%82%E5%88%BB%E8%A1%A8


Frigate_移動物體與偵測的作法

https://docs.frigate-cn.video/frigate/video_pipeline#%E8%A7%86%E9%A2%91%E6%B5%81%E7%A8%8B%E8%AF%A6%E8%BF%B0

可參考這一段程式:https://github.com/blakeblackshear/frigate/blob/b1a5896b537cad54fe13bf7090b082d0214be44e/frigate/motion/frigate_motion.py#L70-L132


