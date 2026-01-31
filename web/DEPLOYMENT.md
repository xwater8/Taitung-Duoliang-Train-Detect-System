# 台東多良車站火車偵測系統 - 部署指南

## 📋 系統架構概覽

本系統包含兩個主要部分：

1. **後端偵測系統** (`train_detect`) - 執行火車偵測並上傳資料
2. **前端網頁系統** (`web`) - 顯示偵測結果

```
流程：火車經過 → 偵測系統 → imgur (圖片) + Google Sheets (資料) → 前端網頁顯示
```

---

## 🔧 後端部署步驟

### 1. 取得 imgur API 金鑰

1. 前往 [imgur API 註冊頁面](https://api.imgur.com/oauth2/addclient)
2. 選擇 "OAuth 2 authorization without a callback URL"
3. 填寫應用程式資訊
4. 取得 **Client ID**（記下來待用）

### 2. 設定 Google Sheets API

#### 2.1 建立 Google Cloud 專案

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案或選擇現有專案
3. 啟用以下 API：
   - Google Sheets API
   - Google Drive API

#### 2.2 建立 Service Account

1. 在 Google Cloud Console 中，前往「IAM 與管理」→「服務帳戶」
2. 點擊「建立服務帳戶」
3. 輸入名稱（例如：train-detect-uploader）
4. 點擊「建立並繼續」
5. 略過權限設定，點擊「繼續」→「完成」
6. 點擊剛建立的服務帳戶
7. 前往「金鑰」分頁
8. 點擊「新增金鑰」→「建立新的金鑰」→ 選擇「JSON」
9. 下載 JSON 金鑰檔案（重要：請妥善保管）
10. 將檔案重新命名為 `credentials.json` 並放在 `train_detect/` 目錄

#### 2.3 建立並設定 Google Sheets

1. 建立新的 [Google Sheets](https://sheets.google.com/)
2. 在第一列輸入標題：
   ```
   日期 | 時間 | imgur url | 備註
   ```
3. 點擊右上角「共用」按鈕
4. 貼上剛才建立的 Service Account 電子郵件地址（格式：`xxx@xxx.iam.gserviceaccount.com`）
5. 設定權限為「編輯者」
6. 點擊「傳送」
7. 從瀏覽器網址列複製 Spreadsheet ID：
   ```
   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
   ```

#### 2.4 發佈 Google Sheets 為 CSV（供前端讀取）

1. 在 Google Sheets 中，點擊「檔案」→「共用」→「發佈到網路」
2. 選擇要發佈的工作表（通常是「工作表1」）
3. 格式選擇「逗號分隔值 (.csv)」
4. 點擊「發佈」
5. 複製產生的 CSV 連結（待用）

### 3. 設定環境變數

在 `train_detect/` 目錄建立 `.env` 檔案（或透過 Docker Compose 設定）：

```bash
# imgur API 設定
IMGUR_CLIENT_ID=你的_imgur_client_id

# Google Sheets 設定
GSHEET_CREDENTIALS_PATH=./credentials.json
GSHEET_SPREADSHEET_ID=你的_spreadsheet_id
GSHEET_WORKSHEET_NAME=工作表1

# 上傳功能開關
ENABLE_UPLOAD=true
```

**注意：不要將 `.env` 和 `credentials.json` 提交到 Git！**

### 4. 更新 Docker Compose（選用）

如果使用 Docker，在 `docker-compose.yml` 中加入環境變數：

```yaml
services:
  train_detect:
    environment:
      - IMGUR_CLIENT_ID=${IMGUR_CLIENT_ID}
      - GSHEET_SPREADSHEET_ID=${GSHEET_SPREADSHEET_ID}
      - GSHEET_CREDENTIALS_PATH=/app/credentials.json
      - GSHEET_WORKSHEET_NAME=工作表1
      - ENABLE_UPLOAD=true
    volumes:
      - ./credentials.json:/app/credentials.json:ro
```

### 5. 安裝相依套件

```bash
cd train_detect
pip install -r docker/requirements.txt
```

### 6. 測試執行

```bash
cd train_detect
python -m train_detect.main
```

執行後應看到：
- `✓ Upload功能已啟用` - 表示上傳器初始化成功
- 當偵測到火車時會顯示上傳進度

---

## 🌐 前端部署步驟

### 1. 設定 Google Sheets CSV URL

編輯 `train_detect_web/app.js`，找到第 2 行：

```javascript
const GOOGLE_SHEET_CSV_URL = 'YOUR_GOOGLE_SHEET_CSV_URL_HERE';
```

替換為剛才取得的 CSV 連結：

```javascript
const GOOGLE_SHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/你的_SPREADSHEET_ID/export?format=csv&gid=0';
```

### 2. 本地測試

使用簡單的 HTTP 伺服器：

```bash
cd train_detect_web

# Python 3
python -m http.server 8000

# 或使用 Node.js (需安裝 http-server)
npx http-server -p 8000
```

開啟瀏覽器：`http://localhost:8000`

### 3. 部署到 GitHub Pages

#### 3.1 建立 GitHub Repository

```bash
cd train_detect_web
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的帳號/train_detect_web.git
git push -u origin main
```

#### 3.2 啟用 GitHub Pages

1. 前往 GitHub Repository 頁面
2. 點擊「Settings」
3. 左側選單選擇「Pages」
4. Source 選擇「Deploy from a branch」
5. Branch 選擇「main」，資料夾選擇「/ (root)」
6. 點擊「Save」
7. 等待幾分鐘後，網站將發佈至：
   ```
   https://你的帳號.github.io/train_detect_web/
   ```

---

## 📁 檔案結構

```
train_detect/
├── config.py                    # 配置檔（已加入 API 設定）
├── config.example.py            # 配置範例檔
├── credentials.json             # Google Service Account 金鑰 (勿提交到 Git!)
├── .env                         # 環境變數 (勿提交到 Git!)
├── docker/
│   └── requirements.txt         # Python 依賴套件（已更新）
├── train_detect/
│   ├── main.py                  # 主程式（已整合上傳功能）
│   └── uploader.py              # 上傳模組（新增）
└── web/                         # 前端網頁系統
    ├── index.html               # 前端頁面
    ├── styles.css               # CSS 樣式
    ├── app.js                   # JavaScript 邏輯
    └── README.md                # 前端說明
```

---

## 🔐 安全性注意事項

### 必須加入 `.gitignore`：

```gitignore
# Google Credentials
credentials.json
*.json

# 環境變數
.env
.env.local

# Python
__pycache__/
*.pyc
```

### 最佳實踐：

1. **絕對不要**將 API 金鑰、Service Account JSON 提交到 Git
2. 使用環境變數管理敏感資訊
3. 定期輪換 API 金鑰
4. Google Sheets 僅分享給 Service Account，不要公開
5. 前端 CSV URL 可公開（僅讀取權限）

---

## 🧪 測試檢查清單

### 後端測試

- [ ] imgur Client ID 已正確設定
- [ ] Google Sheets Service Account 金鑰已下載並放置正確位置
- [ ] Service Account 已加入 Google Sheets 編輯權限
- [ ] 環境變數 `ENABLE_UPLOAD=true` 已設定
- [ ] 執行程式後看到「Upload功能已啟用」
- [ ] 偵測到火車時能成功上傳圖片和資料
- [ ] Google Sheets 中出現新資料列

### 前端測試

- [ ] `app.js` 中的 CSV URL 已正確設定
- [ ] 本地伺服器能正常顯示網頁
- [ ] 能從 Google Sheets 讀取並顯示資料
- [ ] 搜尋過濾功能正常
- [ ] 圖片點擊燈箱效果正常
- [ ] GitHub Pages 部署成功並可訪問

---

## 🐛 常見問題排除

### 後端問題

**Q: 顯示「初始化上傳器失敗」**

A: 檢查：
1. `credentials.json` 路徑是否正確
2. Service Account 是否有 Google Sheets 編輯權限
3. Spreadsheet ID 是否正確

**Q: 圖片上傳失敗**

A: 檢查：
1. imgur Client ID 是否正確
2. 網路連線是否正常
3. 圖片檔案是否存在且未損壞

**Q: Google Sheets 寫入失敗**

A: 檢查：
1. Service Account 電子郵件是否已加入 Google Sheets 共用清單
2. 工作表名稱是否正確（預設為「工作表1」）
3. Google Sheets API 是否已啟用

### 前端問題

**Q: 顯示「請在 app.js 中設定 GOOGLE_SHEET_CSV_URL」**

A: 編輯 `app.js` 第 2 行，填入正確的 CSV URL

**Q: CORS 錯誤**

A: Google Sheets CSV URL 必須是「發佈到網路」產生的公開連結，不是直接的 Google Sheets 網址

**Q: 資料不更新**

A: 
1. 點擊「重新載入」按鈕
2. 檢查瀏覽器快取
3. 確認 Google Sheets 中有最新資料

**Q: GitHub Pages 顯示 404**

A: 
1. 確認 Repository 設定中 Pages 已啟用
2. 等待幾分鐘讓 GitHub 完成部署
3. 確認檔案都已正確推送到 `main` 分支

---

## 📊 系統維護

### 監控建議

1. 定期檢查 Google Sheets 資料是否正常更新
2. 監控 imgur API 使用額度（免費方案：12,500 次/天）
3. 檢查 Google Sheets API 配額（免費方案：100 讀取/分鐘、60 寫入/分鐘）

### 備份建議

1. 定期下載 Google Sheets 資料作為備份
2. 本地 `output/` 資料夾保留原始圖片
3. 設定 Google Sheets 自動備份到 Google Drive

---

## 📞 支援

如遇到問題，請檢查：
1. 系統日誌檔案：`train_detect/logs/Log.txt`
2. 瀏覽器控制台（F12）是否有錯誤訊息

---

**完成部署後，系統將自動偵測火車、上傳資料，並在網頁上即時顯示！** 🎉
