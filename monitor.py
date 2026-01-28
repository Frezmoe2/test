import requests
import hashlib
import os
from datetime import datetime, timezone
import mimetypes
from flask import Flask, request

BOT_TOKEN = "8120207053:AAHq_RmqaWznQyG6E6b6U-DF89r8-IdAjcs"
CHAT_ID = "7530475008"

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

MIME_MAP = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "text/html": ".html",
}

URLS = [
    "https://pusatkode.com/081317155457",
    "https://pusatkode.com/B6yadxhk.png"
]

STATE_DIR="state"
DOWNLOAD="downloads"
os.makedirs(DOWNLOAD,exist_ok=True)
os.makedirs(STATE_DIR,exist_ok=True)

def now():
    return datetime.now(timezone.utc)

def sha(x):
    return hashlib.sha256(x).hexdigest()

def key(u):
    return hashlib.md5(u.encode()).hexdigest()

def state_path(u):
    return f"{STATE_DIR}/{key(u)}"

def load(u):
    return open(state_path(u)).read() if os.path.exists(state_path(u)) else ""

def save(u,v):
    open(state_path(u),"w").write(v)

def tg(msg):
    requests.post(f"{TG}/sendMessage",json={
        "chat_id":CHAT_ID,
        "text":msg
    })

def tg_file(path):
    with open(path,"rb") as f:
        requests.post(
            f"{TG}/sendDocument",
            data={"chat_id":CHAT_ID},
            files={"document":f}
        )

def ext(r):
    p=r.url.split("?")[0]
    if os.path.splitext(p)[1]:
        return os.path.splitext(p)[1]
    ct=r.headers.get("Content-Type","").split(";")[0]
    return MIME_MAP.get(ct,mimetypes.guess_extension(ct) or ".bin")

def scan(force=False):
    for u in URLS:
        r=requests.get(u,allow_redirects=True,timeout=60)

        combo = (r.url + r.content.hex()).encode()
        h=sha(combo)

        old=load(u)

        if force or h!=old:
            save(u,h)

            name=f"{DOWNLOAD}/{now().strftime('%Y%m%d_%H%M%S')}_{h[:8]}{ext(r)}"
            open(name,"wb").write(r.content)

            tg(
                f"🔔 PERUBAHAN\n\n"
                f"{u}\n"
                f"Final: {r.url}\n"
                f"HTTP: {r.status_code}\n"
                f"SHA: {h[:12]}"
            )
            tg_file(name)

@app.route("/")
def home():
    return "OK"

@app.route("/webhook",methods=["POST"])
def hook():
    text=request.json.get("message",{}).get("text","")

    if text=="/health":
        tg("🩺 BOT HIDUP")

    elif text=="/status":
        tg("🟢 AKTIF")

    elif text=="/cekperubahan":
        tg("🔄 Scan...")
        scan(True)
        tg("✅ Selesai")

    return "ok"

@app.route("/autoscan")
def autoscan():
    scan(False)
    return "autoscan ok"

if __name__=="__main__":
    scan(True)
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
