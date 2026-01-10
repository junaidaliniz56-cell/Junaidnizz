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
# SETTINGS
# ============================
BOT_TOKEN = "8437087674:AAEEBJDfEkxl0MbA__lsSF4A7qc7UpwzGU4"
bot = Bot(token=BOT_TOKEN)
GROUP_IDS = [-1003361941052]
OTP_FILE = "otp_store.json"

# API PANELS - Names changed to be unique (cr1, cr2)
API_PANELS = {
    "cr1": {
        "url": "http://51.77.216.195/crapi/dgroup/viewstats",
        "token": "RFRSNEVBdnh3V1NpVHCYQXNfl2hZiGx_R22GZop3d3pBZJJfXGU=",
        "records": 20
    },
    "cr2": {
        "url": "http://147.135.212.197/crapi/st/viewstats",
        "token": "RVdWRElBUzRGcW9WeneNcmd2cGV9ZJd8e29PVlyPcFxeamxSgWVXfw==",
        "records": 20
    }
}

# ============================
# HELPERS & FILTERS
# ============================
ALLOWED_CLIS = []
BLOCKED_CLIS = []
CLI_FILTER_MODE = "off"

def cli_passes_filter(cli):
    if not cli: return True
    cli_lower = str(cli).lower()
    if CLI_FILTER_MODE == "allow":
        return any(a.lower() in cli_lower for a in ALLOWED_CLIS)
    elif CLI_FILTER_MODE == "block":
        return not any(b.lower() in cli_lower for b in BLOCKED_CLIS)
    return True

def load_otp_store():
    if not os.path.exists(OTP_FILE): return {}
    with open(OTP_FILE, "r") as f: return json.load(f)

def save_otp_store(data):
    with open(OTP_FILE, "w") as f: json.dump(data, f, indent=2)

def extract_otp(message):
    for pat in [r'\d{6}', r'\d{4}', r'\d{3}-\d{3}']:
        match = re.search(pat, str(message))
        if match: return match.group(0)
    return "N/A"

def get_country_info(number_str):
    try:
        num = f"+{number_str}" if not str(number_str).startswith("+") else number_str
        parsed = phonenumbers.parse(num)
        country = geocoder.description_for_number(parsed, "en")
        region = phonenumbers.region_code_for_number(parsed)
        flag = "".join(chr(127397 + ord(c)) for c in region) if region else "🌍"
        return country or "Unknown", flag
    except: return "Unknown", "🌍"

# ============================
# FETCH FUNCTION (Updated with Date)
# ============================
def fetch_latest(panel_key):
    cfg = API_PANELS[panel_key]
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    params = {
        "token": cfg["token"],
        "records": cfg["records"],
        "dt1": today_date  # Adding date parameter for accuracy
    }
    
    try:
        response = requests.get(cfg["url"], params=params, timeout=15)
        data = response.json()
        
        if data.get("status") == "success" and data.get("data"):
            latest = data["data"][0]
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
# MESSAGE FORMATTING
# ============================
def format_message(record):
    otp = extract_otp(record["message"])
    clean_msg = str(record["message"]).replace("<", "&lt;").replace(">", "&gt;")
    country, flag = get_country_info(record["number"])
    border = "═" * 30
    
    return (
        f"🟢 <b>✨🛡 PRIME OTP ALERT 🛡✨</b> 🟢\n"
        f"<code>{border}</code>\n"
        f"<b>Service:</b> {record['service']} 📊\n"
        f"<b>Number:</b> <code>{record['number']}</code> 🔢\n"
        f"<b>Country:</b> {flag} {country}\n"
        f"<b>Time:</b> 🕒 {record['time']}\n"
        f"<b>OTP:</b> <code>{otp}</code> 💠\n\n"
        f"<b>Full Message:</b>\n<pre>{clean_msg}</pre>\n"
        f"<code>{border}</code>\n"
        f"Powered by Junaid Niz 💗"
    )

async def send_to_groups(msg):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Channel", url="https://t.me/jndtech1"),
         InlineKeyboardButton("👨‍💻 Dev", url="https://t.me/junaidniz786")]
    ])
    for gid in GROUP_IDS:
        try:
            await bot.send_message(chat_id=gid, text=msg, parse_mode="HTML", reply_markup=keyboard)
        except: pass

# ============================
# MAIN LOOPS
# ============================
async def api_worker(panel_key):
    print(f"Worker {panel_key} started.")
    last_id = None
    while True:
        data = fetch_latest(panel_key)
        if data:
            current_id = f"{data['number']}_{data['message']}"
            if current_id != last_id:
                last_id = current_id
                if cli_passes_filter(data["service"]):
                    # Save OTP
                    otp = extract_otp(data["message"])
                    store = load_otp_store()
                    store[str(data["number"])] = otp
                    save_otp_store(store)
                    
                    # Send Alert
                    await send_to_groups(format_message(data))
        await asyncio.sleep(5) # 5 seconds gap to avoid IP block

async def main():
    print("Bot is starting...")
    tasks = [api_worker(p) for p in API_PANELS.keys()]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
    
