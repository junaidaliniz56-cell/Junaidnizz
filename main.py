import asyncio
import aiohttp
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
        "base": "http://139.99.63.204",
        "ajax": "/ints/agent/res/data_smscdr.php",
        "login_page": "/ints/login",
        "login_post": "/ints/signin",
        "username": "Junaidniz786",
        "password": "Junaidniz786",
        "session": requests.Session(),
        "logged": False
    }
]

# Browser Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "X-Requested-With": "XMLHttpRequest"
}

# =====================================================
# AUTO-CAPTCHA SOLVER
# =====================================================
def solve_math_captcha(html_text):
    match = re.search(r"What is (\d+)\s*\+\s*(\d+)\s*=", html_text)
    if match:
        ans = int(match.group(1)) + int(match.group(2))
        print(f"[SOLVER] {match.group(1)} + {match.group(2)} = {ans}")
        return str(ans)
    return "0"

def login_dashboard(dash):
    try:
        s = dash["session"]
        s.cookies.clear() 
        s.headers.update(HEADERS)

        # Step 1: Login page se hidden fields aur captcha lena
        response = s.get(dash["base"] + dash["login_page"], timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hidden tokens collect karna
        payload = {}
        for hidden in soup.find_all("input", type="hidden"):
            payload[hidden.get("name")] = hidden.get("value")

        # Step 2: Captcha solve karna
        ans = solve_math_captcha(response.text)

        # Step 3: Login details update karna
        payload.update({
            "username": dash["username"],
            "password": dash["password"],
            "answer": ans
        })

        # Step 4: POST Login
        r = s.post(dash["base"] + dash["login_post"], data=payload, timeout=15, allow_redirects=True)

        # Verify login
        if r.status_code == 200 and "login" not in r.url.lower():
            dash["logged"] = True
            print(f"[SUCCESS] {dash['name']} Logged In")
            return True
        else:
            print(f"[FAIL] {dash['name']} Rejected. Check Password or Captcha.")
    except Exception as e:
        print(f"[ERR] {dash['name']}: {e}")
    
    dash["logged"] = False
    return False

# =====================================================
# OTP LOGIC
# =====================================================
def fetch_otp(dash):
    try:
        if not dash["logged"]:
            if not login_dashboard(dash): return None

        r = dash["session"].get(dash["base"] + dash["ajax"], timeout=15)
        data = r.json()
        records = data.get("aaData", []) #
        if records:
            return {"time": records[0][0], "num": records[0][2], "msg": records[0][4]}
    except:
        dash["logged"] = False
    return None

def get_flag(num):
    try:
        p = phonenumbers.parse("+" + str(num).lstrip("+"), None)
        r = phonenumbers.region_code_for_number(p)
        f = chr(127397 + ord(r[0])) + chr(127397 + ord(r[1])) if r else "🌍"
        return f
    except: return "🌍"

async def worker(dash):
    last_id = None
    while True:
        otp = fetch_otp(dash)
        if otp and otp["num"] != last_id:
            last_id = otp["num"]
            flag = get_flag(otp["num"])
            text = f"{flag} <b>New OTP</b>\n\n📞 <code>{otp['num']}</code>\n📩 {otp['msg']}"
            for gid in GROUP_IDS:
                await bot.send_message(gid, text)
        await asyncio.sleep(8) # Block hone se bachne ke liye delay zyada rakha hai

async def main():
    print("Bot starting with Hidden Token Support...")
    async with bot:
        await asyncio.gather(*(worker(d) for d in DASHBOARD_CONFIGS))

if __name__ == "__main__":
    asyncio.run(main())
        
