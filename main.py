import telebot, os, json, threading, time, requests, re
from telebot import types
from datetime import datetime

# ================= CONFIG =================
BOT_TOKEN = "8569662345:AAGdjpXHCKq8lYDc9DVQplDRk5bRosN7nwg"
ADMINS = [7011937754]               # 👈 ONLY YOU
OTP_GROUP_ID = -1003361941052       # 👈 GROUP WHERE ALL OTPs GO

SMS_APIS = [
    "https://www.kamibroken.pw/api/sms?type=sms",
    "https://www.kamibroken.pw/api/sms1?type=sms"
]

# ================= FILES =================
NUM_FILE = "numbers.json"
CH_FILE = "channels.json"
OTP_FILE = "otp_data.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ================= LOAD / SAVE =================
def load(f, d):
    if os.path.exists(f):
        with open(f) as x: return json.load(x)
    return d

def save(f, d):
    with open(f, "w") as x: json.dump(d, x, indent=2)

NUMBERS = load(NUM_FILE, {})
CHANNELS = load(CH_FILE, [])
OTP_DATA = load(OTP_FILE, {"user_current": {}, "user_otps": {}})
STATE = {}

# ================= UTILS =================
def is_admin(uid): return uid in ADMINS

def extract_otp(txt):
    m = re.search(r"\b\d{3}[- ]?\d{3}\b|\b\d{4,6}\b", txt)
    return m.group(0) if m else None

# ================= JOIN CHECK =================
def joined(uid):
    for ch in CHANNELS:
        try:
            m = bot.get_chat_member(ch["id"], uid)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    if not joined(m.chat.id):
        kb = types.InlineKeyboardMarkup()
        for c in CHANNELS:
            kb.add(types.InlineKeyboardButton(f"Join {c['name']}", url=c["link"]))
        kb.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
        bot.send_message(m.chat.id, "❌ Join all channels", reply_markup=kb)
        return
    show_countries(m.chat.id)

@bot.callback_query_handler(func=lambda c: c.data=="verify")
def verify(c):
    if joined(c.from_user.id):
        bot.answer_callback_query(c.id, "✅ Verified")
        show_countries(c.from_user.id)
    else:
        bot.answer_callback_query(c.id, "❌ Join required", show_alert=True)

# ================= USER PANEL =================
def show_countries(cid):
    if not NUMBERS:
        bot.send_message(cid, "❌ No numbers available")
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    for c in NUMBERS:
        kb.add(types.InlineKeyboardButton(
            f"🌍 {c} ({len(NUMBERS[c])})",
            callback_data=f"pick|{c}"
        ))
    kb.add(types.InlineKeyboardButton("📜 View Past OTPs", callback_data="past"))
    kb.add(types.InlineKeyboardButton("📢 OTP Group", url="https://t.me/YOURGROUP"))
    bot.send_message(cid, "🌍 <b>Select Country</b>", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("pick|"))
def pick(c):
    country = c.data.split("|")[1]
    if not NUMBERS.get(country):
        bot.answer_callback_query(c.id, "❌ Empty")
        return

    number = NUMBERS[country].pop(0)
    save(NUM_FILE, NUMBERS)

    OTP_DATA["user_current"][str(c.from_user.id)] = {
        "country": country,
        "number": number
    }
    save(OTP_FILE, OTP_DATA)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔄 Change Number", callback_data=f"pick|{country}"))
    kb.add(types.InlineKeyboardButton("🌍 Change Country", callback_data="back"))

    bot.edit_message_text(
        f"📞 <b>Your Number ({country})</b>\n<code>{number}</code>\n\n⏳ Waiting for OTP...",
        c.message.chat.id, c.message.message_id,
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda c: c.data=="back")
def back(c):
    show_countries(c.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data=="past")
def past(c):
    lst = OTP_DATA["user_otps"].get(str(c.from_user.id), [])
    if not lst:
        bot.answer_callback_query(c.id, "No OTPs")
        return

    txt = "\n\n".join(
        f"📞 {o['number']}\n🔑 {o['otp']}\n🕒 {o['time']}"
        for o in lst[-5:]
    )
    bot.send_message(c.from_user.id, f"📜 <b>Past OTPs</b>\n\n{txt}")

# ================= ADMIN PANEL =================
@bot.message_handler(commands=["admin"])
def admin(m):
    if not is_admin(m.chat.id): return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Add Numbers", "📋 Number List")
    kb.add("➕ Add Channel", "📢 Channels")
    kb.add("❌ Close")
    bot.send_message(m.chat.id, "⚙ <b>Admin Panel</b>", reply_markup=kb)

# ================= ADD NUMBERS =================
@bot.message_handler(func=lambda m: m.text=="➕ Add Numbers")
def add_nums(m):
    STATE[m.chat.id] = "country"
    bot.send_message(m.chat.id, "🌍 Send Country Name")

@bot.message_handler(func=lambda m: STATE.get(m.chat.id)=="country")
def recv_country(m):
    STATE[m.chat.id] = {"country": m.text}
    bot.send_message(m.chat.id, "📄 Send number.txt file")

@bot.message_handler(content_types=["document"])
def recv_file(m):
    st = STATE.get(m.chat.id)
    if not st or "country" not in st: return

    file = bot.download_file(bot.get_file(m.document.file_id).file_path)
    nums = file.decode().splitlines()

    NUMBERS.setdefault(st["country"], []).extend(nums)
    save(NUM_FILE, NUMBERS)

    bot.send_message(m.chat.id, f"✅ {len(nums)} numbers added")
    STATE.pop(m.chat.id)

# ================= NUMBER DELETE =================
@bot.message_handler(func=lambda m: m.text=="📋 Number List")
def list_nums(m):
    kb = types.InlineKeyboardMarkup()
    for c in NUMBERS:
        kb.add(types.InlineKeyboardButton(f"{c} ❌", callback_data=f"delnum|{c}"))
    bot.send_message(m.chat.id, "Tap to delete", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delnum|"))
def delnum(c):
    del NUMBERS[c.data.split("|")[1]]
    save(NUM_FILE, NUMBERS)
    bot.edit_message_text("✅ Deleted", c.message.chat.id, c.message.message_id)

# ================= CHANNELS =================
@bot.message_handler(func=lambda m: m.text=="➕ Add Channel")
def add_ch(m):
    STATE[m.chat.id] = {}
    bot.send_message(m.chat.id, "Send Channel Name")

@bot.message_handler(func=lambda m: isinstance(STATE.get(m.chat.id), dict) and "name" not in STATE[m.chat.id])
def ch_name(m):
    STATE[m.chat.id]["name"] = m.text
    bot.send_message(m.chat.id, "Send Channel Link")

@bot.message_handler(func=lambda m: isinstance(STATE.get(m.chat.id), dict) and "name" in STATE[m.chat.id])
def ch_link(m):
    CHANNELS.append({
        "name": STATE[m.chat.id]["name"],
        "link": m.text,
        "id": m.text.replace("https://t.me/", "@")
    })
    save(CH_FILE, CHANNELS)
    bot.send_message(m.chat.id, "✅ Channel added")
    STATE.pop(m.chat.id)

@bot.message_handler(func=lambda m: m.text=="📢 Channels")
def list_ch(m):
    kb = types.InlineKeyboardMarkup()
    for i,c in enumerate(CHANNELS):
        kb.add(types.InlineKeyboardButton(c["name"]+" ❌", callback_data=f"delch|{i}"))
    bot.send_message(m.chat.id, "Channels", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delch|"))
def delch(c):
    CHANNELS.pop(int(c.data.split("|")[1]))
    save(CH_FILE, CHANNELS)
    bot.edit_message_text("Deleted", c.message.chat.id, c.message.message_id)

# ================= SMS WORKER =================
def sms_worker():
    seen = set()
    while True:
        for api in SMS_APIS:
            try:
                r = requests.get(api, timeout=10).json()
                for row in r.get("aaData", []):
                    msg = row[4]
                    num = row[2]
                    otp = extract_otp(msg)
                    if not otp: continue

                    key = num + otp
                    if key in seen: continue
                    seen.add(key)

                    bot.send_message(
                        OTP_GROUP_ID,
                        f"📩 <b>New OTP</b>\n📞 {num}\n🔑 <code>{otp}</code>",
                        parse_mode="HTML"
                    )

                    for uid,v in OTP_DATA["user_current"].items():
                        if v["number"] == num:
                            OTP_DATA["user_otps"].setdefault(uid, []).append({
                                "number": num,
                                "otp": otp,
                                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            save(OTP_FILE, OTP_DATA)

                            bot.send_message(
                                int(uid),
                                f"🔐 <b>Your OTP</b>\n📞 {num}\n🔑 <code>{otp}</code>",
                                parse_mode="HTML"
                            )
            except:
                pass
        time.sleep(5)

# ================= RUN =================
threading.Thread(target=sms_worker, daemon=True).start()
print("🤖 BOT RUNNING")
bot.infinity_polling()
