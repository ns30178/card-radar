# -*- coding: utf-8 -*-
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

def notify_telegram(text):
    token = os.environ.get(config.TELEGRAM_TOKEN_ENV, "")
    chat_id = os.environ.get(config.TELEGRAM_CHAT_ID_ENV, "")
    if not token or not chat_id: return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=20) as r:
            pass
    except Exception:
        pass

def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ptt_entries, fallback_cards = ingest.gather()
    ptt_cards = ai_processor.process_entries(ptt_entries)
    all_cards = ptt_cards + fallback_cards
    
    ranked = logic.filter_and_rank(all_cards)

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
    
    new_names = [c.get("name", "") for c in ptt_cards if c.get("name")]
    new_line = f"🆕 本期 PTT 新卡（{len(new_names)}）：{'、'.join(new_names[:8])}...\n" if new_names else "🆕 本期無 PTT 新卡\n"
    msg = (f"✅ <b>神卡雷達更新完成</b>\n🕒 時間：{now}\n📊 收錄卡片：{len(normalized)} 張\n{new_line}🔗 前往查看：{config.SITE_URL}")
    notify_telegram(msg)

if __name__ == "__main__":
    main()
