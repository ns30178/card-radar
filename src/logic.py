# -*- coding: utf-8 -*-
import os
import sys
import re
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def mile_to_cash_rate(ntd_per_mile, mile_value=config.MILE_VALUE_NTD):
    if not ntd_per_mile or ntd_per_mile <= 0: return 0.0
    return round((mile_value / ntd_per_mile) * 100, 2)

def normalize_card(card):
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

def clean_card_name(name):
    name = re.sub(r'^(台北富邦|富邦|國泰世華|國泰|玉山銀行|玉山|台新銀行|台新|中國信託|中信)', '', name)
    return name.replace(" ", "").lower()

def dedupe(cards):
    merged = {}
    for c in cards:
        raw_name = c.get("name")
        if not raw_name: continue
        match_id = clean_card_name(raw_name)
        if match_id not in merged or c.get("source_type") == "ptt":
            merged[match_id] = c
    return list(merged.values())

def filter_and_rank(cards):
    cards = [normalize_card(c) for c in cards]
    cards = dedupe(cards)
    
    today = datetime.now().strftime("%Y-%m-%d")
    valid_cards = []
    for c in cards:
        valid_until = c.get("valid_until", "2099-12-31")
        if valid_until and valid_until < today:
            continue
        if (c.get("effective_rate") or 0) <= config.MIN_EFFECTIVE_RATE:
            continue
        valid_cards.append(c)

    result = {}
    for cat in config.CATEGORIES:
        pool = [c for c in valid_cards if cat in c.get("categories", [])]
        pool.sort(key=lambda c: c.get("scenario_rates", {}).get(cat, c.get("effective_rate", 0)), reverse=True)
        top = pool[: config.TOP_N]
        result[cat] = {
            "label": config.CATEGORIES[cat]["label"],
            "emoji": config.CATEGORIES[cat]["emoji"],
            "primary": top[: config.PRIMARY_SPLIT],
            "backup": top[config.PRIMARY_SPLIT : config.TOP_N],
        }
    return result
