# -*- coding: utf-8 -*-

CATEGORIES = {
    "cashback":          {"label": "現金回饋", "emoji": "💰"},
    "overseas":          {"label": "海外通用", "emoji": "🌍"},
    "japan_korea":       {"label": "日韓",     "emoji": "🗾"},
    "europe_us":         {"label": "歐美",     "emoji": "🗽"},
    "miles":             {"label": "哩程",     "emoji": "✈️"},
    "online_shopping":   {"label": "網購",     "emoji": "🛒"},
    "line_pay":          {"label": "LINE Pay", "emoji": "🟢"},
    "jko_pay":           {"label": "街口支付", "emoji": "🔴"},
    "px_pay":            {"label": "全支付",   "emoji": "🐶"},
    "apple_pay":         {"label": "Apple Pay","emoji": "🍎"},
    "domestic_general":  {"label": "國內無腦", "emoji": "🏠"},
    "delivery_streaming":{"label": "外送影音", "emoji": "🍔"},
}

MILE_VALUE_NTD = 0.5
MIN_EFFECTIVE_RATE = 1.0  
TOP_N = 10
PRIMARY_SPLIT = 5

PTT_RSS_URL = "https://www.ptt.cc/atom/creditcard.xml"
PTT_TITLE_KEYWORDS = ["[情報]", "權益", "[心得]"]
FALLBACK_DB_PATH = "data/fallback_cards.json"

AI_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro"]
RATE_LIMIT_COOLDOWN_SEC = 60
MAX_RETRIES_PER_MODEL = 3
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"

OUTPUT_DIR = "docs/data"

TELEGRAM_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID_ENV = "TELEGRAM_CHAT_ID"
SITE_URL = "https://ns30178.github.io/card-radar/"
