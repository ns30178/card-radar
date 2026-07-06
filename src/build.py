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

    # 用 active_cards：去重 + 正規化 + 過期/停發自動下架（與排行榜一致）
    normalized = logic.active_cards(all_cards)
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
