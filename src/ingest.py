# -*- coding: utf-8 -*-
import json
import os
import sys

try:
    import feedparser
except ImportError:
    feedparser = None

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def load_fallback_cards():
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
    if feedparser is None:
        return []
    try:
        feed = feedparser.parse(config.PTT_RSS_URL)
        if getattr(feed, "bozo", 0) and not feed.entries:
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
        print(f"[ingest] PTT 命中 {len(picked)} 篇文章。")
        return picked
    except Exception as ex:
        print(f"[ingest] PTT 抓取失敗: {ex}")
        return []

def gather():
    return fetch_ptt_entries(), load_fallback_cards()
