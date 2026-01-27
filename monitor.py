import requests
import hashlib
import os
import time
from datetime import datetime


# ====== DAFTAR URL (PAKAI ID BEBAS) ======
URLS = [
    "https://pusatkode.com/081317155457",
    "https://pusatkode.com/B6yadxhk.png"
    ]

# URL Workers kamu (hasil wrangler deploy)
WORKER = "https://telegram-bot.frezmoe.workers.dev"


BOT_TOKEN = "8120207053:AAHq_RmqaWznQyG6E6b6U-DF89r8-IdAjcs"
CHAT_ID = "7530475008"

STATE_DIR = "state"
DOWNLOAD_DIR = "downloads"

os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def tg(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )


def tg_file(path):
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


def ext_from_url(u):
    p = u.split("?")[0]
    if "." in p.split("/")[-1]:
        return "." + p.split("/")[-1].split(".")[-1][:5]
    return ".bin"


def in_fast_window():
    now = datetime.now()
    h = now.hour
    m = now.minute
    return h == 20 and 40 <= m <= 50


def check(url):
    r = requests.get(url, allow_redirects=True, timeout=60)
    data = r.content

    h = sha(data)
    old = load_state(url)

    status = r.status_code
    final = r.url
    ctype = r.headers.get("Content-Type", "-")
    size = len(data)

    changed = False

    if h != old:
        save_state(url, h)
        changed = True

        ext = ext_from_url(final)
        name = f"{DOWNLOAD_DIR}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{h[:8]}{ext}"
        open(name, "wb").write(data)

        msg = (
            "🔔 PERUBAHAN TERDETEKSI\n\n"
            f"URL: {url}\n"
            f"Waktu UTC: {datetime.utcnow().isoformat()}\n\n"
            f"HTTP Status: {status}\n"
            f"Redirect: {final}\n"
            f"Content-Type: {ctype}\n\n"
            f"SHA256:\n{h}\n"
            f"Ukuran: {size} bytes"
        )

        tg(msg)
        tg_file(name)

    return changed


tg("🟢 BOT ONLINE")

while True:
    any_change = False

    for u in URLS:
        try:
            if check(u):
                any_change = True
        except Exception as e:
            tg("❌ Error:\n" + str(e))

    # ================= INTERVAL LOGIC =================

    if any_change or in_fast_window():
        sleep = 60       # 1 menit
    else:
        sleep = 600      # 10 menit

    time.sleep(sleep)
