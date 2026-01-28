import requests
import hashlib
import os
import time
from datetime import datetime, timezone
import mimetypes
from flask import Flask
import threading

BOT_TOKEN = "8120207053:AAHq_RmqaWznQyG6E6b6U-DF89r8-IdAjcs"
CHAT_ID = "7530475008"


TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

# ================= CONFIG =================

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

# ========================================

def now():
    return datetime.now(timezone.utc)

def tg(msg):
    requests.post(f"{TG}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})

def tg_file(path):
    if os.path.getsize(path) > MAX_FILE:
        tg("⚠️ File terlalu besar.")
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
    return open(p).read().strip() if os.path.exists(p) else ""

def save_state(k, v):
    open(state_path(k), "w").write(v)

def ext_from_response(resp):
    path = resp.url.split("?")[0]
    if os.path.splitext(path)[1]:
        return os.path.splitext(path)[1]

    ctype = resp.headers.get("Content-Type","").split(";")[0]
    if ctype in MIME_MAP:
        return MIME_MAP[ctype]

    return mimetypes.guess_extension(ctype) or ".bin"

def scan_url(url, force=False):
    r = requests.get(url, timeout=60)
    data = r.content
    h = sha(data)
    old = load_state(url)

    changed = force or h != old

    if changed:
        save_state(url, h)

        name = f"{DOWNLOAD_DIR}/{now().strftime('%Y%m%d_%H%M%S')}_{h[:8]}{ext_from_response(r)}"
        open(name,"wb").write(data)

        tg(
            f"🔔 PERUBAHAN\n\n{url}\n"
            f"HTTP {r.status_code}\n"
            f"SHA {h[:12]}"
        )
        tg_file(name)

    return changed

def scan_all(force=False):
    global last_scan
    changed = False
    for u in URLS:
        if scan_url(u, force):
            changed = True
    last_scan = now()
    return changed

def poll_commands():
    global last_update_id

    r = requests.get(
        f"{TG}/getUpdates",
        params={"offset": last_update_id + 1, "timeout": 1}
    ).json()

    for u in r.get("result", []):
        last_update_id = u["update_id"]
        text = u.get("message",{}).get("text","")

        if text == "/health":
            diff = int((now()-last_scan).total_seconds()/60)
            tg(f"🩺 OK\nLast scan {diff} menit")

        elif text == "/status":
            tg("🟢 BOT AKTIF")

        elif text == "/cekperubahan":
            tg("🔄 Scan manual")
            scan_all(True)
            tg("✅ Selesai")

def worker():
    tg("🟢 BOT ONLINE")

    while True:
        try:
            poll_commands()
            changed = scan_all()
            time.sleep(60 if changed else 600)
        except Exception as e:
            tg(str(e))
            time.sleep(60)

# START BACKGROUND LOOP
threading.Thread(target=worker, daemon=False).start()

# START WEB
app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
