import asyncio
import requests
import re
import phonenumbers
from phonenumbers import geocoder
from telegram import Bot
import json
import os
from datetime import datetime

# ============================
# SETTINGS
# ============================
BOT_TOKEN = "8437087674:AAEEBJDfEkxl0MbA__lsSF4A7qc7UpwzGU4"
bot = Bot(token=BOT_TOKEN)

GROUP_IDS = [-1003361941052]
OTP_FILE = "otp_store.json"

API_CONFIGS = {
    "cr1": {
        "url": "http://51.77.216.195/crapi/dgroup/viewstats",
        "params": {
            "token": "RFRSNEVBdnh3V1NpVHCYQXNfl2hZiGx_R22GZop3d3pBZJJfXGU=",
            "records": 20
        }
    },
    "cr2": {
        "url": "http://147.135.212.197/crapi/st/viewstats",
        "params": {
            "token": "RVdWRElBUzRGcW9WeneNcmd2cGV9ZJd8e29PVlyPcFxeamxSgWVXfw==",
            "dt1": datetime.now().strftime("%Y-%m-%d"),
            "records": 20
        }
    }
}

# ============================
# HELPERS
# ============================
def load_otp_store():
    if not os.path.exists(OTP_FILE):
        return {}
    with open(OTP_FILE, "r") as f:
        return json.load(f)

def save_otp_store(data):
    with open(OTP_FILE, "w") as f:
        json.dump(data, f, indent=2)

def extract_otp(message):
    match = re.search(r"\b\d{4,6}\b", str(message))
    return match.group(0) if match else "N/A"

def get_country_info(number_str):
    try:
        num = f"+{number_str}" if not str(number_str).startswith("+") else number_str
        parsed = phonenumbers.parse(num)
        region = phonenumbers.region_code_for_number(parsed)
        country = geocoder.description_for_number(parsed, "en")
        flag = "".join(chr(127397 + ord(c)) for c in region) if region else "🌍"
        return country or "Unknown", flag
    except:
        return "Unknown", "🌍"

# ============================
# FETCH DATA (CR1 + CR2 FIXED)
# ============================
def fetch_data(panel_key):
    cfg = API_CONFIGS[panel_key]
    try:
        r = requests.get(cfg["url"], params=cfg["params"], timeout=15)
        if r.status_code != 200:
            return None

        data = r.json()
        latest = None

        # CASE 1: [[{...}]]  (CR2)
        if isinstance(data, list) and data:
            if isinstance(data[0], list) and data[0]:
                latest = data[0][0]
            elif isinstance(data[0], dict):
                latest = data[0]

        # CASE 2: {"status":"success","data":[{...}]}
        elif isinstance(data, dict) and data.get("data"):
            latest = data["data"][0]

        if not isinstance(latest, dict):
            return None

        return {
            "time": latest.get("dt", "N/A"),
            "number": latest.get("num", "N/A"),
            "service": latest.get("cli", "N/A"),
            "message": latest.get("message", "N/A")
        }

    except Exception as e:
        print(f"Error on {panel_key}: {e}")
        return None

# ============================
# WORKER
# ============================
async def panel_worker(panel_key):
    print(f"🚀 Worker {panel_key} started...")
    last_id = None

    while True:
        data = fetch_data(panel_key)

        if data and data["message"] != "N/A":
            current_id = f"{data['number']}_{data['message']}"

            if current_id != last_id:
                last_id = current_id

                otp = extract_otp(data["message"])
                store = load_otp_store()
                store[str(data["number"])] = otp
                save_otp_store(store)

                country, flag = get_country_info(data["number"])
                border = "═" * 30

                msg = (
                    f"🟢 <b>✨🛡 PRIME OTP ALERT 🛡✨</b>\n"
                    f"<code>{border}</code>\n"
                    f"<b>Panel:</b> {panel_key.upper()}\n"
                    f"<b>Service:</b> {data['service']}\n"
                    f"<b>Number:</b> <code>{data['number']}</code>\n"
                    f"<b>Country:</b> {flag} {country}\n"
                    f"<b>Time:</b> {data['time']}\n"
                    f"<b>OTP:</b> <code>{otp}</code>\n\n"
                    f"<b>Message:</b>\n<pre>{data['message']}</pre>\n"
                    f"<code>{border}</code>\n"
                    f"Powered by Junaid Niz 💗"
                )

                for gid in GROUP_IDS:
                    try:
                        await bot.send_message(
                            chat_id=gid,
                            text=msg,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print("Telegram Error:", e)

        await asyncio.sleep(5)

# ============================
# MAIN
# ============================
async def main():
    await asyncio.gather(
        panel_worker("cr1"),
        panel_worker("cr2")
    )

if __name__ == "__main__":
    asyncio.run(main())
