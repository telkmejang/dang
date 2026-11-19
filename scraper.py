import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def fetch_listings(url: str) -> list[dict]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items = []
        for a_tag in soup.select('a[href*="/articles/"]'):
            href = a_tag.get("href", "")
            match = re.search(r"/articles/([^/?#]+)", href)
            if not match:
                continue

            item_id = match.group(1)
            full_link = f"https://www.daangn.com{href}" if href.startswith("/") else href

            text_parts = [t.strip() for t in a_tag.stripped_strings if t.strip()]
            if not text_parts:
                continue

            title = text_parts[0]
            raw_info = " | ".join(text_parts[1:])

            items.append({
                "id": item_id,
                "title": title,
                "info": raw_info,
                "link": full_link,
            })

        unique_items = {item["id"]: item for item in items}
        return list(unique_items.values())

    except Exception as e:
        print(f"[수집 에러] {url} -> {e}")
        return []
