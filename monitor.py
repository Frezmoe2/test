import requests
import hashlib
import os
from datetime import datetime

URL = "https://pusatkode.com/081317155457"
STATE_FILE = "last_state.txt"
LOG_FILE = "changes.log"

def get_hash(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def load_last_hash():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return None

def save_hash(h):
    with open(STATE_FILE, "w") as f:
        f.write(h)

def log_change(message):
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")

def main():
    response = requests.get(URL, timeout=10)
    response.raise_for_status()

    current_hash = get_hash(response.text)
    last_hash = load_last_hash()

    if last_hash != current_hash:
        save_hash(current_hash)
        now = datetime.now().isoformat()
        log_change(f"[{now}] Perubahan terdeteksi!")

if __name__ == "__main__":
    main()
