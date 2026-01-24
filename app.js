// ===== 全域變數 =====
const GOOGLE_SHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTdgEX5_o_9EgwdLQqY5s49IY7A1wpbZhN5yJ9nElq4l66Yy6ooI0H6FQOjo_2a6sPZw6B1V4ulUcIE/pub?gid=0&single=true&output=csv';

const USE_FAKE_DATA = false;

const FAKE_DATA = [
    {
        date: '2026-01-24',
        time: '08:15:30',
        image: 'https://picsum.photos/800/600?random=1',
        thumbnail: 'https://picsum.photos/200/150?random=1',
        note: '自強號北上列車通過'
    },
    {
        date: '2026-01-24',
        time: '10:45:20',
        image: 'https://picsum.photos/800/600?random=2',
        thumbnail: 'https://picsum.photos/200/150?random=2',
        note: '莒光號南下列車'
    },
    {
        date: '2026-01-24',
        time: '14:20:15',
        image: 'https://picsum.photos/800/600?random=3',
        thumbnail: 'https://picsum.photos/200/150?random=3',
        note: '普悠瑪號北上通過'
    },
    {
        date: '2026-01-23',
        time: '16:30:45',
        image: 'https://picsum.photos/800/600?random=4',
        thumbnail: 'https://picsum.photos/200/150?random=4',
        note: '太魯閣號南下列車'
    },
    {
        date: '2026-01-23',
        time: '18:55:10',
        image: 'https://picsum.photos/800/600?random=5',
        thumbnail: 'https://picsum.photos/200/150?random=5',
        note: '區間車通過'
    },
    {
        date: '2026-01-22',
        time: '09:10:25',
        image: 'https://picsum.photos/800/600?random=6',
        thumbnail: 'https://picsum.photos/200/150?random=6',
        note: '自強號南下列車'
    },
    {
        date: '2026-01-22',
        time: '13:40:50',
        image: 'https://picsum.photos/800/600?random=7',
        thumbnail: 'https://picsum.photos/200/150?random=7',
        note: '莒光號北上通過'
    },
    {
        date: '2026-01-21',
        time: '11:25:35',
        image: 'https://picsum.photos/800/600?random=8',
        thumbnail: 'https://picsum.photos/200/150?random=8',
        note: '普悠瑪號南下列車'
    },
    {
        date: '2026-01-21',
        time: '07:20:10',
        image: 'https://picsum.photos/800/600?random=9',
        thumbnail: '',
        note: '測試舊資料（無縮圖）'
    }
];

let allData = [];
let filteredData = [];

// DOM 元素
let loadingIndicator, errorMessage, errorText, tableBody, noDataMessage;
let totalCount, todayCount, lastUpdateTime;
let searchDate, searchKeyword;
let lightbox, lightboxImg, lightboxCaption;

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    initElements();
    attachEventListeners();
    loadData();
});

function initElements() {
    loadingIndicator = document.getElementById('loadingIndicator');
    errorMessage = document.getElementById('errorMessage');
    errorText = document.getElementById('errorText');
    tableBody = document.getElementById('tableBody');
    noDataMessage = document.getElementById('noDataMessage');
    
    totalCount = document.getElementById('totalCount');
    todayCount = document.getElementById('todayCount');
    lastUpdateTime = document.getElementById('lastUpdateTime');
    
    searchDate = document.getElementById('searchDate');
    searchKeyword = document.getElementById('searchKeyword');
    
    lightbox = document.getElementById('lightbox');
    lightboxImg = document.getElementById('lightboxImg');
    lightboxCaption = document.getElementById('lightboxCaption');
}

function attachEventListeners() {
    document.getElementById('searchBtn').addEventListener('click', applyFilters);
    document.getElementById('resetBtn').addEventListener('click', resetFilters);
    document.getElementById('refreshBtn').addEventListener('click', loadData);
    
    document.querySelector('.lightbox-close').addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', (e) => {
        if (e.target.id === 'lightbox') closeLightbox();
    });
}

// 解析 CSV 資料
function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    const data = [];
    
    // 跳過標題列 (第一行)
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        // 簡單的 CSV 解析 (假設沒有逗號在欄位內)
        const columns = line.split(',');
        
        if (columns.length >= 4) {
            // 新格式：日期, 時間, 原圖url, 縮圖url, 備註
            // 舊格式：日期, 時間, 原圖url, 備註
            const hasThumb = columns.length >= 5;
            
            data.push({
                date: columns[0].trim(),
                time: columns[1].trim(),
                image: columns[2].trim(),
                thumbnail: hasThumb ? columns[3].trim() : columns[2].trim(), // 舊資料用原圖
                note: hasThumb ? columns[4].trim() : columns[3].trim()
            });
        }
    }
    
    return data;
}

async function loadData() {
    showLoading(true);
    hideError();
    
    try {
        if (USE_FAKE_DATA) {
            await new Promise(resolve => setTimeout(resolve, 800));
            allData = [...FAKE_DATA];
        } else {
            // 從 Google Sheets 讀取 CSV
            const response = await fetch(GOOGLE_SHEET_CSV_URL);
            
            if (!response.ok) {
                throw new Error(`HTTP 錯誤! 狀態: ${response.status}`);
            }
            
            const csvText = await response.text();
            allData = parseCSV(csvText);
            
            if (allData.length === 0) {
                throw new Error('CSV 資料為空或格式不正確');
            }
        }
        
        filteredData = [...allData];
        updateStatistics();
        renderTable();
        
    } catch (error) {
        showError(`載入資料失敗: ${error.message}`);
        console.error('Error loading data:', error);
    } finally {
        showLoading(false);
    }
}

function updateStatistics() {
    const today = new Date().toISOString().split('T')[0];
    const todayData = allData.filter(item => item.date === today);
    
    totalCount.textContent = allData.length;
    todayCount.textContent = todayData.length;
    lastUpdateTime.textContent = new Date().toLocaleTimeString('zh-TW');
}

function renderTable() {
    tableBody.innerHTML = '';
    
    if (filteredData.length === 0) {
        noDataMessage.style.display = 'block';
        return;
    }
    
    noDataMessage.style.display = 'none';
    
    filteredData.forEach((item, index) => {
        const row = document.createElement('tr');
        // 優先使用縮略圖，如果縮略圖為空或與原圖相同則使用原圖
        const displayImg = (item.thumbnail && item.thumbnail !== item.image) ? item.thumbnail : item.image;
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${item.date}</td>
            <td>${item.time}</td>
            <td>
                <img src="${displayImg}" 
                     data-fullsize="${item.image}"
                     alt="火車圖片" 
                     class="train-image"
                     loading="lazy"
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%2275%22%3E%3Crect fill=%22%23ddd%22 width=%22100%22 height=%2275%22/%3E%3Ctext fill=%22%23999%22 x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22%3E圖片載入失敗%3C/text%3E%3C/svg%3E'"
                     onclick="openLightbox(this.dataset.fullsize, '${item.date} ${item.time}')">
            </td>
            <td>${item.note}</td>
        `;
        tableBody.appendChild(row);
    });
}

function applyFilters() {
    const dateValue = searchDate.value;
    const keywordValue = searchKeyword.value.toLowerCase().trim();
    
    filteredData = allData.filter(item => {
        const dateMatch = !dateValue || item.date === dateValue;
        const keywordMatch = !keywordValue || item.note.toLowerCase().includes(keywordValue);
        return dateMatch && keywordMatch;
    });
    
    renderTable();
}

function resetFilters() {
    searchDate.value = '';
    searchKeyword.value = '';
    filteredData = [...allData];
    renderTable();
}

function openLightbox(imgSrc, caption) {
    lightbox.style.display = 'flex';
    lightboxImg.src = imgSrc;
    lightboxCaption.textContent = caption;
}

function closeLightbox() {
    lightbox.style.display = 'none';
}

function showLoading(show) {
    loadingIndicator.style.display = show ? 'flex' : 'none';
}

function showError(message) {
    errorText.textContent = message;
    errorMessage.style.display = 'flex';
}

function hideError() {
    errorMessage.style.display = 'none';
}
