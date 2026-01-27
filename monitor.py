import requests
import hashlib
import os
import time
from datetime import datetime
import mimetypes

BOT_TOKEN = "8120207053:AAHq_RmqaWznQyG6E6b6U-DF89r8-IdAjcs"
CHAT_ID = "7530475008"

MIME_MAP = {
    "text/html": ".html",
    "text/plain": ".txt",
    "application/pdf": ".pdf",
    "application/zip": ".zip",
    "application/x-zip-compressed": ".zip",
    "application/vnd.android.package-archive": ".apk",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
}

URLS = [
    "https://pusatkode.com/081317155457",
    "https://pusatkode.com/B6yadxhk.png"
]

STATE_DIR = "state"
DOWNLOAD_DIR = "downloads"

os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

MAX_FILE = 45 * 1024 * 1024  # 45MB telegram safe


def tg(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )


def tg_file(path):
    if os.path.getsize(path) > MAX_FILE:
        tg("⚠️ File terlalu besar, tidak dikirim.")
        return

    with open(path, "rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
            data={"chat_id": CHAT_ID},
            files={"document": f}
        )


def sha(data):
    return hashlib.sha256(data).hexdigest()


def state_path(k):
    return f"{STATE_DIR}/{hashlib.md5(k.encode()).hexdigest()}.txt"


def load_state(k):
    p = state_path(k)
    if os.path.exists(p):
        return open(p).read().strip()
    return ""


def save_state(k, v):
    open(state_path(k), "w").write(v)


def ext_from_response(resp):
    path = resp.url.split("?")[0]
    url_ext = os.path.splitext(path)[1]
    if url_ext:
        return url_ext

    ctype = resp.headers.get("Content-Type", "").split(";")[0]
    if ctype in MIME_MAP:
        return MIME_MAP[ctype]

    guess = mimetypes.guess_extension(ctype)
    if guess:
        return guess

    return ".bin"


def in_fast_window():
    now = datetime.utcnow() + timedelta(hours=7)  # WIB
    return now.hour == 20 and 40 <= now.minute <= 50


def check(url):
    r = requests.get(url, allow_redirects=True, timeout=60)
    data = r.content

    h = sha(data)
    old = load_state(url)

    if h != old:
        save_state(url, h)

        ext = ext_from_response(r)
        name = f"{DOWNLOAD_DIR}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{h[:8]}{ext}"
        open(name, "wb").write(data)

        msg = (
            "🔔 PERUBAHAN TERDETEKSI\n\n"
            f"URL: {url}\n"
            f"Waktu UTC: {datetime.utcnow().isoformat()}\n\n"
            f"HTTP Status: {r.status_code}\n"
            f"Redirect: {r.url}\n"
            f"Content-Type: {r.headers.get('Content-Type','-')}\n\n"
            f"SHA256:\n{h}\n"
            f"Ukuran: {len(data)} bytes"
        )

        tg(msg)
        tg_file(name)
        return True

    return False


tg("🟢 BOT ONLINE")

while True:
    changed = False

    for u in URLS:
        try:
            if check(u):
                changed = True
        except Exception as e:
            tg("❌ Error:\n" + str(e))

    time.sleep(60 if changed else 600)
