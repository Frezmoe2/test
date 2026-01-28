import requests
import hashlib
import os
from datetime import datetime, timezone
from flask import Flask, request
import json

BOT_TOKEN = "8120207053:AAHq_RmqaWznQyG6E6b6U-DF89r8-IdAjcs"
CHAT_ID = "7530475008"

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

URLS = [
    "https://pusatkode.com/081317155457",
    "https://pusatkode.com/B6yadxhk.png"
]

DATA_DIR = "data"
DOWNLOAD = "downloads"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOWNLOAD, exist_ok=True)

STATE_FILE = f"{DATA_DIR}/state.json"
HISTORY_FILE = f"{DATA_DIR}/history.json"

# ================= STORAGE =================

def load_json(p):
    if os.path.exists(p):
        return json.load(open(p))
    return {}

def save_json(p, d):
    json.dump(d, open(p,"w"), indent=2)

STATE = load_json(STATE_FILE)
HISTORY = load_json(HISTORY_FILE)

# ================= UTILS =================

def now():
    return datetime.now(timezone.utc).isoformat()

def sha256(x):
    return hashlib.sha256(x).hexdigest()

def tg(msg):
    requests.post(f"{TG}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg
    })

def tg_file(path):
    with open(path,"rb") as f:
        requests.post(
            f"{TG}/sendDocument",
            data={"chat_id":CHAT_ID},
            files={"document":f}
        )

def ext(resp):
    p = resp.url.split("?")[0]
    e = os.path.splitext(p)[1]
    if e:
        return e

    ct = resp.headers.get("Content-Type","").split(";")[0]

    MAP = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "text/html": ".html",
        "application/pdf": ".pdf",
        "video/mp4": ".mp4",
        "video/quicktime": ".mov"
    }

    return MAP.get(ct, ".bin")

# ================= CORE =================

def scan(force=False):
    global STATE,HISTORY

    for url in URLS:
        r = requests.get(url, allow_redirects=True, timeout=60)
        data = r.content

        sha = sha256(data)
        size = len(data)
        final = r.url

        prev = STATE.get(url,{})

        changed = (
            force or
            prev.get("sha") != sha or
            prev.get("size") != size
        )

        if not changed:
            continue

        # save file
        name = f"{DOWNLOAD}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{sha[:8]}{ext(r)}"
        open(name,"wb").write(data)

        # update state
        STATE[url]={
            "sha":sha,
            "size":size,
            "final":final,
            "last_change":now()
        }

        # history
        HISTORY.setdefault(url,[]).append({
            "time":now(),
            "sha":sha,
            "size":size,
            "final":final
        })

        save_json(STATE_FILE,STATE)
        save_json(HISTORY_FILE,HISTORY)

        tg(
            "🔔 PERUBAHAN TERDETEKSI\n\n"
            f"URL: {url}\n"
            f"Final: {final}\n"
            f"SHA256:\n{sha}\n"
            f"Size: {size} bytes"
        )

        tg_file(name)

# ================= TELEGRAM =================

@app.route("/webhook",methods=["POST"])
def hook():
    text=request.json.get("message",{}).get("text","")

    if text=="/health":
        tg("🟢 BOT AKTIF")

    elif text=="/status":
        msg="📊 STATUS\n\n"
        for u,v in STATE.items():
            msg+=f"{u}\nSHA:{v['sha'][:12]}...\nSize:{v['size']}\n\n"
        tg(msg or "Belum ada data")

    elif text=="/history":
        msg="📜 HISTORY\n\n"
        for u,h in HISTORY.items():
            msg+=f"{u}\nTotal perubahan: {len(h)}\n\n"
        tg(msg)

    elif text=="/cekperubahan":
        tg("🔄 Scan manual...")
        scan(True)
        tg("✅ Selesai")

    return "ok"

# ================= HTTP =================

@app.route("/")
def home():
    return "OK"

@app.route("/autoscan")
def autoscan():
    scan(False)
    return "autoscan ok"

# ================= START =================

if __name__=="__main__":
    scan(True)
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
