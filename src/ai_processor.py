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
