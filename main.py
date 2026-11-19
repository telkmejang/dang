import json
import os
import requests
from analyzer import analyze_deal
from config import TARGET_URLS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from scraper import fetch_listings
from analyzer import evaluate_deal as analyze_deal

SEEN_FILE = "seen_items.json"


def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_seen(seen_ids: set):
    recent_list = list(seen_ids)[-2000:]
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(recent_list, f, ensure_ascii=False, indent=2)


def send_telegram(item: dict, reason: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"🔔 [알림 테스트] {item['title']} ({item['info']}) - {reason}")
        return

    msg = (
        f"🔥 <b>당근 꿀매 포착!</b>\n\n"
        f"📦 <b>{item['title']}</b>\n"
        f"💰 {item['info']}\n"
        f"🤖 <b>AI 분석:</b> {reason}\n\n"
        f"🔗 <a href='{item['link']}'>매물 바로가기</a>"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"[텔레그램 전송 에러] {e}")


def run_once():
    if not TARGET_URLS:
        print("⚠️ TARGET_URLS가 설정되지 않았습니다. GitHub Secrets를 확인하세요.")
        return

    seen_ids = load_seen()
    initial_count = len(seen_ids)
    print(f"🚀 당근 헌터 1회 스캔 시작 (감시 URL: {len(TARGET_URLS)}개)")

    for url in TARGET_URLS:
        listings = fetch_listings(url)
        new_count = 0

        for item in listings:
            if item["id"] in seen_ids:
                continue

            seen_ids.add(item["id"])
            new_count += 1
            print(f"🆕 새 매물 발견: {item['title']} | {item['info']}")

            analysis = analyze_deal(item)
            if analysis["is_deal"]:
                print(f"✅ 꿀매 판정! 알림 전송 -> {item['title']}")
                send_telegram(item, analysis["reason"])
            else:
                print(f"⏭️ 패스: {analysis['reason']}")

        if new_count == 0:
            print(f"💤 새 매물 없음 ({url})")

    if len(seen_ids) != initial_count:
        save_seen(seen_ids)
        print("💾 seen_items.json 업데이트 완료")


if __name__ == "__main__":
    run_once()
