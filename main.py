import asyncio
import aiohttp
import requests
import re
import json
import sqlite3
from datetime import datetime
import phonenumbers
from phonenumbers import geocoder
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# =====================================================
# BOT CONFIG
# =====================================================
BOT_TOKEN = "8495469799:AAEeO1X4uIgVBBH1A-NQTOLbVOoLjOB0Z1A"
GROUP_IDS = [
    -1003361941052,
]

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")

# =====================================================
# DASHBOARD CONFIG (LOGIN BASED)
# =====================================================
DASHBOARD_CONFIGS = [
    {
        "name": "PRIMARY",
        "base": "http://139.99.63.204",
        "ajax": "/ints/agent/res/data_smscdr.php",
        "login_page": "/ints/login",
        "login_post": "/ints/signin",
        "username": "Junaidniz786",
        "password": "Junaidniz786",
        "session": requests.Session(),
        "logged": False
    },
    {
        "name": "BACKUP",
        "base": "http://109.236.84.81",
        "ajax": "/ints/agent/res/data_smscdr.php",
        "login_page": "/ints/login",
        "login_post": "/ints/signin",
        "username": "Junaidniz786",
        "password": "Junaidniz786",
        "session": requests.Session(),
        "logged": False
    }
]

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json"
}

# =====================================================
# LOGIN FUNCTION
# =====================================================
def login_dashboard(dash):
    try:
        s = dash["session"]
        s.headers.update(COMMON_HEADERS)

        s.get(dash["base"] + dash["login_page"], timeout=15)

        payload = {
            "username": dash["username"],
            "password": dash["password"]
        }

        r = s.post(dash["base"] + dash["login_post"], data=payload, timeout=15)

        if r.status_code == 200:
            dash["logged"] = True
            print(f"[LOGIN OK] {dash['name']}")
            return True

    except Exception as e:
        print(f"[LOGIN ERROR] {dash['name']} {e}")

    dash["logged"] = False
    return False


# =====================================================
# FETCH OTP FROM DASHBOARD
# =====================================================
def fetch_latest_otp(dash):
    try:
        if not dash["logged"]:
            if not login_dashboard(dash):
                return None

        url = dash["base"] + dash["ajax"]
        r = dash["session"].get(url, timeout=20)
        data = r.json()

        records = data.get("aaData", [])
        valid = [r for r in records if isinstance(r[0], str) and ":" in r[0]]
        if not valid:
            return None

        latest = valid[0]
        return {
            "time": latest[0],
            "number": str(latest[2]),
            "service": str(latest[3]),
            "message": str(latest[4])
        }

    except Exception as e:
        print(f"[FETCH ERROR] {dash['name']} {e}")
        dash["logged"] = False
        return None


# =====================================================
# OTP EXTRACT
# =====================================================
def extract_otp(message):
    for p in [r"\d{6}", r"\d{4}", r"\d{3}-\d{3}"]:
        m = re.search(p, message)
        if m:
            return m.group()
    return "N/A"


# =====================================================
# MASK NUMBER
# =====================================================
def mask_number(num):
    try:
        num = "+" + num.lstrip("+")
        return f"{num[:5]}{'*'*(len(num)-9)}{num[-4:]}"
    except:
        return num


# =====================================================
# COUNTRY + FLAG (FIXED & VERIFIED)
# =====================================================
def get_country_info(number):
    try:
        number = "+" + number.lstrip("+")
        parsed = phonenumbers.parse(number, None)

        if not phonenumbers.is_valid_number(parsed):
            return "Unknown", "🌍"

        country = geocoder.description_for_number(parsed, "en")
        region = phonenumbers.region_code_for_number(parsed)

        base = 127397
        flag = chr(base + ord(region[0])) + chr(base + ord(region[1])) if region else "🌍"

        return country or "Unknown", flag

    except:
        return "Unknown", "🌍"


# =====================================================
# FORMAT MESSAGE
# =====================================================
def format_message(r):
    otp = extract_otp(r["message"])
    masked = mask_number(r["number"])
    country, flag = get_country_info(r["number"])

    icon = "📱"
    s = r["service"].lower()
    if "whatsapp" in s:
        icon = "🟢"
    elif "telegram" in s:
        icon = "🔵"
    elif "facebook" in s:
        icon = "📘"

    return f"""
<b>{flag} New {country} OTP</b>

<blockquote>🕰 Time: {r['time']}</blockquote>
<blockquote>{flag} Country: {country}</blockquote>
<blockquote>{icon} Service: {r['service']}</blockquote>
<blockquote>📞 Number: {masked}</blockquote>
<blockquote>🔑 OTP: <code>{otp}</code></blockquote>

<blockquote>📩 Message:</blockquote>
<pre>{r['message']}</pre>

Powered by <b>Junaid Niz</b> 💗
"""


# =====================================================
# SEND TO GROUPS
# =====================================================
async def send_groups(text):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Channel", url="https://t.me/jndtech1"),
            InlineKeyboardButton(text="☎️ Numbers", url="https://t.me/+c4VCxBCT3-QzZGFk")
        ]
    ])

    for g in GROUP_IDS:
        try:
            await bot.send_message(g, text, reply_markup=kb)
        except Exception as e:
            print("Send error:", e)


# =====================================================
# MAIN LOOP
# =====================================================
async def dashboard_worker(dash):
    last = None
    while True:
        otp = fetch_latest_otp(dash)
        if otp and otp["number"] != last:
            last = otp["number"]
            await send_groups(format_message(otp))
            print(f"[SENT] {otp['number']} from {dash['name']}")
        await asyncio.sleep(3)


async def main():
    await asyncio.gather(*(dashboard_worker(d) for d in DASHBOARD_CONFIGS))


if __name__ == "__main__":
    asyncio.run(main())
