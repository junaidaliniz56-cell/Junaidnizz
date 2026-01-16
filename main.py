import asyncio
import aiohttp
import requests
import re
from datetime import datetime
import phonenumbers
from phonenumbers import geocoder
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

# =====================================================
# BOT CONFIG
# =====================================================
BOT_TOKEN = "8495469799:AAEeO1X4uIgVBBH1A-NQTOLbVOoLjOB0Z1A" # Apna Bot Token dalein
GROUP_IDS = [-1003361941052]

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

DASHBOARD_CONFIGS = [
    {
        "name": "PRIMARY",
        "base": "http://139.99.63.204",
        "ajax": "/ints/agent/res/data_smscdr.php",
        "login_page": "/ints/login",
        "login_post": "/ints/signin",
        "username": "Mrking",
        "password": "mrkingbrand1",
        "session": requests.Session(),
        "logged": False
    }
]

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

# =====================================================
# YE FUNCTION HAR BAAR NAYA CAPTCHA KHUD DEKHEGA
# =====================================================
def solve_math_captcha(html_text):
    try:
        # Ye line page se "What is 3 + 9 =" ya "What is 10 + 10 =" ko khud dhoondti hai
        match = re.search(r"What is (\d+)\s*\+\s*(\d+)\s*=", html_text)
        if match:
            num1 = int(match.group(1))
            num2 = int(match.group(2))
            result = num1 + num2
            print(f"[AUTO-SOLVER] Captcha Found: {num1} + {num2} = {result}")
            return str(result)
    except Exception as e:
        print(f"Captcha Error: {e}")
    return "0"

def login_dashboard(dash):
    try:
        s = dash["session"]
        s.headers.update(COMMON_HEADERS)

        # 1. Pehle login page load karo naya captcha dekhne ke liye
        response = s.get(dash["base"] + dash["login_page"], timeout=15)
        
        # 2. Captcha khud hi solve karo
        captcha_answer = solve_math_captcha(response.text)

        # 3. Username, Password aur Auto-solved answer submit karo
        payload = {
            "username": dash["username"],
            "password": dash["password"],
            "answer": captcha_answer 
        }

        r = s.post(dash["base"] + dash["login_post"], data=payload, timeout=15)

        if r.status_code == 200 and "agent" in r.url.lower():
            dash["logged"] = True
            print(f"[SUCCESS] Login successful for {dash['name']}")
            return True
        else:
            print(f"[FAILED] Login failed. Answer {captcha_answer} might be wrong or session expired.")

    except Exception as e:
        print(f"[ERROR] {dash['name']}: {e}")

    dash["logged"] = False
    return False

# =====================================================
# OTP FETCH & SEND LOGIC
# =====================================================
def fetch_latest_otp(dash):
    try:
        if not dash["logged"]:
            if not login_dashboard(dash): return None

        r = dash["session"].get(dash["base"] + dash["ajax"], timeout=20)
        data = r.json()
        records = data.get("aaData", [])
        if not records: return None
        
        latest = records[0]
        return {
            "time": latest[0],
            "number": str(latest[2]),
            "service": str(latest[3]),
            "message": str(latest[4]),
        }
    except:
        dash["logged"] = False
        return None

async def worker(dash):
    last_num = None
    while True:
        otp = fetch_latest_otp(dash)
        if otp and otp["number"] != last_num:
            last_num = otp["number"]
            # Formatting and sending logic
            text = f"<b>New OTP</b>\n\nNumber: {otp['number']}\nService: {otp['service']}\nCode: <code>{otp['message']}</code>"
            for gid in GROUP_IDS:
                await bot.send_message(gid, text)
        await asyncio.sleep(5)

async def main():
    print("Bot is LIVE with AUTO-CAPTCHA SOLVER...")
    async with bot:
        await asyncio.gather(*(worker(d) for d in DASHBOARD_CONFIGS))

if __name__ == "__main__":
    asyncio.run(main())
        
