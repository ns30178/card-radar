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
