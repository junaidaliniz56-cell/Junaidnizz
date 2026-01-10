import asyncio
import json
import re
import requests
from telegram import Bot

# =========================
# CONFIG
# =========================

BOT_TOKEN = "8433897615:AAHE2px-1g5KvJTyMuGfdJoi_XfHx03Lcmw"

CR_API = "http://147.135.212.197/crapi/st/viewstats"
CR_TOKEN = "RVdWRElBUzRGcW9WeneNcmd2cGV9ZJd8e29PVlyPcFxeamxSgWVXfw=="

GROUP_IDS = [
    -1003361941052,   # apna group ID
]

OTP_FILE = "otp_store.json"

bot = Bot(token=BOT_TOKEN)

# =========================
# UTILS
# =========================

def load_otp_store():
    try:
        with open(OTP_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_otp_store(data):
    with open(OTP_FILE, "w") as f:
        json.dump(data, f)

def extract_otp(text):
    match = re.search(r"\b(\d{4,8})\b", text)
    return match.group(1) if match else None

def fetch_cr_data():
    try:
        r = requests.get(
            CR_API,
            params={"token": CR_TOKEN},
            timeout=10
        )
        if r.status_code == 200:
            return r.json()
    except:
        return None

async def send_to_groups(msg):
    for gid in GROUP_IDS:
        try:
            await bot.send_message(gid, msg)
        except Exception as e:
            print("Send error:", e)

# =========================
# CR WORKER
# =========================

async def cr_worker():
    print("🚀 CR Worker Started")
    last_unique = None

    while True:
        data = fetch_cr_data()

        if isinstance(data, dict):
            number = str(data.get("num") or data.get("number") or "")
            message = str(data.get("msg") or data.get("message") or "")
            service = str(data.get("service") or "CR")

            if number and message:
                unique = number + message

                if unique != last_unique:
                    last_unique = unique

                    otp = extract_otp(message)
                    if otp:
                        store = load_otp_store()
                        store[number] = otp
                        save_otp_store(store)

                    text = (
                        f"📡 <b>{service}</b>\n"
                        f"📞 <code>{number}</code>\n"
                        f"💬 {message}"
                    )

                    await send_to_groups(text)
                    print("Sent:", number)

        await asyncio.sleep(3)

# =========================
# COMMAND LISTENER
# =========================

async def command_listener():
    print("⌨️ Command Listener Started")
    offset = 0

    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=20)

            for update in updates:
                offset = update.update_id + 1

                if update.message and update.message.text:
                    chat_id = update.message.chat.id
                    text = update.message.text.strip()

                    if text.startswith("/otpfor"):
                        parts = text.split()

                        if len(parts) < 2:
                            await bot.send_message(chat_id, "Usage: /otpfor <number>")
                            continue

                        number = parts[1]
                        store = load_otp_store()

                        if number in store:
                            await bot.send_message(
                                chat_id,
                                f"🔐 OTP for {number}: <code>{store[number]}</code>",
                                parse_mode="HTML"
                            )
                        else:
                            await bot.send_message(
                                chat_id,
                                "❌ No OTP found for this number"
                            )

        except Exception as e:
            print("COMMAND ERROR:", e)

        await asyncio.sleep(1)

# =========================
# MAIN
# =========================

async def main():
    await asyncio.gather(
        cr_worker(),
        command_listener()
    )

if __name__ == "__main__":
    asyncio.run(main())
