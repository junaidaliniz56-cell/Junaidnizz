import telebot
import requests
import json
import os
import re
import threading
import time
from telebot import types
import phonenumbers
from phonenumbers import geocoder

# ================= CONFIG =================
BOT_TOKEN = "8546188939:AAGCchjT0fnBRmgeKVz87S1i7cIkhVOfZHI"
ADMINS = [7011937754]   # 👈 apni Telegram ID

DATA_FILE = "data.json"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ================= STORAGE =================
def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "numbers": {},
        "channels": [],
        "otp_groups": [],
        "sms_apis": [],
        "user_current": {},
        "user_otps": {},
        "buttons": {
            "channel": None,
            "numbers": None,
            "developer": None,
            "youtube": None
        }
    }

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load()
STATE = {}

def is_admin(uid):
    return uid in ADMINS

# ================= COUNTRY + SERVICE =================
def get_country_flag(number):
    try:
        if not number.startswith("+"):
            number = "+" + number
        p = phonenumbers.parse(number)
        region = phonenumbers.region_code_for_number(p)
        if not region:
            return "🌍", "Unknown"
        base = 127462 - ord("A")
        flag = chr(base + ord(region[0])) + chr(base + ord(region[1]))
        country = geocoder.description_for_number(p, "en")
        return flag, country
    except:
        return "🌍", "Unknown"

def service_icon(msg):
    m = msg.lower()
    if "whatsapp" in m:
        return "🟢 WhatsApp"
    if "telegram" in m:
        return "🔵 Telegram"
    if "facebook" in m:
        return "📘 Facebook"
    if "google" in m or "gmail" in m:
        return "📧 Google"
    return "📱 Service"

def extract_otp(text):
    m = re.search(r"\b\d{4,6}\b", text)
    return m.group(0) if m else None

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    show_countries(m.chat.id)

# ================= USER PANEL =================
def show_countries(uid):
    if not data["numbers"]:
        bot.send_message(uid, "❌ No numbers available")
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    for c in data["numbers"]:
        kb.add(types.InlineKeyboardButton(
            f"🌍 {c} ({len(data['numbers'][c])})",
            callback_data=f"country|{c}"
        ))
    bot.send_message(uid, "🌍 Select Country", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("country|"))
def pick_country(c):
    country = c.data.split("|")[1]
    if not data["numbers"].get(country):
        bot.answer_callback_query(c.id, "❌ No numbers", show_alert=True)
        return

    num = data["numbers"][country].pop(0)
    uid = str(c.from_user.id)
    data["user_current"][uid] = num
    data["user_otps"].setdefault(uid, [])
    save()

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔄 Change Number", callback_data=f"country|{country}"),
        types.InlineKeyboardButton("🌍 Change Country", callback_data="back")
    )
    kb.add(types.InlineKeyboardButton("📜 View Past OTPs", callback_data="past"))

    if data["buttons"]["channel"]:
        kb.add(types.InlineKeyboardButton("📢 OTP Group", url=data["buttons"]["channel"]))

    bot.edit_message_text(
        f"<b>📞 Your Number</b>\n\n<code>{num}</code>\n\n⏳ Waiting for OTP...",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda c: c.data == "back")
def back(c):
    show_countries(c.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data == "past")
def past(c):
    otps = data["user_otps"].get(str(c.from_user.id), [])
    txt = "\n".join(otps[-10:]) or "No OTPs yet"
    bot.send_message(c.from_user.id, f"<b>📜 Past OTPs</b>\n\n{txt}")

# ================= ADMIN PANEL =================
@bot.message_handler(commands=["admin"])
def admin(m):
    if not is_admin(m.chat.id):
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Add Numbers", "➕ Add SMS API")
    kb.add("➕ Add OTP Group")
    kb.add("➕ Set Channel Button", "➕ Set Numbers Button")
    kb.add("➕ Set Developer Button", "➕ Set YouTube Button")
    kb.add("❌ Close")
    bot.send_message(m.chat.id, "🛠 Admin Panel", reply_markup=kb)

# ---------- ADD NUMBERS ----------
@bot.message_handler(func=lambda m: m.text == "➕ Add Numbers")
def add_numbers(m):
    STATE[m.chat.id] = "country"
    bot.send_message(m.chat.id, "🌍 Send Country Name")

@bot.message_handler(func=lambda m: STATE.get(m.chat.id) == "country")
def get_country(m):
    STATE[m.chat.id] = {"country": m.text}
    bot.send_message(m.chat.id, "📄 Send number.txt file")

@bot.message_handler(content_types=["document"])
def recv_file(m):
    st = STATE.get(m.chat.id)
    if not st or "country" not in st:
        return
    file = bot.download_file(bot.get_file(m.document.file_id).file_path)
    nums = file.decode().splitlines()
    c = st["country"]
    data["numbers"].setdefault(c, []).extend(nums)
    save()
    STATE.pop(m.chat.id)
    bot.send_message(m.chat.id, f"✅ {len(nums)} numbers added")

# ---------- SMS API ----------
@bot.message_handler(func=lambda m: m.text == "➕ Add SMS API")
def add_api(m):
    STATE[m.chat.id] = "api"
    bot.send_message(m.chat.id, "Send SMS API URL")

@bot.message_handler(func=lambda m: STATE.get(m.chat.id) == "api")
def save_api(m):
    data["sms_apis"].append(m.text)
    save()
    threading.Thread(target=sms_worker, args=(m.text,), daemon=True).start()
    STATE.pop(m.chat.id)
    bot.send_message(m.chat.id, "✅ API added & worker started")

# ---------- OTP GROUP ----------
@bot.message_handler(func=lambda m: m.text == "➕ Add OTP Group")
def add_otp_group(m):
    STATE[m.chat.id] = "otpgrp"
    bot.send_message(m.chat.id, "Send PRIVATE GROUP ID\nExample: -1001234567890")

@bot.message_handler(func=lambda m: STATE.get(m.chat.id) == "otpgrp")
def save_otp_group(m):
    data["otp_groups"].append(int(m.text))
    save()
    STATE.pop(m.chat.id)
    bot.send_message(m.chat.id, "✅ OTP Group added")

# ---------- BUTTONS ----------
@bot.message_handler(func=lambda m: m.text.startswith("➕ Set"))
def set_button(m):
    STATE[m.chat.id] = m.text
    bot.send_message(m.chat.id, "Send URL")

@bot.message_handler(func=lambda m: isinstance(STATE.get(m.chat.id), str) and STATE[m.chat.id].startswith("➕ Set"))
def save_button(m):
    t = STATE[m.chat.id]
    if "Channel" in t:
        data["buttons"]["channel"] = m.text
    elif "Numbers" in t:
        data["buttons"]["numbers"] = m.text
    elif "Developer" in t:
        data["buttons"]["developer"] = m.text
    elif "YouTube" in t:
        data["buttons"]["youtube"] = m.text
    save()
    STATE.pop(m.chat.id)
    bot.send_message(m.chat.id, "✅ Button saved")

# ================= SMS WORKER =================
def sms_worker(api):
    last = None
    while True:
        try:
            r = requests.get(api, timeout=10).json()
            rows = r.get("aaData", [])
            if not rows:
                time.sleep(3)
                continue

            row = rows[0]
            msg = row[-1]
            num = str(row[2])
            otp = extract_otp(msg)
            if not otp:
                time.sleep(3)
                continue

            key = num + otp
            if key == last:
                time.sleep(3)
                continue
            last = key

            flag, country = get_country_flag(num)
            service = service_icon(msg)

            text = f"""
<b>{flag} New OTP Received!</b>

<blockquote>{flag} Country: {country}</blockquote>
<blockquote>{service}</blockquote>
<blockquote>📞 Number: <code>{num}</code></blockquote>
<blockquote>🔑 OTP: <code>{otp}</code></blockquote>

<blockquote>📩 Message:</blockquote>
<pre>{msg}</pre>
"""

            keyboard = types.InlineKeyboardMarkup(row_width=2)
            for k, v in data["buttons"].items():
                if v:
                    keyboard.add(types.InlineKeyboardButton(k.capitalize(), url=v))

            for gid in data["otp_groups"]:
                bot.send_message(gid, text, reply_markup=keyboard)

            for uid, u_num in data["user_current"].items():
                if u_num == num:
                    bot.send_message(int(uid), f"<b>🔑 Your OTP</b>\n\n<code>{otp}</code>")
                    data["user_otps"][uid].append(f"{num} → {otp}")
                    save()

        except:
            pass
        time.sleep(3)

# ================= START =================
for api in data["sms_apis"]:
    threading.Thread(target=sms_worker, args=(api,), daemon=True).start()

print("🤖 Bot Running")
bot.infinity_polling()
