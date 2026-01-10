import asyncio
import requests
import re
import phonenumbers
from phonenumbers import geocoder
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import json
import os
from datetime import datetime

# ============================
# CONFIGURATION
# ============================
BOT_TOKEN = "8437087674:AAEEBJDfEkxl0MbA__lsSF4A7qc7UpwzGU4"
bot = Bot(token=BOT_TOKEN)
GROUP_IDS = [-1003361941052]
OTP_FILE = "otp_store.json"

# API CONFIG: Is tarah likhne se syntax error nahi aayega
API_CONFIGS = {
    "cr1": {
        "url": "http://51.77.216.195/crapi/dgroup/viewstats",
        "params": {
            "token": "RFRSNEVBdnh3V1NpVHCYQXNfl2hZiGx_R22GZop3d3pBZJJfXGU=",
            "records": 20
        }
    },
    "cr2": {
        # Yahan humne base URL alag rakha hai aur params alag
        "url": "http://147.135.212.197/crapi/st/viewstats",
        "params": {
            "token": "RVdWRElBUzRGcW9WeneNcmd2cGV9ZJd8e29PVlyPcFxeamxSgWVXfw==",
            "dt1": datetime.now().strftime("%Y-%m-%d"), # Aaj ki date auto lega
            "records": 20
        }
    }
}

# ============================
# HELPERS
# ============================
def load_otp_store():
    if not os.path.exists(OTP_FILE): return {}
    with open(OTP_FILE, "r") as f: return json.load(f)

def save_otp_store(data):
    with open(OTP_FILE, "w") as f: json.dump(data, f, indent=2)

def extract_otp(message):
    match = re.search(r'\d{4,6}', str(message))
    return match.group(0) if match else "N/A"

def get_country_info(number_str):
    try:
        num = f"+{number_str}" if not str(number_str).startswith("+") else number_str
        parsed = phonenumbers.parse(num)
        region = phonenumbers.region_code_for_number(parsed)
        country = geocoder.description_for_number(parsed, "en")
        flag = "".join(chr(127397 + ord(c)) for c in region) if region else "🌍"
        return country or "Unknown", flag
    except: return "Unknown", "🌍"

# ============================
# FETCH LOGIC (Fixed for List Error)
# ============================
def fetch_data(panel_key):
    cfg = API_CONFIGS[panel_key]
    try:
        # requests.get khud hi URL ke peeche ?token=...&dt1=... laga dega
        response = requests.get(cfg["url"], params=cfg["params"], timeout=15)
        if response.status_code != 200: return None
        data = response.json()
        
        # FIX: Check if list or dict
        if isinstance(data, list) and len(data) > 0:
            latest = data[0]
        elif isinstance(data, dict) and data.get("status") == "success" and data.get("data"):
            latest = data["data"][0]
        else:
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
# WORKER LOOP
# ============================
async def panel_worker(panel_key):
    print(f"🚀 Worker {panel_key} started...")
    last_id = None
    while True:
        data = fetch_data(panel_key)
        if data:
            current_id = f"{data['number']}_{data['message']}"
            if current_id != last_id:
                last_id = current_id
                
                otp = extract_otp(data["message"])
                store = load_otp_store()
                store[str(data['number'])] = otp
                save_otp_store(store)
                
                country, flag = get_country_info(data["number"])
                border = "═" * 30
                msg = (
                    f"🟢 <b>✨🛡 PRIME OTP ALERT 🛡✨</b> 🟢\n"
                    f"<code>{border}</code>\n"
                    f"<b>Panel:</b> {panel_key.upper()}\n"
                    f"<b>Service:</b> {data['service']} 📊\n"
                    f"<b>Number:</b> <code>{data['number']}</code>\n"
                    f"<b>Country:</b> {flag} {country}\n"
                    f"<b>Time:</b> 🕒 {data['time']}\n"
                    f"<b>OTP:</b> <code>{otp}</code> 💠\n\n"
                    f"<b>Message:</b>\n<pre>{data['message']}</pre>\n"
                    f"<code>{border}</code>\n"
                    f"Powered by Junaid Niz 💗"
                )
                
                for gid in GROUP_IDS:
                    try:
                        await bot.send_message(chat_id=gid, text=msg, parse_mode="HTML")
                    except: pass
        
        await asyncio.sleep(5)

async def main():
    await asyncio.gather(
        panel_worker("cr1"),
        panel_worker("cr2")
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
