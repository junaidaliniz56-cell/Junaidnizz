import telebot
import requests
import json
import re
import time

BOT_TOKEN = "8569662345:AAGdjpXHCKq8lYDc9DVQplDRk5bRosN7nwg"
ADMIN_ID = 7011937754   # 👈 user ka Telegram ID

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
DATA_FILE = "otp_data.json"

def load():
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except:
        return {
            "apis": [],
            "groups": [],
            "last_ids": {}
        }

def save(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

data = load()

def is_admin(uid):
    return uid == ADMIN_ID

# ---------------- ADMIN ----------------
@bot.message_handler(commands=["admin"])
def admin(m):
    if not is_admin(m.from_user.id): return

    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Add SMS API", "➕ Add Group ID")
    kb.add("📋 List APIs", "📋 List Groups")
    bot.send_message(m.chat.id, "⚙️ <b>OTP BOT ADMIN</b>", reply_markup=kb)

# ---------------- API ----------------
@bot.message_handler(func=lambda m: m.text == "➕ Add SMS API")
def add_api(m):
    bot.send_message(m.chat.id, "Send SMS API URL:")
    bot.register_next_step_handler(m, save_api)

def save_api(m):
    url = m.text.strip()
    if url not in data["apis"]:
        data["apis"].append(url)
        save(data)
    bot.send_message(m.chat.id, "✅ API added")

# ---------------- GROUP ----------------
@bot.message_handler(func=lambda m: m.text == "➕ Add Group ID")
def add_group(m):
    bot.send_message(m.chat.id, "Send GROUP ID:")
    bot.register_next_step_handler(m, save_group)

def save_group(m):
    gid = m.text.strip()
    if gid not in data["groups"]:
        data["groups"].append(gid)
        save(data)
    bot.send_message(m.chat.id, "✅ Group added")

# ---------------- FETCH OTP ----------------
def extract_otp(text):
    m = re.search(r"\b\d{4,6}\b", text)
    return m.group() if m else "N/A"

def poll():
    while True:
        for api in data["apis"]:
            try:
                r = requests.get(api, timeout=10).json()
                rows = r.get("aaData", [])
                if not rows:
                    continue

                row = rows[0]
                msg = row[-1]
                otp = extract_otp(msg)

                last = data["last_ids"].get(api)
                if last == msg:
                    continue

                data["last_ids"][api] = msg
                save(data)

                text = f"""
🔐 <b>NEW OTP</b>

📩 {msg}
🔑 <code>{otp}</code>

Powered by You ❤️
"""
                for g in data["groups"]:
                    bot.send_message(g, text)

            except:
                pass

        time.sleep(3)

import threading
threading.Thread(target=poll, daemon=True).start()

bot.infinity_polling()
