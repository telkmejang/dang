import os
from dotenv import load_dotenv

load_dotenv()

TARGET_URLS = [url.strip() for url in os.getenv("TARGET_URLS", "").split(",") if url.strip()]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "180"))
