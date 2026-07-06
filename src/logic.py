# -*- coding: utf-8 -*-
"""核心篩選與換算機制 (Filtering & Logic) — 系統的靈魂。

1. 哩程動態匯率：把 "20 元 1 哩" 換算成等值現金回饋率
   （預設 1 哩 = 0.5 元 → 0.5/20 = 2.5%），讓哩程卡與現金卡在同一排行榜公平競爭。
2. 門檻過濾：只挑總回饋率 > MIN_EFFECTIVE_RATE 的卡片，排除廢卡。
3. 分類制：把卡歸進 8 大情境。
4. 排行榜：每情境取前 TOP_N，拆成主力(1~5) / 備用(6~10)。
5. 推薦邏輯：依使用者消費輪廓動態計算「最適合 / 最高回饋」。
6. 過期/停發自動下架：status 非 active 或 expires 已過期 → 自動移除。
7. 強化去重：正規化卡名（去空白、去銀行前綴）+ 銀行別名統一，避免重複卡。
"""
import datetime
import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# ---- 匯率換算 ----
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
            for cat in card.get("categories", []):
                card.setdefault("scenario_rates", {})
                if card["scenario_rates"].get(cat, 0) == 0:
                    card["scenario_rates"][cat] = rate
    if "effective_rate" not in card or card["effective_rate"] is None:
        rates = card.get("scenario_rates", {}) or {}
        card["effective_rate"] = max(rates.values()) if rates else card.get("base_rate", 0)
    return card


# ---- 強化去重：正規化卡名 + 銀行別名 ----
# 銀行別名 → 統一代號（把「台北富邦」與「富邦」視為同一家）
BANK_ALIASES = {
    "台北富邦銀行": "fubon", "台北富邦": "fubon", "富邦銀行": "fubon", "富邦": "fubon",
    "中國信託": "ctbc", "中信銀行": "ctbc", "中信": "ctbc",
    "國泰世華": "cathay", "國泰銀行": "cathay", "國泰": "cathay",
    "台新銀行": "taishin", "台新國際商業銀行": "taishin", "台新": "taishin",
    "玉山銀行": "esun", "玉山": "esun",
    "永豐銀行": "sinopac", "永豐": "sinopac",
    "匯豐銀行": "hsbc", "滙豐": "hsbc", "匯豐": "hsbc",
    "星展銀行": "dbs", "星展（原花旗消金）": "dbs", "星展": "dbs",
    "第一銀行": "first", "第一": "first",
    "合作金庫": "tcb", "合庫": "tcb",
    "兆豐銀行": "mega", "兆豐": "mega",
    "元大銀行": "yuanta", "元大": "yuanta",
    "凱基銀行": "kgi", "凱基": "kgi",
    "華南銀行": "hncb", "華南": "hncb",
    "上海商業儲蓄銀行": "scsb", "上海商銀": "scsb",
    "渣打銀行": "sc", "渣打": "sc",
    "遠東商銀": "feib", "遠東國際商業銀行": "feib", "遠東": "feib",
    "王道銀行": "obank", "王道": "obank",
    "樂天銀行": "rakuten", "樂天": "rakuten",
    "聯邦銀行": "ubot", "聯邦": "ubot",
    "連線商業銀行": "linebank", "LINE Bank": "linebank",
}
# 卡名裡也常帶銀行前綴，正規化時一併移除
_NAME_PREFIXES = sorted(BANK_ALIASES.keys(), key=len, reverse=True)
_STRIP_CHARS = "（）()【】[]／/｜|·．•、,，-—_　 \t"


def _fullwidth_to_half(s):
    return "".join(chr(ord(c) - 0xFEE0) if "！" <= c <= "～" else c for c in s)


def bank_key(bank):
    b = _fullwidth_to_half(bank or "").replace(" ", "")
    for k in _NAME_PREFIXES:
        if k in b:
            return BANK_ALIASES[k]
    return b.lower()


def canonical_name(name):
    """卡名正規化：全形轉半形、去空白/標點、去銀行前綴、轉小寫。"""
    s = _fullwidth_to_half(name or "")
    for p in _NAME_PREFIXES:              # 去銀行名稱前綴（最長優先）
        if s.replace(" ", "").startswith(p):
            s = s.replace(" ", "", 1) if False else s  # noqa
            s = s[s.find(p) + len(p):]
            break
    s = re.sub(r"[%s]" % re.escape(_STRIP_CHARS), "", s)
    s = s.replace("信用卡", "").replace("卡", "")       # 去共通字尾，減少變體
    return s.lower().strip()


def dedupe_key(card):
    """去重鍵 = 統一銀行代號 + 正規化卡名。避免『富邦J卡』vs『台北富邦J卡』被當兩張。"""
    return bank_key(card.get("bank", "")) + "|" + canonical_name(card.get("name", ""))


def dedupe(cards):
    """依 dedupe_key 去重；PTT 新資料優先蓋過保底資料（並保留保底的官方連結等補充欄位）。"""
    merged = {}
    for c in cards:
        key = dedupe_key(c)
        if not key or key == "|":
            key = c.get("id") or c.get("name")
        if key not in merged:
            merged[key] = c
        else:
            old = merged[key]
            # PTT 新資料覆蓋保底；但用保底補齊 PTT 缺的官方連結/旅平險
            if c.get("source_type") == "ptt" and old.get("source_type") != "ptt":
                for fld in ("official_url", "travel_insurance"):
                    if not c.get(fld) and old.get(fld):
                        c[fld] = old[fld]
                merged[key] = c
            # 其餘情況保留先出現者（保底優先於重複的保底）
    return list(merged.values())


# ---- 過期 / 停發自動下架 ----
def is_active(card, today=None):
    """status 非 active，或 expires 已過期 → 視為下架。"""
    if today is None:
        today = datetime.date.today().isoformat()
    if card.get("status") in ("merged", "discontinued", "inactive"):
        return False
    exp = card.get("expires")
    if exp and str(exp) < today:
        return False
    return True


def filter_and_rank(cards):
    """輸出 {category: {"primary": [...], "backup": [...]}}。"""
    cards = [normalize_card(c) for c in cards]
    cards = dedupe(cards)
    cards = [c for c in cards if is_active(c)]                     # 過期/停發自動下架
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
            "backup": top[config.PRIMARY_SPLIT: config.TOP_N],
        }
    return result


def active_cards(cards):
    """回傳去重 + 正規化 + 下架過濾後的完整清單（給前端 all_cards / 現金比較用）。"""
    out = [normalize_card(c) for c in dedupe(cards)]
    return [c for c in out if is_active(c)]


def _capped_reward(spend, rate_pct, cap):
    raw = spend * rate_pct / 100.0
    if cap and cap.get("amount"):
        return min(raw, cap["amount"])
    return raw


def recommend(cards, spend_profile):
    """最佳推薦邏輯（選配後端 API）。"""
    cards = active_cards(cards)
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
                "id": c.get("id"), "name": c.get("name"),
                "reward_type": c.get("reward_type"),
                "monthly_reward": round(total, 1), "annual_reward": round(total * 12, 1),
                "breakdown": breakdown, "summary": c.get("summary", ""),
            })
    scored.sort(key=lambda x: x["monthly_reward"], reverse=True)
    return scored


if __name__ == "__main__":
    assert mile_to_cash_rate(20) == 2.5
    assert canonical_name("台北富邦 J 卡") == canonical_name("富邦J卡"), "去重正規化失敗"
    assert dedupe_key({"bank": "台北富邦銀行", "name": "台北富邦 J 卡"}) == \
           dedupe_key({"bank": "富邦", "name": "富邦J卡"}), "去重鍵應相同"
    assert not is_active({"expires": "2020-01-01"}), "過期卡應下架"
    assert not is_active({"status": "merged"}), "整合卡應下架"
    print("logic 自我測試通過：換算 / 去重正規化 / 過期下架 皆正常")
