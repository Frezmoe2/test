import requests
import hashlib
import os
from datetime import datetime

# ================== KONFIG ==================
URL = "https://pusatkode.com/081317155457"

BOT_TOKEN = ("8120207053:AAHq_RmqaWznQyG6E6b6U-DF89r8-IdAjcs") 
CHAT_ID = ("7530475008")

STATE_FILE = "last_state.txt"
SUMMARY_FILE = "summary_hour.txt"
DOWNLOAD_DIR = "downloads"
# ===========================================


def send_telegram(text):
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(api, data={"chat_id": CHAT_ID, "text": text}, timeout=15)


def send_file(path, caption):
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with open(path, "rb") as f:
        requests.post(
            api,
            data={"chat_id": CHAT_ID, "caption": caption},
            files={"document": f},
            timeout=120
        )


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path):
    return open(path).read() if os.path.exists(path) else None


def save(path, data):
    open(path, "w").write(data)


# ========== SUMMARY 1 JAM ==========
def hourly_summary(current_state, changes):
    hour = datetime.utcnow().strftime("%Y-%m-%d %H")
    last = load(SUMMARY_FILE)

    if last == hour:
        return  # sudah kirim summary jam ini

    save(SUMMARY_FILE, hour)

    send_telegram(
        "📊 SUMMARY 1 JAM\n\n"
        f"URL: {URL}\n"
        f"Periode (UTC): {hour}:00 – {hour}:59\n\n"
        f"Status HTTP: {current_state['status']}\n"
        f"Redirect: {current_state['location']}\n"
        f"Hash terakhir:\n{current_state['hash']}\n"
        f"Ukuran: {current_state['size']} bytes\n\n"
        f"Perubahan jam ini: {changes}\n"
        f"Status sistem: {'🟡 Ada aktivitas' if changes > 0 else '🟢 Stabil'}"
    )


# ========== EKSTENSI ==========
def guess_extension(headers, data: bytes) -> str:
    ct = headers.get("Content-Type", "").lower()
    head = data[:8192]

    if "html" in ct:
        return ".html"
    if "plain" in ct:
        return ".txt"
    if "json" in ct:
        return ".json"
    if "xml" in ct:
        return ".xml"
    if "csv" in ct:
        return ".csv"
    if "zip" in ct:
        return ".zip"
    if "pdf" in ct:
        return ".pdf"
    if "android.package-archive" in ct:
        return ".apk"

    if head.startswith(b"PK\x03\x04"):
        if b"AndroidManifest.xml" in head:
            return ".apk"
        return ".zip"
    if head.startswith(b"%PDF"):
        return ".pdf"
    if head.startswith(b"MZ"):
        return ".exe"

    try:
        text = data.decode("utf-8", errors="ignore")
        if sum(c.isprintable() for c in text[:2000]) / max(len(text[:2000]), 1) > 0.9:
            if "<html" in text.lower():
                return ".html"
            return ".txt"
    except Exception:
        pass

    return ".bin"


# ================== MAIN ==================
def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    s = requests.Session()
    r = s.get(URL, allow_redirects=False, timeout=20)

    status = r.status_code
    location = r.headers.get("Location", "-")
    content_type = r.headers.get("Content-Type", "-")

    file_hash = "-"
    file_size = "-"
    changes = 0

    last_state = load(STATE_FILE)

    if status in (301, 302, 303, 307, 308) and location:
        d = s.get(location, timeout=30)
        file_hash = sha256(d.content)
        file_size = str(len(d.content))

        if not last_state or f"FILE_HASH={file_hash}" not in last_state:
            changes += 1
            ext = guess_extension(d.headers, d.content)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            path = f"{DOWNLOAD_DIR}/{ts}_{file_hash[:8]}{ext}"

            with open(path, "wb") as f:
                f.write(d.content)

            size_mb = len(d.content) / (1024 * 1024)
            if size_mb <= 20:
                send_file(path, f"📦 File berubah ({size_mb:.2f} MB)")

    current_state = {
        "status": status,
        "location": location,
        "hash": file_hash,
        "size": file_size
    }

    state_text = (
        f"STATUS={status}\n"
        f"LOCATION={location}\n"
        f"FILE_HASH={file_hash}\n"
        f"FILE_SIZE={file_size}"
    )

    if last_state != state_text:
        save(STATE_FILE, state_text)
        send_telegram(
            "🔔 PERUBAHAN TERDETEKSI\n\n"
            f"URL: {URL}\n"
            f"Waktu UTC: {datetime.utcnow()}\n\n"
            f"SHA256:\n{file_hash}"
        )

    hourly_summary(current_state, changes)


if __name__ == "__main__":
    main()
