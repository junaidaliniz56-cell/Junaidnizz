import asyncio
import requests
import re
import json
import os
from datetime import datetime, timedelta
from telegram import Bot

# ======================
# TELEGRAM SETTINGS
# ======================
BOT_TOKEN = "8437087674:AAEEBJDfEkxl0MbA__lsSF4A7qc7UpwzGU4"
bot = Bot(BOT_TOKEN)

GROUP_IDS = [-1003361941052]
OTP_FILE = "otp_store.json"

# ======================
# CR PANEL CONFIG
# ======================
PK_DATE = (datetime.utcnow() + timedelta(hours=5)).strftime("%Y-%m-%d")

CR_API = {
    "url": "http://147.135.212.197/crapi/st/viewstats",
    "params": {
        "token": "RVdWRElBUzRGcW9WeneNcmd2cGV9ZJd8e29PVlyPcFxeamxSgWVXfw==",
        "dt1": PK_DATE,
        "records": 20
    }
}

# ======================
# HELPERS
# ======================
def load_otp_store():
    if not os.path.exists(OTP_FILE):
        return {}
    with open(OTP_FILE, "r") as f:
        return json.load(f)

def save_otp_store(data):
    with open(OTP_FILE, "w") as f:
        json.dump(data, f, indent=2)

def extract_otp(msg):
    m = re.search(r"\b\d{4,6}\b", str(msg))
    return m.group(0) if m else None

# ======================
# FETCH FROM CR (FIXED)
# ======================
def fetch_cr_latest():
    try:
        r = requests.get(CR_API["url"], params=CR_API["params"], timeout=15)
        if r.status_code != 200:
            return None

        data = r.json()

        # CR response is [[{...}]]
        if isinstance(data, list) and data and isinstance(data[0], list) and data[0]:
            return data[0][0]

        return None

    except Exception as e:
        print("CR FETCH ERROR:", e)
        return None

# ======================
# CR WORKER
# ======================
async def cr_worker():
    print("🚀 CR Worker Started")
    last_unique = None

    while True:
        data = fetch_cr_latest()

        if data:
            unique = str(data.get("num")) + str(data.get("message"))

            if unique != last_unique:
                last_unique = unique

                number = str(data.get("num"))
                message = data.get("message", "")
                otp = extract_otp(message)

                if otp:
                    store = load_otp_store()
                    store[number] = otp
                    save_otp_store(store)

                text = (
                    f"🟢 <b>CR OTP ALERT</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"<b>Number:</b> <code>{number}</code>\n"
                    f"<b>Time:</b> {data.get('dt','N/A')}\n"
                    f"<b>OTP:</b> <code>{otp or 'N/A'}</code>\n\n"
                    f"<pre>{message}</pre>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🇵🇰 Pakistan Date: {PK_DATE}"
                )

                for gid in GROUP_IDS:
                    try:
                        await bot.send_message(gid, text, parse_mode="HTML")
                    except Exception as e:
                        print("TG ERROR:", e)

        await asyncio.sleep(5)

# ======================
# /otpfor COMMAND
# ======================
async def command_listener():
    offset = 0
    print("⌨️ Command Listener Started")

    while True:
        updates = await bot.get_updates(offset=offset, timeout=10)

        for u in updates:
            offset = u.update_id + 1

            if not u.message or not u.message.text:
                continue

            text = u.message.text.strip()
            chat_id = u.message.chat_id

            if text.startswith("/otpfor"):
                parts = text.split()
                if len(parts) < 2:
                    await bot.send_message(chat_id, "⚠️ Usage: /otpfor <number>")
                    continue

                number = parts[1].replace("+", "")
                store = load_otp_store()

                if number in store:
                    await bot.send_message(
                        chat_id,
                        f"🔐 <b>Saved OTP:</b> <code>{store[number]}</code>",
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        chat_id,
                        "❌ No OTP found for this number",
                        parse_mode="HTML"
                    )

        await asyncio.sleep(1)

# ======================
# MAIN
# ======================
async def main():
    await asyncio.gather(
        cr_worker(),
        command_listener()
    )

if __name__ == "__main__":
    asyncio.run(main())
