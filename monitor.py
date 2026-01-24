import requests
import hashlib
import os
import difflib
from datetime import datetime
from playwright.sync_api import sync_playwright

URL = "https://pusatkode.com/081317155457"

STATE_FILE = "last_content.txt"
SCREENSHOT = "screenshot.png"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def send_telegram_text(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text
    }, timeout=10)


def send_telegram_photo(caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(SCREENSHOT, "rb") as img:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "caption": caption
        }, files={"photo": img}, timeout=20)


def take_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, timeout=30000)
        page.screenshot(path=SCREENSHOT, full_page=True)
        browser.close()


def main():
    response = requests.get(URL, timeout=15)
    response.raise_for_status()
    current = response.text.splitlines()

    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            old = f.read().splitlines()
    else:
        old = []

    if old != current:
        diff = difflib.unified_diff(
            old, current,
            fromfile="sebelum",
            tofile="sesudah",
            lineterm=""
        )

        diff_text = "\n".join(list(diff)[:50])  # batasi agar tidak kepanjangan

        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(current))

        take_screenshot()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            f"🔔 PERUBAHAN TERDETEKSI\n"
            f"{URL}\n"
            f"Waktu: {now}\n\n"
            f"Diff (potongan):\n"
            f"{diff_text}"
        )

        send_telegram_text(message)
        send_telegram_photo("Screenshot halaman terbaru")


if __name__ == "__main__":
    main()
