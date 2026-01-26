import requests
import hashlib

# ====== DAFTAR URL (PAKAI ID BEBAS) ======
URLS = {
    "kode1": "https://pusatkode.com/081317155457",
    # tambah kalau perlu:
    # "fileA": "https://example.com/a.zip",
    # "fileB": "https://example.com/b.apk",
}

# URL Workers kamu (hasil wrangler deploy)
WORKER_UPDATE_URL = "https://telegram-bot.yourname.workers.dev/update"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def send_to_worker(payload):
    requests.post(WORKER_UPDATE_URL, json=payload, timeout=15)


def main():
    all_states = {}

    for name, URL in URLS.items():
        s = requests.Session()
        r = s.get(URL, allow_redirects=False, timeout=20)

        status = r.status_code
        location = r.headers.get("Location", "-")

        file_hash = "-"
        file_size = "-"

        if status in (301, 302, 303, 307, 308) and location:
            d = s.get(location, timeout=30)
            file_hash = sha256(d.content)
            file_size = str(len(d.content))

        all_states[name] = {
            "url": URL,
            "http_status": status,
            "redirect": location,
            "hash": file_hash,
            "size": file_size
        }

    # kirim SEMUA status ke Workers
    send_to_worker(all_states)


if __name__ == "__main__":
    main()
