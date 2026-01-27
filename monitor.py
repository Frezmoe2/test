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

# ================= CONFIG =================

URLS = [
    "https://pusatkode.com/081317155457",
    "https://pusatkode.com/B6yadxhk.png"
]

STATE_DIR = "state"
DOWNLOAD_DIR = "downloads"
MAX_FILE = 45 * 1024 * 1024

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

os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

last_scan = datetime.now(timezone.utc)
last_update_id = 0

# ================= HELPERS =================

def now():
    return datetime.now(timezone.utc)

def tg(msg):
    requests.post(f"{TG}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})

def tg_file(path):
    if os.path.getsize(path) > MAX_FILE:
        tg("⚠️ File terlalu besar")
        return
    with open(path, "rb") as f:
        requests.post(f"{TG}/sendDocument",
            data={"chat_id": CHAT_ID},
            files={"document": f}
        )

def sha(data):
    return hashlib.sha256(data).hexdigest()

def state_path(k):
    return f"{STATE_DIR}/{hashlib.md5(k.encode()).hexdigest()}.txt"

def load_state(k):
    if os.path.exists(state_path(k)):
        return open(state_path(k)).read()
    return ""

def save_state(k,v):
    open(state_path(k),"w").write(v)

def ext_from_response(r):
    p = r.url.split("?")[0]
    e = os.path.splitext(p)[1]
    if e: return e
    ct = r.headers.get("Content-Type","").split(";")[0]
    if ct in MIME_MAP: return MIME_MAP[ct]
    g = mimetypes.guess_extension(ct)
    return g if g else ".bin"

# ================= CORE =================

def scan_url(url, force=False):
    r = requests.get(url,timeout=60,allow_redirects=True)
    data = r.content
    h = sha(data)
    old = load_state(url)

    if force or h!=old:
        save_state(url,h)
        ext = ext_from_response(r)
        name=f"{DOWNLOAD_DIR}/{now().strftime('%Y%m%d_%H%M%S')}_{h[:8]}{ext}"
        open(name,"wb").write(data)

        tg(
            f"🔔 UPDATE\n{url}\nHTTP:{r.status_code}\nSHA:{h}\nSize:{len(data)}"
        )
        tg_file(name)
        return True
    return False

def scan_all(force=False):
    global last_scan
    changed=False
    for u in URLS:
        if scan_url(u,force):
            changed=True
    last_scan=now()
    return changed

def poll_commands():
    global last_update_id
    r=requests.get(f"{TG}/getUpdates",
        params={"offset":last_update_id+1,"timeout":1}).json()

    for u in r.get("result",[]):
        last_update_id=u["update_id"]
        t=u["message"]["text"]

        if t=="/health":
            m=int((now()-last_scan).total_seconds()/60)
            tg(f"🩺 Last scan {m} menit")

        elif t=="/cekperubahan":
            tg("Manual scan...")
            scan_all(True)

        elif t=="/status":
            tg("Bot aktif")

def bot_loop():
    tg("🟢 BOT ONLINE")
    while True:
        try:
            poll_commands()
            c=scan_all()
            time.sleep(60 if c else 600)
        except Exception as e:
            tg(str(e))
            time.sleep(60)

# ================= START =================

Thread(target=bot_loop,daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
