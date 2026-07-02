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
