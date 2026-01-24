# 台東多良車站火車偵測儀表板

> 一個用於視覺化台東多良車站火車偵測結果的實時網頁儀表板

🚂 **線上示範**: https://xwater8.github.io/Taitung-Duoliang-Train-Detect-System-Web/

## 專案概述

此專案是台東多良車站火車偵測系統的**報告與視覺化儀表板**。當火車經過車站指定區域時，偵測系統會自動將偵測結果上傳到 Google Sheets，並將火車圖片上傳到 Imgur，透過此網頁介面提供實時訪問。

儀表板提供直觀的瀏覽器介面，支援以下功能：
- **查看偵測記錄** - 包含時間戳和圖片
- **搜尋與篩選** - 按日期和關鍵字篩選結果
- **監控統計資訊** - 包括每日及總偵測次數
- **瀏覽火車圖片** - 燈箱圖片庫

## 系統架構

系統運作流程如下：

```
┌─────────────────────────────────────────────────────────────┐
│  台東多良車站直播串流                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  火車偵測系統 (train_detect)                                │
│  • 電腦視覺偵測                                              │
│  • 影像處理與分析                                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐      ┌──────────┐    ┌─────────────┐
    │ Imgur   │      │ Google   │    │ 偵測日誌    │
    │ 圖片儲存 │      │ Sheets   │    │             │
    └─────────┘      └──────────┘    └─────────────┘
         │                 │
         └─────────────────┼─────────────────┐
                           │                 │
         ┌─────────────────▼─────────────────▼┐
         │  火車偵測網頁儀表板                │
         │  (此資源庫)                        │
         │  • 實時資料顯示                    │
         │  • 搜尋與篩選                      │
         │  • 圖片庫                          │
         └───────────────────────────────────┘
```

## 主要功能

✅ **無需後端** - 完全靜態前端，無需伺服器  
✅ **實時更新** - 從 Google Sheets 提取最新資料  
✅ **響應式設計** - 適用於桌面、平板和行動裝置  
✅ **圖片庫** - 火車偵測照片的燈箱檢視器  
✅ **進階搜尋** - 按日期和關鍵字篩選  
✅ **實時統計** - 總次數、每日統計和更新時間戳  
✅ **易於部署** - 直接部署到 GitHub Pages  

## 快速開始

### 前置需求

- 現代化網頁瀏覽器
- 能夠連接到 Google Sheets CSV 匯出網址

### 安裝

1. **複製資源庫**:
   ```bash
   git clone https://github.com/yourusername/train_detect_web.git
   cd train_detect_web
   ```

2. **設定 Google Sheets 網址** (可選 - 用於本地開發):
   編輯 `app.js` 並更新 `GOOGLE_SHEET_CSV_URL` 常數:
   ```javascript
   const GOOGLE_SHEET_CSV_URL = 'YOUR_GOOGLE_SHEETS_CSV_URL';
   ```

3. **本地執行** (Python 3):
   ```bash
   python -m http.server 8000
   ```
   
   或使用 Node.js:
   ```bash
   npx http-server -p 8000
   ```

4. **在瀏覽器中開啟**:
   瀏覽至 `http://localhost:8000`

## 專案結構

```
train_detect_web/
├── index.html          # 主要 HTML 結構
├── app.js              # JavaScript 邏輯與資料處理
├── styles.css          # CSS 樣式與響應式設計
├── README.md           # 本檔案
├── DEPLOYMENT.md       # 詳細部署指南
└── .gitignore          # Git 忽略規則
```

## 設定

### Google Sheets 整合

為使儀表板能夠顯示火車偵測資料，需要：

1. **從偵測系統資料庫匯出 Google Sheets 為 CSV**
2. **在 Google Sheets 設定中啟用「發佈到網路」**
3. **更新 `app.js` 中的 CSV 網址**:
   ```javascript
   const GOOGLE_SHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0';
   ```

預期的 CSV 格式:
```
日期,時間,原圖url,縮圖url,備註
2026-01-24,08:15:30,https://imgur.com/image1.jpg,https://imgur.com/thumb1.jpg,自強號北上列車
```

詳細設定說明請見 [DEPLOYMENT.md](DEPLOYMENT.md)。

## 使用方式

### 查看記錄

儀表板以表格格式顯示所有偵測到的火車記錄，包含：
- **日期與時間** - 精確的偵測時間戳
- **縮圖** - 偵測圖片的預覽
- **備註** - 關於火車的額外資訊

### 搜尋與篩選

1. **按日期篩選**: 使用日期選擇器篩選特定日期的記錄
2. **按關鍵字搜尋**: 在「備註」欄位搜尋特定火車類型或情況
3. **重置**: 清除所有篩選條件並查看所有記錄
4. **重新載入**: 從 Google Sheets 重新載入資料

### 查看圖片

點擊任何縮圖即可在燈箱檢視器中開啟全尺寸圖片。使用關閉按鈕或點擊影像外部即可關閉。

## 瀏覽器支援

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- 行動瀏覽器 (iOS Safari 12+, Android Chrome 88+)

## 技術堆疊

- **前端**: HTML5、CSS3、Vanilla JavaScript (無框架)
- **資料來源**: Google Sheets (CSV 匯出)
- **圖片代管**: Imgur
- **部署**: GitHub Pages
- **後端**: 外部 (train_detect) - 將資料上傳至 Google Sheets 和 Imgur

## 部署

### GitHub Pages (推薦)

自動代管和 CDN 交付:

1. 將此資源庫推送到 GitHub
2. 前往「Repository Settings → Pages」
3. 選擇「Deploy from a branch → `main` branch」
4. 儀表板將在以下網址上線: `https://yourusername.github.io/train_detect_web/`

### 其他代管選項

此為靜態網站，可部署至：
- **Netlify** - 拖放部署
- **Vercel** - 基於 Git 的持續部署
- **AWS S3** - 靜態網站代管
- **任何網頁伺服器** - 只需將檔案複製到 `public` 資料夾

詳細說明請見 [DEPLOYMENT.md](DEPLOYMENT.md)。

## 開發

### 檔案組織

- `index.html` - DOM 結構和佈局
- `app.js` - 應用邏輯、資料擷取和事件處理器
- `styles.css` - 所有樣式，包括響應式斷點

### app.js 中的主要函數

| 函數 | 用途 |
|----------|---------|
| `loadData()` | 從 Google Sheets 擷取 CSV 資料 |
| `parseCSV()` | 將 CSV 文字解析為 JavaScript 物件 |
| `applyFilters()` | 應用日期/關鍵字篩選 |
| `renderTable()` | 呈現偵測記錄表格 |
| `openLightbox()` | 開啟圖片檢視器彈窗 |

## 相關專案

- **[train_detect](../train_detect/)** - 後端偵測系統 (Python)
  - 基於電腦視覺的火車偵測
  - 圖片上傳至 Imgur
  - 資料儲存於 Google Sheets
  - 在 Raspberry Pi 或 x86 伺服器上執行

## 疑難排解

### 資料無法載入？

- 檢查瀏覽器控制台 (F12) 是否有錯誤
- 驗證 CSV 網址是否可訪問且公開分享
- 確保 Google Sheets 已發佈為 CSV

### 圖片未顯示？

- 確認 Imgur 連結為公開
- 在瀏覽器控制台檢查是否有混合內容警告 (HTTPS vs HTTP)
- 驗證縮圖網址是否正確

### 樣式顯示錯誤？

- 清除瀏覽器快取 (Ctrl+Shift+Delete)
- 在 DevTools 的「Network」分頁檢查 styles.css 是否載入

更多疑難排解資訊，請見 [DEPLOYMENT.md](DEPLOYMENT.md)。

## 隱私與安全

- **此伺服器不儲存任何資料**
- **不使用 Cookie 或追蹤**
- **Google Sheets 資料為公開** (僅 CSV 匯出)
- **圖片網址直接來自 Imgur**

## 未來增強功能

潛在的改進方向：
- [ ] 透過 WebSocket 進行實時更新
- [ ] 資料匯出功能 (JSON、Excel)
- [ ] 進階分析與統計
- [ ] 地圖整合顯示偵測位置
- [ ] 火車類型分類顯示
- [ ] 自動化資料歸檔

## 支援與貢獻

針對此儀表板的問題：
- 檢查 [DEPLOYMENT.md](DEPLOYMENT.md) 了解常見問題
- 查看瀏覽器控制台的錯誤訊息
- 驗證 Google Sheets 和 Imgur 設定

如有偵測後端的問題，請參閱 [train_detect](../train_detect/) 專案。

## 授權

詳見 LICENSE 檔案。

---

**以愛心為台東多良車站的火車愛好者而製**