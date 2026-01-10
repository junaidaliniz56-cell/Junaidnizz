import asyncio
import requests
import re
import json
import os
from datetime import datetime, timedelta
from telegram import Bot, Update
from telegram.error import Conflict

# ======================
# TELEGRAM SETTINGS
# ======================
BOT_TOKEN = "8437087674:AAEEBJDfEkxl0MbA__lsSF4A7qc7UpwzGU4"
bot = Bot(token=BOT_TOKEN)

GROUP_IDS = [-1003361941052]   # apna group id
OTP_FILE = "otp_store.json"

# ======================
# PAKISTAN DATE (UTC+5)
# ======================
PK_DATE = (datetime.utcnow() + timedelta(hours=5)).strftime("%Y-%m-%d")

# ======================
# CR API CONFIG
# ======================
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

def extract_otp(text):
    m = re.search(r"\b\d{4,6}\b", str(text))
    return m.group(0) if m else None

# ======================
# FETCH CR DATA (SAFE)
# ======================
def fetch_cr_latest():
    try:
        r = requests.get(CR_API["url"], params=CR_API["params"], timeout=15)
        if r.status_code != 200:
            return None

        data = r.json()

        # Expected format: [[{...}]]
        if (
            isinstance(data, list)
            and data
            and isinstance(data[0], list)
            and data[0]
            and isinstance(data[0][0], dict)
        ):
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

        if isinstance(data, dict):
            num = str(data.get("num", ""))
            msg = str(data.get("message", ""))
            dt = str(data.get("dt", "N/A"))

            unique = num + msg
            if unique != last_unique:
                last_unique = unique

                otp = extract_otp(msg)
                if otp:
                    store = load_otp_store()
                    store[num] = otp
                    save_otp_store(store)

                text = (
                    f"🟢 <b>CR OTP ALERT</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"<b>Number:</b> <code>{num}</code>\n"
                    f"<b>Time:</b> {dt}\n"
                    f"<b>OTP:</b> <code>{otp or 'N/A'}</code>\n\n"
                    f"<pre>{msg}</pre>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🇵🇰 Date: {PK_DATE}"
                )

                for gid in GROUP_IDS:
                    try:
                        await bot.send_message(gid, text, parse_mode="HTML")
                    except Exception as e:
                        print("TG SEND ERROR:", e)

        await asyncio.sleep(5)

# ======================
# COMMAND LISTENER (/otpfor)
# ======================
async def command_listener():
    print("⌨️ Command Listener Started")
    offset = 0

    while True:
        try:
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
                        await bot.send_message(
                            chat_id,
                            "⚠️ Usage: /otpfor <number>"
                        )
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

        except Conflict:
            print("⚠️ Telegram Conflict: another instance running")
            await asyncio.sleep(10)

        except Exception as e:
            print("COMMAND ERROR:", e)
            await asyncio.sleep(5)

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
