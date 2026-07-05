# -*- coding: utf-8 -*-
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

PROMPT_TEMPLATE = """你是信用卡回饋資料的結構化引擎。以下是一篇 PTT 信用卡情報文。
請抽取文中「所有提到」的信用卡權益，並輸出**嚴格的 JSON 陣列 (Array of objects)**。如果文中提到 3 張卡，就輸出 3 個物件。

【分類嚴格定義】
"categories" 陣列只能從以下 12 類挑選，請精準對應：
1. cashback (只要主打現金或等值點數回饋皆算)
2. overseas (海外一般) / japan_korea (日韓) / europe_us (歐美)
3. miles (主打哩程累積) / online_shopping (網購、電商)
4. line_pay (限提到 LINE Pay) / jko_pay (限提到街口) / px_pay (限提到全支付) / apple_pay (限提到 Apple Pay 或 AP)
5. domestic_general (國內一般消費) / delivery_streaming (外送與影音)

陣列內每個物件的輸出欄位：
{{
  "id": "英文小寫-連字號 id",
  "name": "卡片全名",
  "bank": "發卡銀行",
  "network": "Visa/Mastercard/JCB",
  "categories": ["依照上述 12 類精準挑選，可複選"],
  "reward_type": "cash | miles | points",
  "scenario_rates": {{"符合的 category_key": 回饋率數字(%)}},
  "base_rate": 基礎回饋率數字,
  "effective_rate": 該卡最高等值現金回饋率數字,
  "mile_spec": {{"ntd_per_mile": 幾元1哩, "program": "航空計畫"}},
  "cap": {{"amount": 每期上限金額或null, "period": "monthly/none", "note": "說明"}},
  "conditions": {{"need_register": true/false, "need_digital_account": true/false, "min_spend": 門檻金額, "mobile_pay_required": true/false}},
  "annual_fee": {{"amount": 年費, "waivable": true/false, "waive_condition": "減免條件"}},
  "summary": "一句話重點摘要",
  "highlights": ["賣點1", "賣點2"],
  "limitations": "把複雜的上限/登錄/門檻限制濃縮成一段白話。若有換行請使用 \\n",
  "valid_until": "YYYY-MM-DD",
  "official_url": "官方介紹網址",
  "travel_insurance": {{"has": true/false, "note": "旅平險說明"}}
}}

若無法判斷為信用卡情報，請輸出 []。
文章標題：{title}
文章內文：{body}
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
    prompt = PROMPT_TEMPLATE.format(
        title=entry.get("title", ""),
        body=entry.get("summary", "")[:4000]
    )
    for model_name in config.AI_MODELS:
        for attempt in range(config.MAX_RETRIES_PER_MODEL):
            try:
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
                text = (resp.text or "").strip()
                if text.startswith("```"):
                    text = text.strip("`").split("\n", 1)[-1]
                    if text.endswith("```"):
                        text = text[:-3]
                
                parsed_arr = json.loads(text)
                if isinstance(parsed_arr, dict): 
                    parsed_arr = [parsed_arr]
                
                valid_cards = []
                for obj in parsed_arr:
                    if obj and obj.get("name"):
                        obj.setdefault("source", entry.get("link", ""))
                        obj["source_type"] = "ptt"
                        valid_cards.append(obj)
                return valid_cards
            except Exception as err:
                if _is_rate_limit(err):
                    time.sleep(config.RATE_LIMIT_COOLDOWN_SEC)
                    continue
                break
    return []

def process_entries(entries):
    if not entries: return []
    if not _configure(): return []
    
    cards = []
    for e in entries:
        results = _call_one(e)
        if results:
            cards.extend(results) 
            
    print(f"[ai] AI 解析出 {len(cards)} 張卡片。")
    return cards
