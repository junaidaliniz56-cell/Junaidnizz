import asyncio

import requests

import re

import phonenumbers

from phonenumbers import geocoder

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from datetime import datetime

BOT_TOKEN = "8299685411:AAHrwDwXawJV8zJcIweC1mcgsPhoBITnEgM"

bot = Bot(token=BOT_TOKEN)

GROUP_IDS = [

    -1003665350559,

]

# ============================

#      CR API SETTINGS

# ============================

CR_API_URL = "http://51.77.216.195/crapi/dgroup/viewstats"

CR_TOKEN = "RFRSNEVBdnh3V1NpVHCYQXNfl2hZiGx_R22GZop3d3pBZJJfXGU="

CR_RECORD_LIMIT = 20

# ============================

#      MAIT API SETTINGS

# ============================

MAIT_API_URL = "http://51.77.216.195/crapi/mait/viewstats"

MAIT_TOKEN = "SlRXRzRSQkV6dZGKRmaOV31ml3xKbolJU1CSYXVwinRpcoBVhV9v"

MAIT_RECORD_LIMIT = 20

# ============================

#    CLI FILTER SETTINGS

# ============================

ALLOWED_CLIS = [

    # "google",

    # "facebook",

    # "msverify"
    
    # "Whatsapp"

]

BLOCKED_CLIS = [

    # "ads",

    # "promo",

]

CLI_FILTER_MODE = "off"  # "allow" / "block" / "off"

def cli_passes_filter(cli):

    cli_lower = cli.lower()

    if CLI_FILTER_MODE == "allow":

        return any(a.lower() in cli_lower for a in ALLOWED_CLIS)

    elif CLI_FILTER_MODE == "block":

        return not any(b.lower() in cli_lower for b in BLOCKED_CLIS)

    return True

# ============================

#    FETCH CR API

# ============================

def fetch_latest_from_cr():

    try:

        response = requests.get(CR_API_URL, params={

            "token": CR_TOKEN,

            "records": CR_RECORD_LIMIT

        }, timeout=10)

        data = response.json()

        if data.get("status") != "success":

            print("CR API Error:", data)

            return None

        records = data.get("data", [])

        if not records:

            return None

        latest = records[0]

        return {

            "time": latest.get("dt", ""),

            "number": latest.get("num", ""),

            "service": latest.get("cli", ""),

            "message": latest.get("message", "")

        }

    except Exception as e:

        print("CR API Fetch Error:", e)

        return None

# ============================

#    FETCH MAIT API

# ============================

def fetch_latest_from_mait():

    try:

        response = requests.get(MAIT_API_URL, params={

            "token": MAIT_TOKEN,

            "records": MAIT_RECORD_LIMIT

        }, timeout=10)

        data = response.json()

        if data.get("status") != "success":

            print("MAIT API Error:", data)

            return None

        records = data.get("data", [])

        if not records:

            return None

        latest = records[0]

        return {

            "time": latest.get("dt", ""),

            "number": latest.get("num", ""),

            "service": latest.get("cli", ""),

            "message": latest.get("message", "")

        }

    except Exception as e:

        print("MAIT API Fetch Error:", e)

        return None

# ============================

#       HELPER FUNCTIONS

# ============================

def extract_otp(message):

    for pat in [r'\d{3}-\d{3}', r'\d{6}', r'\d{4}']:

        match = re.search(pat, message)

        if match:

            return match.group(0)

    return "N/A"

def mask_number(number_str):

    try:

        number_str = f"+{number_str}"

        length = len(number_str)

        show_first = 5 if length >= 10 else 4

        show_last = 4 if length >= 10 else 2

        stars = "*" * (length - show_first - show_last)

        return f"{number_str[:show_first]}{stars}{number_str[-show_last:]}"

    except:

        return f"+{number_str}"

def get_country_info(number_str):

    try:

        if not number_str.startswith("+"):

            number_str = "+" + number_str

        parsed = phonenumbers.parse(number_str)

        country_name = geocoder.description_for_number(parsed, "en")

        region = phonenumbers.region_code_for_number(parsed)

        if region:

            base = 127462 - ord("A")

            flag = chr(base + ord(region[0])) + chr(base + ord(region[1]))

        else:

            flag = "🌍"

        return country_name or "Unknown", flag

    except:

        return "Unknown", "🌍"

def format_message(record):

    raw = record["message"]

    otp = extract_otp(raw)

    clean = raw.replace("<", "&lt;").replace(">", "&gt;")

    country, flag = get_country_info(record["number"])

    masked = mask_number(record["number"])

    return f"""

<b>{flag} New {record['service']} OTP!</b>
<blockquote>🕐 Time: {record['time']}</blockquote>
<blockquote>{flag} Country: {country}</blockquote>
<blockquote>📲 Service: {record['service']}</blockquote>
<blockquote>📞 Number: {masked}</blockquote>
<blockquote>🔐 OTP: <code>{otp}</code></blockquote>
<blockquote>📩 Full Message:</blockquote>
<pre>{clean}</pre>
Powered by Kumail Khan

"""

async def send_to_all_groups(msg):

    keyboard = InlineKeyboardMarkup(inline_keyboard=[

        [

            InlineKeyboardButton(text="☎️ Numbers", url="https://t.me/PKNUMBER"),

            InlineKeyboardButton(text="📱 Channel",url="https://t.me/PKNUMBER")

        ],

        [

            InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/junaidniz786"),

            InlineKeyboardButton(text="🟢 Whatsapp", url="https://whatsapp.com/channel/0029Vaf1X3f6hENsP7dKm81z")

        ]

    ])

    for gid in GROUP_IDS:

        try:

            await bot.send_message(

                chat_id=gid,

                text=msg,

                parse_mode="HTML",

                reply_markup=keyboard

            )

        except Exception as e:

            print(f"Send Error -> {gid}: {e}")

# ============================

#         WORKERS

# ============================

async def cr_worker():

    print("[STARTED] CR API Worker")

    last = None

    while True:

        data = fetch_latest_from_cr()

        if data:

            if not cli_passes_filter(data["service"]):

                print("[FILTER] CR API Skipped:", data["service"])

                await asyncio.sleep(3)

                continue

            uniq = data["number"] + data["message"]

            if uniq != last:

                last = uniq

                msg = format_message(data)

                await send_to_all_groups(msg)

                print(f"[CR] Sent: {data['service']} | {data['number']}")

        await asyncio.sleep(3)

async def mait_worker():

    print("[STARTED] MAIT API Worker")

    last = None

    while True:

        data = fetch_latest_from_mait()

        if data:

            if not cli_passes_filter(data["service"]):

                print("[FILTER] MAIT API Skipped:", data["service"])

                await asyncio.sleep(3)

                continue

            uniq = data["number"] + data["message"]

            if uniq != last:

                last = uniq

                msg = format_message(data)

                await send_to_all_groups(msg)

                print(f"[MAIT] Sent: {data['service']} | {data['number']}")

        await asyncio.sleep(3)

# ============================

#          MAIN

# ============================

async def main():

    print("Starting Prime OTP Bot...")

    await asyncio.gather(

        cr_worker(),

        mait_worker()

    )

if __name__ == "__main__":

    asyncio.run(main())
