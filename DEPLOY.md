# 神卡雷達 — 全程在 GitHub 網頁完成的上架手冊（免終端機）

> 目標：**完全不碰本機終端機**，只用瀏覽器在 GitHub 網站上完成部署，並設定成
> 每月 5 號自動更新、更新完成後用 Telegram 通知你。
>
> 你會用到 4 個免費服務：GitHub（放網站+自動化）、Google AI Studio（Gemini 金鑰）、
> Telegram（通知）、cron-job.org（每月定時喚醒）。全部照著章節做即可。

---

## 目錄
1. [先把專案檔案放上 GitHub（純網頁操作）](#step1)
2. [開啟 GitHub Pages 讓網站上線](#step2)
3. [申請 Gemini API 金鑰](#step3)
4. [建立 Telegram Bot、取得通知資訊](#step4)
5. [在 GitHub 設定 Secrets](#step5)
6. [用網頁編輯器改 config.py 的網址](#step6)
7. [手動跑第一次更新（測試）](#step7)
8. [設定 cron-job.org 每月 5 號外部喚醒](#step8)
9. [驗收清單與疑難排解](#step9)
10. [附錄：全部程式碼（可對照或手動貼上）](#step10)

---

<a id="step1"></a>
## 1. 先把專案檔案放上 GitHub（純網頁操作）

### 1-1 建立 Repository
1. 登入 https://github.com → 右上角「**+**」→「**New repository**」。
2. **Repository name** 填 `card-radar`（可自訂）。
3. 選 **Public**（Pages 免費版需公開）。
4. 勾選「**Add a README file**」（讓 repo 先有內容）。
5. 按「**Create repository**」。

### 1-2 用「上傳」把整包檔案丟上去（免終端機、免 Git）
> 我給你的 `credit-card-compare` 資料夾裡有所有檔案。GitHub 網頁支援**直接把資料夾拖進去**，會自動保留子資料夾結構。

1. 在 repo 首頁按「**Add file**」→「**Upload files**」。
2. 打開你電腦上的 `credit-card-compare` 資料夾，把裡面的**所有項目**（`config.py`、`requirements.txt`、`README.md`、`DEPLOY.md`、`data/`、`src/`、`docs/`、`.github/` 等）**全選後一起拖曳**到 GitHub 的上傳框。
   - ⚠️ 拖「資料夾內的東西」，不要多包一層。上傳後 repo 根目錄要能直接看到 `config.py` 與 `docs/`。
   - ⚠️ `.github` 是隱藏資料夾；用「拖曳整包」通常會一起帶上。若沒有，見 1-3 手動補建。
3. 下方「Commit changes」→ 按「**Commit changes**」。等進度跑完。

### 1-3 （若某些檔沒上傳成功）用網頁直接「建立檔案」貼上
GitHub 可以在網頁上直接寫檔案：
1. 「**Add file**」→「**Create new file**」。
2. 檔名欄輸入路徑，用 `/` 會自動建資料夾。例如打 `.github/workflows/build.yml`。
3. 把[附錄](#step10)對應檔案的內容整段貼上 → 「Commit changes」。
4. 大型檔（`data/fallback_cards.json`、`docs/index.html`、`docs/data/*.json`）建議用 1-2 的「Upload files」拖上去，不需手貼。

---

<a id="step2"></a>
## 2. 開啟 GitHub Pages 讓網站上線
1. repo 上方「**Settings**」→ 左側「**Pages**」。
2. 「Build and deployment」→ Source 選「**Deploy from a branch**」。
3. Branch 選「**main**」，資料夾**選 `/docs`** → 「**Save**」。
4. 等 1–2 分鐘，重新整理，頁面上方出現：
   `Your site is live at https://<你的帳號>.github.io/card-radar/`
5. 點開就能看到神卡雷達。（此時顯示的是你上傳時 `docs/data/` 內的資料。）

---

<a id="step3"></a>
## 3. 申請 Gemini API 金鑰（讓 AI 能解析 PTT 新情報）
> 不申請也能跑，只會單用 48 張保底卡；要 AI 自動抓新卡就需要。
1. 前往 https://aistudio.google.com/ ，用 Google 帳號登入。
2. 點「**Get API key**」→「**Create API key**」。
3. 複製金鑰（`AIza...` 開頭），先貼在記事本備用。

---

<a id="step4"></a>
## 4. 建立 Telegram Bot、取得通知資訊
需要兩個東西：**Bot Token** 與 **Chat ID**。

**4-1 取得 Bot Token**
1. Telegram 搜尋 **@BotFather**（有藍勾）→ Start。
2. 輸入 `/newbot` → 依提示取顯示名稱與帳號名（帳號需以 `bot` 結尾，例 `card_radar_notify_bot`）。
3. 成功後會給一串 Token（像 `123456789:AAE...`），複製備用。

**4-2 取得 Chat ID**
1. 先在 Telegram 搜尋你剛建的 bot，按 **Start** 並隨便傳一句「hi」（這步必做，否則 bot 不能傳訊給你）。
2. 搜尋 **@userinfobot** → Start，它會回你的 **Id**（一串數字），那就是 Chat ID，複製備用。

---

<a id="step5"></a>
## 5. 在 GitHub 設定 Secrets（安全存放金鑰）
1. repo →「**Settings**」→ 左側「**Secrets and variables**」→「**Actions**」。
2. 按「**New repository secret**」，逐一新增（名稱要**完全一致**）：

| Name | Value | 必填 |
|---|---|---|
| `GEMINI_API_KEY` | 第 3 步的金鑰 | 想用 AI 才填 |
| `TELEGRAM_BOT_TOKEN` | 第 4-1 的 Token | 想要通知就填 |
| `TELEGRAM_CHAT_ID` | 第 4-2 的 Chat ID | 想要通知就填 |

3. 各按「**Add secret**」。沒填 Telegram 也不影響建置，只是不發通知。

---

<a id="step6"></a>
## 6. 用網頁編輯器改 config.py 的網址
讓 Telegram 通知附上你的網站連結。
1. repo 首頁點進 `config.py` → 右上角**鉛筆圖示（Edit this file）**。
2. 找到最後一行：
   `SITE_URL = "https://<你的帳號>.github.io/<你的repo>/"`
   改成你第 2 步的真實網址，例如：
   `SITE_URL = "https://your-name.github.io/card-radar/"`
3. 右上「**Commit changes...**」→ 確認。

---

<a id="step7"></a>
## 7. 手動跑第一次更新（測試整條流程）
1. repo 上方「**Actions**」。若看到提示，按「**I understand my workflows, enable them**」。
2. 左側點「**Build Card Data**」→ 右側「**Run workflow**」→ 綠色「**Run workflow**」。
3. 等約 1–2 分鐘出現綠色勾勾＝成功。此時：
   - `docs/data/` 會被機器人自動更新並 commit；
   - 你的 Telegram 應收到「✅ 神卡雷達更新完成」。
4. 打開網站確認「資料更新」時間有變。

> 紅色 ❌：點進該次執行看 log。最常見是 Secret 名稱打錯，或 `.github/workflows/build.yml` 沒上傳成功（回第 1、5 步）。

---

<a id="step8"></a>
## 8. 設定 cron-job.org 每月 5 號外部喚醒

**8-1 先在 GitHub 建立 Personal Access Token（給 cron 觸發權限）**
1. GitHub 右上頭像 →「**Settings**」→ 最下「**Developer settings**」。
2. 「**Personal access tokens**」→「**Fine-grained tokens**」→「**Generate new token**」。
3. 設定：Token name `cron-dispatch`；Expiration 選長一點；Repository access 選「Only select repositories」→ 你的 `card-radar`；Permissions →「Repository permissions」→「**Contents**」設 **Read and write**。
4. 「Generate token」→ **複製 token**（只顯示一次）。

**8-2 在 cron-job.org 建立排程**
1. 到 https://cron-job.org 註冊登入 →「**Create cronjob**」。
2. **Title**：`神卡雷達每月更新`
3. **URL**：`https://api.github.com/repos/<你的帳號>/card-radar/dispatches`
4. **Schedule**：選 custom，設 **每月 5 號 09:00**，時區選 **Asia/Taipei**。
5. 展開「**Advanced**」：
   - **Request method**：**POST**
   - **Headers**（逐條新增）：
     | Key | Value |
     |---|---|
     | `Accept` | `application/vnd.github+json` |
     | `Authorization` | `Bearer <你8-1的token>` |
     | `X-GitHub-Api-Version` | `2022-11-28` |
     | `User-Agent` | `cron-job` |
   - **Request body**：`{"event_type":"rebuild"}`
6. 儲存。可按「**TEST RUN**」測試，回 GitHub Actions 應看到一次由 `repository_dispatch` 觸發的執行。

> 對應關係：body 的 `{"event_type":"rebuild"}` ⟷ `build.yml` 的 `repository_dispatch: types: [rebuild]`，兩邊字串要一致。

---

<a id="step9"></a>
## 9. 驗收清單與疑難排解

**完成後應該是：**
- 打開 `https://<你的帳號>.github.io/card-radar/` 看得到 8 大情境 + 比較總表。
- 卡片點開有「旅遊平安險（含額度）」與「🔗 前往官方網站參閱」按鈕，且連結直接到那張卡。
- 每月 5 號早上自動更新，更新完 Telegram 收到通知。

| 症狀 | 解法 |
|---|---|
| 網站 404 | Pages 資料夾要選 `/docs`；剛存檔需等 1–2 分鐘。 |
| 有頁面沒資料 | 先手動 Run 一次 workflow（第 7 步）產生 `docs/data`。 |
| Actions 紅字 | 點 log 看；多半 Secret 名稱拼錯或 workflow 檔沒上傳。 |
| 沒收到 Telegram | 是否已先對 bot 按 Start 傳訊；Token/Chat ID 是否正確。 |
| cron 沒反應 | 檢查 PAT 權限 Contents=Read and write、URL 帳號/repo 名、body 是否 `{"event_type":"rebuild"}`。 |

**費用**：以上服務個人用量皆可維持免費。

---

<a id="step10"></a>
## 10. 附錄：全部程式碼（可對照或手動貼上）

> 大型檔（`data/fallback_cards.json`、`docs/index.html`、`docs/data/*.json`）請用第 1-2 步「Upload files」拖曳上傳，不需手貼。
> 以下為其餘核心程式碼，若你想用「Create new file」手動建立，直接整段複製貼上即可。

### `requirements.txt`

```text
feedparser>=6.0.0
google-generativeai>=0.7.0
```

### `config.py`

```python
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
```

### `.github/workflows/build.yml`

```yaml
name: Build Card Data

# 運作週期：
#  1) 由 cron-job.org 每月（或自訂時間）以 repository_dispatch 從外部喚醒
#  2) 內建 schedule 作為保險（每月 5 號 01:00 UTC = 台灣時間早上 09:00）
#  3) 可手動觸發
on:
  repository_dispatch:
    types: [rebuild]
  schedule:
    # 每月 5 號 09:00 (台灣) 更新；cron 用 UTC，故設 01:00
    - cron: "0 1 5 * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install deps
        run: pip install -r requirements.txt

      - name: Build static JSON
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python -m src.build

      - name: Commit & push data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/data
          git diff --staged --quiet || git commit -m "chore: auto-update card data [skip ci]"
          git push
```

### `src/ingest.py`

```python
# -*- coding: utf-8 -*-
"""資料獲取層 (Data Ingestion)。

策略：
1. 主要來源：解析 PTT 信用卡版官方 RSS，鎖定標題含 [情報] / 權益 的新文章。
2. 保底機制：無論 PTT 是否成功，都載入「硬體級神卡資料庫」墊檔，
   確保畫面永不開天窗（至少 40~50 張卡）。
"""
import json
import os
import sys

try:
    import feedparser
except ImportError:  # 允許在未安裝時仍能載入保底資料庫
    feedparser = None

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def load_fallback_cards():
    """載入硬體級保底神卡資料庫。"""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        config.FALLBACK_DB_PATH,
    )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cards = data.get("cards", [])
    print(f"[ingest] 已載入保底資料庫 {len(cards)} 張卡片。")
    return cards


def fetch_ptt_entries():
    """抓取 PTT RSS 中符合關鍵字的文章（標題 + 內文 + 連結）。

    回傳 list[dict]，失敗時回傳空 list（交由保底機制接手）。
    """
    if feedparser is None:
        print("[ingest] 未安裝 feedparser，跳過 PTT 抓取。")
        return []
    try:
        feed = feedparser.parse(config.PTT_RSS_URL)
        if getattr(feed, "bozo", 0) and not feed.entries:
            print(f"[ingest] PTT RSS 解析異常：{getattr(feed, 'bozo_exception', '')}")
            return []
        picked = []
        for e in feed.entries:
            title = e.get("title", "")
            if any(k in title for k in config.PTT_TITLE_KEYWORDS):
                picked.append({
                    "title": title,
                    "summary": e.get("summary", ""),
                    "link": e.get("link", ""),
                })
        print(f"[ingest] PTT 命中 {len(picked)} 篇符合關鍵字的文章。")
        return picked
    except Exception as ex:  # noqa: BLE001 - 任何錯誤都墊檔
        print(f"[ingest] PTT 抓取失敗，改用保底資料庫：{ex}")
        return []


def gather():
    """統一入口：回傳 (ptt_entries, fallback_cards)。"""
    return fetch_ptt_entries(), load_fallback_cards()


if __name__ == "__main__":
    entries, fallback = gather()
    print(f"PTT 文章 {len(entries)} 篇 / 保底卡片 {len(fallback)} 張")
```

### `src/ai_processor.py`

```python
# -*- coding: utf-8 -*-
"""AI 處理大腦 (AI Processing)。

職責：把 PTT 半結構化文章，抽取/正規化成與保底資料庫相同 schema 的卡片物件。

容錯機制（解決伺服器不穩定的痛點）：
- 智慧煞車：遇到 429 流量限制，自動冷卻休眠 RATE_LIMIT_COOLDOWN_SEC 秒。
- 多模型備援：主模型（flash）掛掉就自動換備援（pro）。
- 全程 try/except：AI 整段失敗也不會中斷主流程（回傳空 list，交由保底墊檔）。
"""
import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

try:
    import google.generativeai as genai
except ImportError:
    genai = None


PROMPT_TEMPLATE = """你是信用卡回饋資料的結構化引擎。以下是 PTT 信用卡版的一篇文章。
請抽取其中「單一張信用卡」的回饋資訊，並輸出**嚴格 JSON**（不要 markdown 圍欄）。

輸出欄位：
{{
  "id": "英文小寫-連字號 id",
  "name": "卡片全名",
  "bank": "發卡銀行",
  "network": "Visa/Mastercard/JCB",
  "categories": ["從這 8 類挑選: overseas, japan_korea, europe_us, miles, online_shopping, mobile_pay, domestic_general, delivery_streaming"],
  "reward_type": "cash | miles | points",
  "scenario_rates": {{"該卡適用情境": 回饋率數字(%)}},
  "base_rate": 基礎回饋率數字,
  "effective_rate": 該卡最高等值現金回饋率數字,
  "mile_spec": {{"ntd_per_mile": 幾元1哩(哩程卡才填), "program": "航空計畫"}},
  "cap": {{"amount": 每期上限金額或null, "period": "monthly/none", "note": "說明"}},
  "conditions": {{"need_register": true/false, "need_digital_account": true/false, "min_spend": 門檻金額, "mobile_pay_required": true/false}},
  "annual_fee": {{"amount": 年費, "waivable": true/false, "waive_condition": "減免條件"}},
  "summary": "一句話重點摘要（給前端當標題）",
  "highlights": ["賣點1", "賣點2"],
  "limitations": "把複雜的上限/登錄/門檻限制濃縮成一段白話",
  "valid_until": "YYYY-MM-DD 活動到期日",
  "official_url": "該卡發卡銀行的官方介紹網址(找不到就填銀行信用卡首頁)",
  "travel_insurance": {{"has": true/false, "note": "旅遊平安險/旅遊不便險說明，沒有就寫無"}},
  "source_type": "ptt"
}}

若文章無法判斷為單一張卡的回饋情報，請輸出 {{}}。
文章標題：{title}
文章內文：{body}
來源連結：{link}
"""


def _configure():
    api_key = os.environ.get(config.GEMINI_API_KEY_ENV, "")
    if genai is None or not api_key:
        return False
    genai.configure(api_key=api_key)
    return True


def _is_rate_limit(err) -> bool:
    s = str(err).lower()
    return "429" in s or "quota" in s or "rate" in s or "resource_exhausted" in s


def _call_one(entry):
    """對單篇文章跑 AI，含多模型備援 + 智慧煞車。回傳 dict 或 None。"""
    prompt = PROMPT_TEMPLATE.format(
        title=entry.get("title", ""),
        body=entry.get("summary", "")[:4000],
        link=entry.get("link", ""),
    )
    for model_name in config.AI_MODELS:                 # 多模型備援
        for attempt in range(config.MAX_RETRIES_PER_MODEL):
            try:
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
                text = (resp.text or "").strip()
                if text.startswith("```"):
                    text = text.strip("`").split("\n", 1)[-1]
                    if text.endswith("```"):
                        text = text[:-3]
                obj = json.loads(text)
                if obj and obj.get("name"):
                    obj.setdefault("source", entry.get("link", ""))
                    obj["source_type"] = "ptt"
                    return obj
                return None
            except Exception as err:                    # noqa: BLE001
                if _is_rate_limit(err):                  # 智慧煞車
                    print(f"[ai] {model_name} 遇到 429，冷卻 {config.RATE_LIMIT_COOLDOWN_SEC}s…")
                    time.sleep(config.RATE_LIMIT_COOLDOWN_SEC)
                    continue
                print(f"[ai] {model_name} 第 {attempt+1} 次失敗：{err}")
                break  # 非流量問題 → 換下一個模型
    return None


def process_entries(entries):
    """把 PTT 文章批次轉為卡片 list。任何情況都不拋例外。"""
    if not entries:
        return []
    if not _configure():
        print("[ai] 未設定 GEMINI_API_KEY 或未安裝 SDK，跳過 AI 解析（僅用保底庫）。")
        return []
    cards = []
    for e in entries:
        try:
            card = _call_one(e)
            if card:
                cards.append(card)
        except Exception as err:  # noqa: BLE001
            print(f"[ai] 單篇處理例外，略過：{err}")
    print(f"[ai] AI 解析出 {len(cards)} 張卡片。")
    return cards


if __name__ == "__main__":
    sample = [{"title": "[情報] 某銀行海外 5% 回饋", "summary": "海外實體 5%...", "link": "http://x"}]
    print(process_entries(sample))
```

### `src/logic.py`

```python
# -*- coding: utf-8 -*-
"""核心篩選與換算機制 (Filtering & Logic) — 系統的靈魂。

1. 哩程動態匯率：把 "20 元 1 哩" 換算成等值現金回饋率
   （預設 1 哩 = 0.5 元 → 0.5/20 = 2.5%），讓哩程卡與現金卡在同一排行榜公平競爭。
2. 門檻過濾：只挑總回饋率 > MIN_EFFECTIVE_RATE 的卡片，排除廢卡。
3. 分類制：把卡歸進 8 大情境。
4. 排行榜：每情境取前 TOP_N，拆成主力(1~5) / 備用(6~10)。
5. 推薦邏輯：依使用者消費輪廓動態計算「最適合 / 最高回饋」。
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def mile_to_cash_rate(ntd_per_mile, mile_value=config.MILE_VALUE_NTD):
    """幾元 1 哩 → 等值現金回饋率(%)。20 元 1 哩、1 哩 0.5 元 → 2.5%。"""
    if not ntd_per_mile or ntd_per_mile <= 0:
        return 0.0
    return round((mile_value / ntd_per_mile) * 100, 2)


def normalize_card(card):
    """補齊 effective_rate（哩程卡自動換算）並回傳同一物件。"""
    if card.get("reward_type") == "miles":
        spec = card.get("mile_spec") or {}
        rate = mile_to_cash_rate(spec.get("ntd_per_mile"))
        if rate:
            card["effective_rate"] = rate
            # 讓哩程卡在 miles/overseas 情境也有可比數字
            for cat in card.get("categories", []):
                card.setdefault("scenario_rates", {})
                if card["scenario_rates"].get(cat, 0) == 0:
                    card["scenario_rates"][cat] = rate
    if "effective_rate" not in card or card["effective_rate"] is None:
        rates = card.get("scenario_rates", {}) or {}
        card["effective_rate"] = max(rates.values()) if rates else card.get("base_rate", 0)
    return card


def dedupe(cards):
    """依 id 去重；PTT 新資料優先蓋過保底資料。"""
    merged = {}
    for c in cards:
        cid = c.get("id") or c.get("name")
        if not cid:
            continue
        if cid not in merged or c.get("source_type") == "ptt":
            merged[cid] = c
    return list(merged.values())


def filter_and_rank(cards):
    """輸出 {category: {"primary": [...], "backup": [...]}}。"""
    cards = [normalize_card(c) for c in cards]
    cards = dedupe(cards)
    # 門檻過濾
    cards = [c for c in cards if (c.get("effective_rate") or 0) > config.MIN_EFFECTIVE_RATE]

    result = {}
    for cat in config.CATEGORIES:
        pool = [c for c in cards if cat in c.get("categories", [])]
        pool.sort(key=lambda c: c.get("scenario_rates", {}).get(cat, c.get("effective_rate", 0)), reverse=True)
        top = pool[: config.TOP_N]
        result[cat] = {
            "label": config.CATEGORIES[cat]["label"],
            "emoji": config.CATEGORIES[cat]["emoji"],
            "primary": top[: config.PRIMARY_SPLIT],
            "backup": top[config.PRIMARY_SPLIT : config.TOP_N],
        }
    return result


def _capped_reward(spend, rate_pct, cap):
    """單一情境的實拿回饋（考慮月上限）。"""
    raw = spend * rate_pct / 100.0
    if cap and cap.get("amount"):
        return min(raw, cap["amount"])
    return raw


def recommend(cards, spend_profile):
    """最佳推薦邏輯。

    spend_profile: {category: 每月消費金額}
    回傳依「預估每月總回饋」由高到低排序的卡片清單，附上明細。
    這是「哪張最適合 / 最高回饋」的動態計算核心。
    """
    cards = [normalize_card(c) for c in dedupe(cards)]
    scored = []
    for c in cards:
        rates = c.get("scenario_rates", {}) or {}
        total = 0.0
        breakdown = {}
        for cat, spend in spend_profile.items():
            if spend <= 0 or cat not in rates:
                continue
            r = _capped_reward(spend, rates[cat], c.get("cap"))
            if r > 0:
                breakdown[cat] = round(r, 1)
                total += r
        if total > 0:
            scored.append({
                "id": c.get("id"),
                "name": c.get("name"),
                "reward_type": c.get("reward_type"),
                "monthly_reward": round(total, 1),
                "annual_reward": round(total * 12, 1),
                "breakdown": breakdown,
                "summary": c.get("summary", ""),
            })
    scored.sort(key=lambda x: x["monthly_reward"], reverse=True)
    return scored


if __name__ == "__main__":
    assert mile_to_cash_rate(20) == 2.5, "20 元 1 哩應換算為 2.5%"
    assert mile_to_cash_rate(10) == 5.0
    print("logic 自我測試通過：20 元 1 哩 = 2.5%，10 元 1 哩 = 5.0%")
```

### `src/build.py`

```python
# -*- coding: utf-8 -*-
"""主流程：抓取 → AI 解析 → 合併保底 → 換算篩選排序 → 拋轉靜態 JSON → Telegram 通知。

由 GitHub Actions（cron-job.org 每月喚醒）執行。
產出：
- docs/data/all_cards.json          全部通過門檻的卡片
- docs/data/<category>_top10.json   每情境前 10 名（含主力/備用拆分）
- docs/data/index.json              情境清單 + 更新時間 + 免責聲明
"""
import datetime
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src import ingest, ai_processor, logic

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _write_json(rel_path, obj):
    path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[build] 寫出 {rel_path}")


def notify_telegram(text):
    """建置完成後推播 Telegram。未設定 token/chat_id 則自動略過，且絕不讓通知失敗中斷流程。"""
    token = os.environ.get(config.TELEGRAM_TOKEN_ENV, "")
    chat_id = os.environ.get(config.TELEGRAM_CHAT_ID_ENV, "")
    if not token or not chat_id:
        print("[notify] 未設定 Telegram Secrets，略過通知。")
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }).encode()
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=20) as r:
            print(f"[notify] Telegram 已送出（HTTP {r.status}）。")
    except Exception as ex:  # noqa: BLE001 - 通知失敗不影響建置成敗
        print(f"[notify] Telegram 發送失敗（略過）：{ex}")


def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1) 資料獲取層：PTT + 保底
    ptt_entries, fallback_cards = ingest.gather()

    # 2) AI 處理大腦：把 PTT 文章轉成卡片（失敗自動空手而回）
    ptt_cards = ai_processor.process_entries(ptt_entries)

    # 3) 合併（PTT 新資料 + 保底墊檔）
    all_cards = ptt_cards + fallback_cards
    print(f"[build] 合併後共 {len(all_cards)} 張（PTT {len(ptt_cards)} + 保底 {len(fallback_cards)}）。")

    # 4) 換算 + 門檻過濾 + 分類排序
    ranked = logic.filter_and_rank(all_cards)

    # 5) 拋轉靜態 JSON（前端展示層直接讀取）
    disclaimer = "本站回饋資訊僅供參考，實際權益以各發卡銀行公告為準。"
    index = {"updated_at": now, "disclaimer": disclaimer, "categories": []}
    for cat, data in ranked.items():
        _write_json(f"{config.OUTPUT_DIR}/{cat}_top10.json", {
            "category": cat, "label": data["label"], "emoji": data["emoji"],
            "updated_at": now, "primary": data["primary"], "backup": data["backup"],
        })
        index["categories"].append({
            "key": cat, "label": data["label"], "emoji": data["emoji"],
            "count": len(data["primary"]) + len(data["backup"]),
        })

    normalized = [logic.normalize_card(c) for c in logic.dedupe(all_cards)]
    _write_json(f"{config.OUTPUT_DIR}/all_cards.json", {
        "updated_at": now, "disclaimer": disclaimer, "cards": normalized,
    })
    _write_json(f"{config.OUTPUT_DIR}/index.json", index)
    print("[build] 完成。")

    # 6) Telegram 通知（含本月 PTT 新卡清單，讓你一眼看出資料有沒有長新的）
    new_names = [c.get("name", "") for c in ptt_cards if c.get("name")]
    if new_names:
        shown = "、".join(new_names[:8]) + ("…" if len(new_names) > 8 else "")
        new_line = f"🆕 本月 PTT 新卡（{len(new_names)}）：{shown}\n"
    else:
        new_line = "🆕 本月無 PTT 新卡，維持既有資料\n"
    msg = (
        "✅ <b>神卡雷達更新完成</b>\n"
        f"🕒 時間：{now}\n"
        f"📊 收錄卡片：{len(normalized)} 張（PTT 新增 {len(ptt_cards)} / 保底 {len(fallback_cards)}）\n"
        f"{new_line}"
        f"🔗 前往查看：{config.SITE_URL}"
    )
    notify_telegram(msg)


if __name__ == "__main__":
    main()
```

