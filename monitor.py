import requests
import hashlib
import os
from datetime import datetime

URL = "https://pusatkode.com/081317155457"

STATE_FILE = "last_state.txt"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def send_telegram(msg):
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(api, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_state():
    if os.path.exists(STATE_FILE):
        return open(STATE_FILE).read()
    return None


def save_state(state):
    open(STATE_FILE, "w").write(state)


def main():
    session = requests.Session()

    # === 1. REQUEST TANPA FOLLOW REDIRECT ===
    r = session.get(URL, allow_redirects=False, timeout=20)

    status = r.status_code
    location = r.headers.get("Location", "-")
    content_type = r.headers.get("Content-Type", "-")

    # === 2. JIKA REDIRECT / DOWNLOAD ===
    file_hash = "-"
    file_size = "-"

    if status in (301, 302, 303, 307, 308) and location:
        download = session.get(location, timeout=30)
        file_hash = sha256_bytes(download.content)
        file_size = str(len(download.content))

    # === 3. STATE DIGABUNG ===
    current_state = (
        f"STATUS={status}\n"
        f"LOCATION={location}\n"
        f"CONTENT_TYPE={content_type}\n"
        f"FILE_HASH={file_hash}\n"
        f"FILE_SIZE={file_size}"
    )

    last_state = load_state()

    if last_state != current_state:
        save_state(current_state)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            "🔔 PERUBAHAN TERDETEKSI\n\n"
            f"URL: {URL}\n"
            f"Waktu: {now}\n\n"
            f"HTTP Status: {status}\n"
            f"Redirect: {location}\n"
            f"Content-Type: {content_type}\n\n"
            f"File SHA256:\n{file_hash}\n"
            f"File Size: {file_size} bytes"
        )

        send_telegram(message)


if __name__ == "__main__":
    main()
