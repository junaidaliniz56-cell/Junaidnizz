import asyncio
import aiohttp
import requests
import re
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

# aiogram v3 fix
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
    },
    {
        "name": "BACKUP",
        "base": "http://109.236.84.81",
        "ajax": "/ints/agent/res/data_smscdr.php",
        "login_page": "/ints/login",
        "login_post": "/ints/signin",
        "username": "BODYELYOUTUBER",
        "password": "BODY EL YOUTUBER",
        "session": requests.Session(),
        "logged": False
    }
]

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# =====================================================
# CAPTCHA SOLVER
# =====================================================
def solve_math_captcha(html_text):
    try:
        # Extract numbers like "What is 10 + 10 ="
        match = re.search(r"What is (\d+)\s*\+\s*(\d+)\s*=", html_text)
        if match:
            n1, n2 = int(match.group(1)), int(match.group(2))
            result = n1 + n2
            print(f"[AUTO-SOLVER] Solved: {n1} + {n2} = {result}")
            return str(result)
    except Exception as e:
        print(f"Captcha extraction error: {e}")
    return "0"

def login_dashboard(dash):
    try:
        s = dash["session"]
        s.cookies.clear() # Clear old session to avoid "Connection Aborted"
        s.headers.update(COMMON_HEADERS)

        # Step 1: Get Login Page to fetch Captcha
        response = s.get(dash["base"] + dash["login_page"], timeout=15)
        captcha_answer = solve_math_captcha(response.text)

        # Step 2: Prepare Login Payload
        payload = {
            "username": dash["username"],
            "password": dash["password"],
            "answer": captcha_answer 
        }

        # Step 3: POST Login
        r = s.post(dash["base"] + dash["login_post"], data=payload, timeout=15, allow_redirects=True)

        # Success check: If redirected away from login page
        if r.status_code == 200 and "login" not in r.url.lower():
            dash["logged"] = True
            print(f"[SUCCESS] Logged into {dash['name']}")
            return True
        else:
            print(f"[FAILED] Login failed for {dash['name']}. Status: {r.status_code}")
    except Exception as e:
        print(f"[ERROR] Connection error on {dash['name']}: {e}")

    dash["logged"] = False
    return False

# =====================================================
# FETCHING & FORMATTING
# =====================================================
def fetch_otp(dash):
    try:
        if not dash["logged"]:
            if not login_dashboard(dash): return None

        r = dash["session"].get(dash["base"] + dash["ajax"], timeout=15)
        data = r.json()
        records = data.get("aaData", []) #
        if records:
            return {
                "time": records[0][0],
                "number": records[0][2],
                "service": records[0][3],
                "message": records[0][4]
            }
    except:
        dash["logged"] = False
    return None

def get_country_flag(number):
    try:
        num = "+" + str(number).lstrip("+")
        parsed = phonenumbers.parse(num, None)
        region = phonenumbers.region_code_for_number(parsed)
        country = geocoder.description_for_number(parsed, "en")
        flag = chr(127397 + ord(region[0])) + chr(127397 + ord(region[1])) if region else "🌍"
        return country or "Unknown", flag
    except: return "Unknown", "🌍"

async def send_to_telegram(otp):
    country, flag = get_country_flag(otp["number"])
    text = (f"<b>{flag} New {country} OTP</b>\n\n"
            f"<blockquote>🕰 Time: {otp['time']}</blockquote>\n"
            f"<blockquote>📱 Service: {otp['service']}</blockquote>\n"
            f"<blockquote>📞 Number: <code>{otp['number']}</code></blockquote>\n\n"
            f"<pre>{otp['message']}</pre>\n\n"
            f"Powered by <b>Junaid Niz</b>")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📱 Channel", url="https://t.me/jndtech1")
    ]])

    for gid in GROUP_IDS:
        try: await bot.send_message(gid, text, reply_markup=kb)
        except: pass

async def worker(dash):
    last_number = None
    print(f"Monitoring: {dash['name']}")
    while True:
        otp = fetch_otp(dash)
        if otp and otp["number"] != last_number:
            last_number = otp["number"]
            await send_to_telegram(otp)
            print(f"[SENT] OTP for {otp['number']} from {dash['name']}")
        await asyncio.sleep(6) # Increased sleep to prevent blocking

async def main():
    async with bot:
        await asyncio.gather(*(worker(d) for d in DASHBOARD_CONFIGS))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    
