# -*- coding: utf-8 -*-
"""AI 處理大腦 (AI Processing)。

職責：把 PTT 半結構化文章，抽取/正規化成與保底資料庫相同 schema 的卡片物件。
一篇情報文常同時提到「多家銀行/多張卡」，因此要求 AI 一次輸出 **JSON 陣列**，
避免只抓第一張、漏掉其餘、或把多張卡權益縫合成一張「幻覺卡」。

容錯機制：
- 智慧煞車：遇到 429 流量限制，自動冷卻休眠 RATE_LIMIT_COOLDOWN_SEC 秒。
- 多模型備援：主模型（flash）掛掉就自動換備援（pro）。
- 全程 try/except：AI 整段失敗也不會中斷主流程（回傳空 list，交由保底墊檔）。

抗幻覺設計：
- 明確要求「只擷取文章實際出現的卡；未提及的欄位一律填 null」。
- 禁止把不同卡的權益混寫成一張；每張卡必須能對應文章某段落。
- 後處理再做結構檢查，欄位不合規則丟棄該張，寧缺勿假。
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


PROMPT_TEMPLATE = """你是嚴謹的信用卡回饋資料結構化引擎。以下是一篇 PTT 信用卡版文章，
內容可能同時提到「多家銀行」或「多張卡片」。

任務：把文章中**每一張明確出現的信用卡**都抽取出來，輸出成一個 **JSON 陣列**。

【鐵則（務必遵守，違反即視為錯誤）】
1. 只輸出文章「實際提到」的真實卡片；一張卡一個物件，不要遺漏任何一張。
2. **嚴禁把不同卡的權益混在一起**變成一張卡；每張卡的數字都必須來自該卡對應段落。
3. 文章沒寫到的欄位**一律填 null**，不要臆測、不要用常識補、不要編造數字。
4. 若整篇文章沒有任何可辨識的單卡回饋資訊，輸出空陣列 []。
5. 只輸出 JSON 陣列本身，不要加任何說明文字或 markdown 圍欄。

【每張卡的欄位】
{{
  "name": "卡片全名(含銀行)",
  "bank": "發卡銀行",
  "network": "Visa/Mastercard/JCB 或 null",
  "categories": ["從這 8 類挑選(可多選): overseas, japan_korea, europe_us, miles, online_shopping, mobile_pay, domestic_general, delivery_streaming"],
  "reward_type": "cash | miles | points",
  "scenario_rates": {{"情境key": 回饋率數字(%)}},
  "base_rate": 基礎回饋率數字或 null,
  "effective_rate": 該卡最高等值現金回饋率數字或 null,
  "mile_spec": {{"ntd_per_mile": 幾元1哩, "program": "航空計畫"}} 或 null,
  "pay_channels": ["行動支付通路,從: line_pay, jko(街口), pxpay(全支付), apple_pay, other 挑選"] 或 [],
  "cap": {{"amount": 每期上限金額或null, "period": "monthly/none", "note": "說明或null"}},
  "conditions": {{"need_register": true/false, "need_digital_account": true/false, "min_spend": 門檻金額, "mobile_pay_required": true/false}},
  "annual_fee": {{"amount": 年費數字, "waivable": true/false, "waive_condition": "減免條件或null"}},
  "summary": "一句話重點摘要",
  "highlights": ["賣點1", "賣點2"],
  "limitations": "把上限/登錄/門檻限制濃縮成白話，未提及填 null",
  "travel_insurance": {{"has": true/false, "amount": "額度字串或null", "note": "說明或null"}},
  "official_url": "該卡官方介紹網址或 null",
  "valid_until": "此活動參考結束日 YYYY-MM-DD 或 null",
  "expires": "此卡/活動確切下架日 YYYY-MM-DD；長期權益填 null"
}}

文章標題：{title}
文章內文：{body}
來源連結：{link}
"""

_ALLOWED_CATS = {"overseas", "japan_korea", "europe_us", "miles",
                 "online_shopping", "mobile_pay", "domestic_general", "delivery_streaming"}
_ALLOWED_PAY = {"line_pay", "jko", "pxpay", "apple_pay", "other"}


def _configure():
    api_key = os.environ.get(config.GEMINI_API_KEY_ENV, "")
    if genai is None or not api_key:
        return False
    genai.configure(api_key=api_key)
    return True


def _is_rate_limit(err) -> bool:
    s = str(err).lower()
    return "429" in s or "quota" in s or "rate" in s or "resource_exhausted" in s


def _strip_fence(text):
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def _valid_card(obj):
    """結構檢查：欄位不合規則回傳 None（寧缺勿假），合規則做輕度清理後回傳。"""
    if not isinstance(obj, dict):
        return None
    name = (obj.get("name") or "").strip()
    bank = (obj.get("bank") or "").strip()
    if not name or not bank:
        return None
    cats = [c for c in (obj.get("categories") or []) if c in _ALLOWED_CATS]
    if not cats:
        return None
    obj["categories"] = cats
    obj["pay_channels"] = [p for p in (obj.get("pay_channels") or []) if p in _ALLOWED_PAY]
    if obj.get("reward_type") not in ("cash", "miles", "points"):
        obj["reward_type"] = "cash"
    obj["source_type"] = "ptt"
    obj["status"] = "active"
    return obj


def _call_one(entry):
    """對單篇文章跑 AI（要求陣列輸出），含多模型備援 + 智慧煞車。回傳 list[dict]。"""
    prompt = PROMPT_TEMPLATE.format(
        title=entry.get("title", ""),
        body=entry.get("summary", "")[:6000],
        link=entry.get("link", ""),
    )
    for model_name in config.AI_MODELS:                 # 多模型備援
        for attempt in range(config.MAX_RETRIES_PER_MODEL):
            try:
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
                data = json.loads(_strip_fence(resp.text))
                if isinstance(data, dict):              # 萬一模型回單一物件也接受
                    data = [data]
                if not isinstance(data, list):
                    return []
                out = []
                for obj in data:
                    card = _valid_card(obj)
                    if card:
                        card.setdefault("source", entry.get("link", ""))
                        out.append(card)
                return out
            except Exception as err:                    # noqa: BLE001
                if _is_rate_limit(err):                 # 智慧煞車
                    print(f"[ai] {model_name} 遇到 429，冷卻 {config.RATE_LIMIT_COOLDOWN_SEC}s…")
                    time.sleep(config.RATE_LIMIT_COOLDOWN_SEC)
                    continue
                print(f"[ai] {model_name} 第 {attempt+1} 次失敗：{err}")
                break                                   # 非流量問題 → 換下一個模型
    return []


def process_entries(entries):
    """把多篇 PTT 文章批次轉為卡片 list（每篇可產生多張卡）。任何情況都不拋例外。"""
    if not entries:
        return []
    if not _configure():
        print("[ai] 未設定 GEMINI_API_KEY 或未安裝 SDK，跳過 AI 解析（僅用保底庫）。")
        return []
    cards = []
    for e in entries:
        try:
            cards.extend(_call_one(e))
        except Exception as err:  # noqa: BLE001
            print(f"[ai] 單篇處理例外，略過：{err}")
    print(f"[ai] AI 解析出 {len(cards)} 張卡片（多卡陣列）。")
    return cards


if __name__ == "__main__":
    sample = [{"title": "[情報] 三家銀行海外權益更新", "summary": "某A卡海外5%...某B卡日韓6%...", "link": "http://x"}]
    print(process_entries(sample))
