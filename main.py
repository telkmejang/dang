import os
import re
import json
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
from analyzer import analyze_deal

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SEEN_FILE = "seen_items.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )
}

TARGET_BRANDS = [
    # 1. 당근 헐값/빈티지 발굴 최다 (10)
    "아크테릭스", "파타고니아", "몽벨", "노스페이스", "버버리",
    "폴로", "바버", "리바이스", "칼하트", "오클리",
    # 2. 급처 매물 다수 · 고마진 아카이브/컨템 (10)
    "스톤아일랜드", "CP컴퍼니", "메종마르지엘라", "아워레가시", "아크네스튜디오",
    "프라다", "비비안웨스트우드", "꼼데가르송", "살로몬", "미하라야스히로",
    # 3. 고회전 스트릿 · 일본 도메스틱 (10)
    "스투시", "슈프림", "팔라스", "니들스", "캐피탈",
    "휴먼메이드", "베이프", "디스이즈네버댓", "언더커버", "요지야마모토",
]


def load_seen() -> set:
    if not os.path.exists(SEEN_FILE):
        return set()
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(seen_set: set):
    recent_list = list(seen_set)[-5000:]
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(recent_list, f, ensure_ascii=False, indent=2)


def fetch_karrot(brand: str) -> list[dict]:
    encoded = urllib.parse.quote(brand)
    url = f"https://www.daangn.com/kr/buy-sell/?search={encoded}"
    items = []

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        for a_tag in soup.select("a[href*='/kr/buy-sell/']"):
            href = a_tag.get("href", "")
            match = re.search(r"/kr/buy-sell/([^/?#]+)", href)
            if not match:
                continue

            slug = match.group(1)
            text_lines = [t.strip() for t in a_tag.stripped_strings if t.strip()]
            if len(text_lines) < 2:
                continue

            title = text_lines[0]
            price = next((t for t in text_lines if "원" in t or "나눔" in t), "가격미상")
            full_url = f"https://www.daangn.com{href}" if href.startswith("/") else href

            items.append({
                "unique_id": f"karrot:{slug}",
                "brand": brand,
                "title": title,
                "price": price,
                "description": " / ".join(text_lines[1:4]),
                "url": full_url,
            })
    except Exception as e:
        print(f"[당근 수집 오류 - {brand}] {e}")

    return items[:15]


def send_telegram(item: dict, reason: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[경고] 텔레그램 토큰 또는 채팅 ID가 설정되지 않았습니다.")
        return

    text = (
        f"🥕 <b>[당근 사입 꿀매 포착]</b>\n\n"
        f"🏷 <b>브랜드:</b> {item['brand']}\n"
        f"📦 <b>상품명:</b> {item['title']}\n"
        f"💰 <b>가격:</b> {item['price']}\n"
        f"💡 <b>판정:</b> {reason}\n\n"
        f"🔗 <a href=\"{item['url']}\">당근 매물 바로가기</a>"
    )

    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            api_url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=10,
        )
    except Exception as e:
        print(f"[텔레그램 전송 오류] {e}")


def main():
    seen = load_seen()
    new_alerts = 0
    print(f"당근마켓 탐색 시작 | 대상 브랜드: {len(TARGET_BRANDS)}개")

    for brand in TARGET_BRANDS:
        items = fetch_karrot(brand)
        for item in items:
            uid = item["unique_id"]
            if uid in seen:
                continue

            seen.add(uid)
            is_deal, reason = analyze_deal(item)
            if is_deal:
                send_telegram(item, reason)
                new_alerts += 1
                print(f"[알림 발송] {item['title']} ({item['price']})")

        time.sleep(0.8)

    save_seen(seen)
    print(f"탐색 완료. 신규 사입 알림: {new_alerts}건")


if __name__ == "__main__":
    main()