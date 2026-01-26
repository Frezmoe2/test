import requests, hashlib, os

# ====== DAFTAR URL (PAKAI ID BEBAS) ======
URLS = {
    "kode1": "https://pusatkode.com/081317155457",
    "kode2": "https://pusatkode.com/B6yadxhk.png",
    # tambah kalau perlu:
    # "fileA": "https://example.com/a.zip",
    # "fileB": "https://example.com/b.apk",
}

# URL Workers kamu (hasil wrangler deploy)
WORKER = "https://telegram-bot.frezmoe.workers.dev"


BOT_TOKEN = "8120207053:AAHq_RmqaWznQyG6E6b6U-DF89r8-IdAjcs"
CHAT_ID = "7530475008"

DOWNLOAD="downloads"
os.makedirs(DOWNLOAD,exist_ok=True)

def sha(x): return hashlib.sha256(x).hexdigest()

def send_file(path):
    with open(path,"rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
            data={"chat_id":CHAT_ID},
            files={"document":f}
        )

def main():
    data={}
    for k,u in URLS.items():
        r=requests.get(u,allow_redirects=False)
        loc=r.headers.get("Location","-")
        h="-";s="-"

        if loc!="-":
            d=requests.get(loc)
            h=sha(d.content);s=len(d.content)

            fn=f"{DOWNLOAD}/{k}_{h[:8]}.bin"
            open(fn,"wb").write(d.content)

            if s<20*1024*1024:
                send_file(fn)

        data[k]={
            "url":u,
            "http_status":r.status_code,
            "redirect":loc,
            "hash":h,
            "size":s
        }

    requests.post(WORKER,json=data)

main()
