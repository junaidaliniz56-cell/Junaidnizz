import asyncio
import requests
import re
from bs4 import BeautifulSoup
import phonenumbers
from phonenumbers import geocoder
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

# =====================================================
# BOT CONFIG
# =====================================================
BOT_TOKEN = "8495469799:AAEeO1X4uIgVBBH1A-NQTOLbVOoLjOB0Z1A"
GROUP_IDS = [-1003361941052]

# Error Fix: Use DefaultBotProperties for aiogram v3
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
        "session": requests.Session(), # Keep session alive for captcha
        "logged": False
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "http://139.99.63.204/ints/login"
}

# =====================================================
# SOLVER LOGIC
# =====================================================
def solve_captcha(html):
    match = re.search(r"What is (\d+)\s*\+\s*(\d+)\s*=", html)
    if match:
        ans = int(match.group(1)) + int(match.group(2))
        print(f"[SOLVER] {match.group(1)} + {match.group(2)} = {ans}")
        return str(ans)
    return None

def login_dashboard(dash):
    try:
        s = dash["session"]
        s.headers.update(HEADERS)

        # Step 1: Page load karo aur cookies save hone do
        print(f"[STEP 1] Getting login page for {dash['name']}...")
        res = s.get(dash["base"] + dash["login_page"], timeout=15)
        
        # Step 2: Captcha solve karo
        ans = solve_captcha(res.text)
        if not ans: return False

        # Step 3: Login Payload (Wahi session use karke jo page load kiya tha)
        payload = {
            "username": dash["username"],
            "password": dash["password"],
            "answer": ans
        }

        print(f"[STEP 2] Sending login request with answer {ans}...")
        r = s.post(dash["base"] + dash["login_post"], data=payload, timeout=15, allow_redirects=True)

        # Step 4: Verify Success
        if r.status_code == 200 and "login" not in r.url.lower():
            dash["logged"] = True
            print(f"[SUCCESS] Login OK for {dash['name']}")
            return True
        else:
            print(f"[FAIL] Server rejected the answer for {dash['name']}")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

# =====================================================
# OTP MONITORING
# =====================================================
async def worker(dash):
    last_val = None
    while True:
        if not dash["logged"]:
            login_dashboard(dash)
        
        if dash["logged"]:
            try:
                # Dashboard se data uthana
                r = dash["session"].get(dash["base"] + dash["ajax"], timeout=10)
                data = r.json()
                records = data.get("aaData", [])
                
                if records and records[0][2] != last_val:
                    last_val = records[0][2]
                    num = records[0][2]
                    msg = records[0][4]
                    
                    # Formatting
                    text = f"<b>🆕 New OTP Received</b>\n\n📞 <code>{num}</code>\n📩 <code>{msg}</code>"
                    for gid in GROUP_IDS:
                        await bot.send_message(gid, text)
                    print(f"[SENT] Message for {num}")
            except Exception:
                print(f"[SESSION EXPIRED] Re-logging {dash['name']}...")
                dash["logged"] = False

        await asyncio.sleep(10)

async def main():
    print("🚀 Bot is running with Session Persistence...")
    async with bot:
        await asyncio.gather(*(worker(d) for d in DASHBOARD_CONFIGS))

if __name__ == "__main__":
    asyncio.run(main())
        
