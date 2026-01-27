import requests
import hashlib
import os
import time
from datetime import datetime, timezone
import mimetypes
from threading import Thread
from flask import Flask

BOT_TOKEN = "8120207053:AAHq_RmqaWznQyG6E6b6U-DF89r8-IdAjcs"
CHAT_ID = "7530475008"

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

Thread(target=run_web, daemon=True).start()

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

MAX_FILE = 45 * 1024 * 1024

last_scan = datetime.now(timezone.utc)
last_update_id = 0


def now():
    return datetime.now(timezone.utc)


def tg(msg):
    requests.post(f"{TG}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})


def tg_file(path):
    if os.path.getsize(path) > MAX_FILE:
        tg("⚠️ File terlalu besar, tidak dikirim.")
        return
    with open(path, "rb") as f:
        requests.post(
            f"{TG}/sendDocument",
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


def scan_url(url, force=False):
    r = requests.get(url, allow_redirects=True, timeout=60)
    data = r.content

    h = sha(data)
    old = load_state(url)

    changed = force or (h != old)

    if changed:
        save_state(url, h)

        ext = ext_from_response(r)
        name = f"{DOWNLOAD_DIR}/{now().strftime('%Y%m%d_%H%M%S')}_{h[:8]}{ext}"
        open(name, "wb").write(data)

        msg = (
            "🔔 PERUBAHAN TERDETEKSI\n\n"
            f"URL: {url}\n"
            f"HTTP: {r.status_code}\n"
            f"Redirect: {r.url}\n"
            f"Content-Type: {r.headers.get('Content-Type','-')}\n\n"
            f"SHA256:\n{h}\n"
            f"Size: {len(data)} bytes"
        )

        tg(msg)
        tg_file(name)

    return {
        "url": url,
        "status": r.status_code,
        "hash": h[:12],
        "size": len(data),
        "changed": changed
    }


def scan_all(force=False):
    global last_scan
    results = []
    any_change = False

    for u in URLS:
        res = scan_url(u, force)
        results.append(res)
        if res["changed"]:
            any_change = True

    last_scan = now()
    return any_change, results


def poll_commands():
    global last_update_id

    r = requests.get(
        f"{TG}/getUpdates",
        params={"offset": last_update_id + 1, "timeout": 1}
    ).json()

    for u in r.get("result", []):
        last_update_id = u["update_id"]
        text = u.get("message", {}).get("text", "")

        if text == "/health":
            diff = int((now() - last_scan).total_seconds() / 60)
            tg(f"🩺 HEALTH\nTerakhir scan: {diff} menit lalu\nTotal URL: {len(URLS)}")

        elif text == "/cekperubahan":
            tg("🔄 Scan manual dimulai...")
            scan_all(force=True)
            tg("✅ Scan manual selesai")

        elif text == "/status":
            _, res = scan_all(force=False)
            msg = "📊 STATUS\n\n"
            for r2 in res:
                msg += (
                    f"{r2['url']}\n"
                    f"HTTP: {r2['status']}\n"
                    f"SHA: {r2['hash']}...\n"
                    f"Size: {r2['size']} bytes\n\n"
                )
            tg(msg)


tg("🟢 BOT ONLINE")

while True:
    try:
        poll_commands()
        changed, _ = scan_all()
        time.sleep(60 if changed else 600)

    except Exception as e:
        tg("❌ ERROR:\n" + str(e))
        time.sleep(60)
