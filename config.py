# -*- coding: utf-8 -*-
"""全域設定：分類、匯率、門檻、AI 模型、資料來源。"""

# ---- 8 大實用情境（key -> 顯示名稱 / emoji）----
CATEGORIES = {
    "overseas":          {"label": "海外通用", "emoji": "🌍"},
    "japan_korea":       {"label": "日韓",     "emoji": "🗾"},
    "europe_us":         {"label": "歐美",     "emoji": "🗽"},
    "miles":             {"label": "哩程",     "emoji": "✈️"},
    "online_shopping":   {"label": "網購",     "emoji": "🛒"},
    "mobile_pay":        {"label": "行動支付", "emoji": "📱"},
    "domestic_general":  {"label": "國內無腦", "emoji": "🏠"},
    "delivery_streaming":{"label": "外送影音", "emoji": "🍔"},
}

# ---- 核心換算與篩選規則 ----
# 哩程動態匯率：預設 1 哩 = 0.5 元。可依市場行情調整。
MILE_VALUE_NTD = 0.5

# 門檻過濾：只保留「等值現金回饋率」大於此值的卡片，排除沒有競爭力的廢卡。
MIN_EFFECTIVE_RATE = 1.0  # 單位 %

# 每個情境排行榜取前 N 名
TOP_N = 10
# 主力推薦 / 備用神卡 的分界（1~SPLIT 為主力，SPLIT+1~TOP_N 為備用）
PRIMARY_SPLIT = 5

# ---- 資料來源 ----
# PTT 信用卡版官方 RSS
PTT_RSS_URL = "https://www.ptt.cc/atom/creditcard.xml"
# 只鎖定標題含這些關鍵字的文章
PTT_TITLE_KEYWORDS = ["[情報]", "權益", "[心得]"]
# 保底資料庫路徑
FALLBACK_DB_PATH = "data/fallback_cards.json"

# ---- AI 處理設定 ----
# 多模型備援：主模型掛掉（429/5xx）自動切換到下一個
AI_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro"]
# 遇到 429 流量限制時的冷卻秒數（智慧煞車）
RATE_LIMIT_COOLDOWN_SEC = 60
# 每個模型的最大重試次數
MAX_RETRIES_PER_MODEL = 3
# API Key 由環境變數提供（GitHub Actions Secret）
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"

# ---- 輸出 ----
# 前端讀取的靜態 JSON 產出目錄
OUTPUT_DIR = "docs/data"

# ---- Telegram 更新通知（選配）----
# 於 GitHub Actions Secrets 設定；未設定則自動略過通知，不影響建置。
TELEGRAM_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID_ENV = "TELEGRAM_CHAT_ID"
# 網站公開網址（會附在通知訊息裡，方便你點開查看）
SITE_URL = "https://<你的帳號>.github.io/<你的repo>/"
