import telebot, os, json, time, requests
from telebot import types

BOT_TOKEN = "8569662345:AAGdjpXHCKq8lYDc9DVQplDRk5bRosN7nwg"
ADMINS = [7011937754]  # 👈 your Telegram ID

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ---------- FILES ----------
FILES = {
    "numbers": "numbers.json",
    "channels": "channels.json",
    "groups": "otp_groups.json",
    "apis": "sms_apis.json",
    "user_otps": "user_otps.json"
}

def load(f, d):
    if os.path.exists(f):
        return json.load(open(f))
    return d

def save(f, d):
    json.dump(d, open(f, "w"), indent=2)

NUMBERS = load(FILES["numbers"], {})
CHANNELS = load(FILES["channels"], [])
OTP_GROUPS = load(FILES["groups"], [])
SMS_APIS = load(FILES["apis"], [])
USER_OTPS = load(FILES["user_otps"], {})

STATE = {}

# ---------- HELPERS ----------
def is_admin(uid): return uid in ADMINS

def joined(uid):
    for ch in CHANNELS:
        try:
            m = bot.get_chat_member(ch["id"], uid)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(m):
    if not joined(m.chat.id):
        kb = types.InlineKeyboardMarkup()
        for c in CHANNELS:
            kb.add(types.InlineKeyboardButton(c["name"], url=c["link"]))
        kb.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
        bot.send_message(m.chat.id, "❌ Join required channels", reply_markup=kb)
        return
    show_countries(m.chat.id)

@bot.callback_query_handler(func=lambda c: c.data=="verify")
def verify(c):
    if joined(c.from_user.id):
        show_countries(c.from_user.id)
    else:
        bot.answer_callback_query(c.id, "Join all channels", show_alert=True)

# ---------- USER PANEL ----------
def show_countries(uid):
    if not NUMBERS:
        bot.send_message(uid, "❌ No numbers available")
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    for c in NUMBERS:
        kb.add(types.InlineKeyboardButton(f"{c} ({len(NUMBERS[c])})", callback_data=f"pick|{c}"))
    bot.send_message(uid, "🌍 <b>Select Country</b>", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("pick|"))
def pick(c):
    country = c.data.split("|")[1]
    if not NUMBERS.get(country):
        bot.answer_callback_query(c.id, "No numbers left")
        return

    number = NUMBERS[country].pop(0)
    save(FILES["numbers"], NUMBERS)

    USER_OTPS.setdefault(str(c.from_user.id), []).append({
        "number": number, "otp": None, "time": time.time()
    })
    save(FILES["user_otps"], USER_OTPS)

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔄 Change Number", callback_data=f"pick|{country}"),
        types.InlineKeyboardButton("🌍 Change Country", callback_data="back")
    )
    kb.add(
        types.InlineKeyboardButton("📜 View Past OTPs", callback_data="past"),
        types.InlineKeyboardButton("📢 OTP Group", url="https://t.me/YOURGROUP")
    )

    bot.edit_message_text(
        f"📞 <b>Your Number ({country})</b>\n<code>{number}</code>\n\n⏳ Waiting for OTP...",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda c: c.data=="back")
def back(c):
    show_countries(c.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data=="past")
def past(c):
    data = USER_OTPS.get(str(c.from_user.id), [])
    if not data:
        bot.answer_callback_query(c.id, "No OTPs")
        return
    txt = ""
    for o in data[-5:]:
        txt += f"📞 {o['number']} | OTP: {o['otp']}\n"
    bot.send_message(c.from_user.id, f"<pre>{txt}</pre>")

# ---------- ADMIN PANEL ----------
@bot.message_handler(commands=["admin"])
def admin(m):
    if not is_admin(m.chat.id): return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Add Numbers", "📋 Number List")
    kb.add("➕ Add Channel", "📢 Channels")
    kb.add("➕ Add OTP Group", "📢 OTP Groups")
    kb.add("➕ Add SMS API", "🔌 SMS APIs")
    kb.add("❌ Close")
    bot.send_message(m.chat.id, "🛠 <b>Admin Panel</b>", reply_markup=kb)

# ---------- ADD NUMBERS ----------
@bot.message_handler(func=lambda m: m.text=="➕ Add Numbers")
def add_numbers(m):
    STATE[m.chat.id] = "country"
    bot.send_message(m.chat.id, "Send country name")

@bot.message_handler(func=lambda m: STATE.get(m.chat.id)=="country")
def get_country(m):
    STATE[m.chat.id] = {"country": m.text}
    bot.send_message(m.chat.id, "Send number.txt file")

@bot.message_handler(content_types=["document"])
def recv_file(m):
    st = STATE.get(m.chat.id)
    if not st: return
    file = bot.download_file(bot.get_file(m.document.file_id).file_path)
    nums = file.decode().splitlines()
    NUMBERS.setdefault(st["country"], []).extend(nums)
    save(FILES["numbers"], NUMBERS)
    bot.send_message(m.chat.id, f"✅ {len(nums)} numbers added")
    STATE.pop(m.chat.id)

# ---------- SMS API WORKER ----------
def poll_sms():
    while True:
        for api in SMS_APIS:
            try:
                r = requests.get(api, timeout=10).json()
                for row in r.get("data", []):
                    otp = row["otp"]
                    num = row["number"]

                    # send to groups
                    for g in OTP_GROUPS:
                        bot.send_message(g, f"📩 OTP\n{num} → {otp}")

                    # send to user if matched
                    for uid, arr in USER_OTPS.items():
                        for o in arr:
                            if o["number"] == num and o["otp"] is None:
                                o["otp"] = otp
                                bot.send_message(int(uid), f"✅ OTP Received\n{otp}")
                                save(FILES["user_otps"], USER_OTPS)
            except:
                pass
        time.sleep(5)

import threading
threading.Thread(target=poll_sms, daemon=True).start()

print("🤖 BOT RUNNING")
bot.infinity_polling()
