import requests
import hashlib
import os
from datetime import datetime, date

URL = "https://pusatkode.com/081317155457"

STATE_FILE = "last_state.txt"
HEARTBEAT_FILE = "last_heartbeat.txt"

BOT_TOKEN = ("8120207053:AAHq_RmqaWznQyG6E6b6U-DF89r8-IdAjcs")
CHAT_ID = ("7530475008")


def send_telegram(msg):
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(api, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_file(path):
    if os.path.exists(path):
        return open(path).read()
    return None


def save_file(path, data):
    open(path, "w").write(data)


def heartbeat():
    today = date.today().isoformat()
    last = load_file(HEARTBEAT_FILE)

    if last != today:
        send_telegram(f"ℹ️ Monitor aktif\n{URL}\nTanggal: {today}")
        save_file(HEARTBEAT_FILE, today)


def main():
    # === HEARTBEAT (1x per hari) ===
    heartbeat()

    session = requests.Session()

    # === HTTP CHECK (NO REDIRECT) ===
    r = session.get(URL, allow_redirects=False, timeout=20)

    status = r.status_code
    location = r.headers.get("Location", "-")
    content_type = r.headers.get("Content-Type", "-")

    file_hash = "-"
    file_size = "-"

    if status in (301, 302, 303, 307, 308) and location:
        download = session.get(location, timeout=30)
        file_hash = sha256_bytes(download.content)
        file_size = str(len(download.content))

    current_state = (
        f"STATUS={status}\n"
        f"LOCATION={location}\n"
        f"CONTENT_TYPE={content_type}\n"
        f"FILE_HASH={file_hash}\n"
        f"FILE_SIZE={file_size}"
    )

    last_state = load_file(STATE_FILE)

    if last_state != current_state:
        save_file(STATE_FILE, current_state)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        send_telegram(
            "🔔 PERUBAHAN TERDETEKSI\n\n"
            f"URL: {URL}\n"
            f"Waktu: {now}\n\n"
            f"HTTP Status: {status}\n"
            f"Redirect: {location}\n"
            f"Content-Type: {content_type}\n\n"
            f"File SHA256:\n{file_hash}\n"
            f"File Size: {file_size} bytes"
        )


if __name__ == "__main__":
    main()
