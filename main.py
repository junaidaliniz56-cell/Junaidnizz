import telebot
import time
import random
import string
import json
import requests

BOT_TOKEN = "8569662345:AAGdjpXHCKq8lYDc9DVQplDRk5bRosN7nwg"
ADMIN_IDS = [7011937754]   # 👈 MASTER ADMIN ID

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
DATA_FILE = "master_data.json"

# ---------------- DATA ----------------
def load():
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except:
        return {
            "channels": [],
            "redeems": {},
            "used_users": [],
            "connected_bots": {}
        }

def save(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

data = load()

# ---------------- UTILS ----------------
def is_admin(uid):
    return uid in ADMIN_IDS

def gen_code():
    return ''.join(random.choices(string.ascii_uppercase, k=7))

# ---------------- START ----------------
@bot.message_handler(commands=["start"])
def start(m):
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔗 Contact Bot OTP", "🎟 Redeem Code")
    kb.add("ℹ️ About")
    bot.send_message(
        m.chat.id,
        "🤖 <b>OTP CONTROL SYSTEM</b>\n\nChoose option:",
        reply_markup=kb
    )

# ---------------- ABOUT ----------------
@bot.message_handler(func=lambda m: m.text == "ℹ️ About")
def about(m):
    bot.send_message(
        m.chat.id,
        "This system lets you create & control OTP bots.\n\n"
        "• Redeem based access\n"
        "• Admin controlled\n"
        "• Secure\n\nPowered by You ❤️"
    )

# ---------------- REDEEM ----------------
@bot.message_handler(func=lambda m: m.text == "🎟 Redeem Code")
def redeem(m):
    bot.send_message(m.chat.id, "Send your redeem code:")
    bot.register_next_step_handler(m, apply_redeem)

def apply_redeem(m):
    code = m.text.strip().upper()
    uid = m.from_user.id

    if code not in data["redeems"]:
        bot.send_message(uid, "❌ Invalid code")
        return

    if uid in data["used_users"]:
        bot.send_message(uid, "❌ You already used a code")
        return

    if time.time() > data["redeems"][code]:
        bot.send_message(uid, "❌ Code expired")
        return

    data["used_users"].append(uid)
    save(data)
    bot.send_message(uid, "✅ Redeem successful!\nNow use <b>Contact Bot OTP</b>")

# ---------------- CONTACT BOT OTP ----------------
@bot.message_handler(func=lambda m: m.text == "🔗 Contact Bot OTP")
def contact(m):
    uid = m.from_user.id
    if uid not in data["used_users"]:
        bot.send_message(uid, "❌ Redeem required first")
        return

    bot.send_message(
        uid,
        "🤖 <b>Send your OTP BOT TOKEN</b>\n\n"
        "After verification you can use /admin in your bot"
    )
    bot.register_next_step_handler(m, receive_token)

def receive_token(m):
    token = m.text.strip()
    uid = m.from_user.id

    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if not r.json().get("ok"):
            raise Exception("Invalid token")
    except:
        bot.send_message(uid, "❌ Invalid BOT TOKEN")
        return

    data["connected_bots"][str(uid)] = token
    save(data)

    bot.send_message(
        uid,
        "✅ <b>Bot connected successfully</b>\n\n"
        "Now open your bot and send:\n"
        "<code>/admin</code>"
    )

# ---------------- ADMIN PANEL ----------------
@bot.message_handler(commands=["admin"])
def admin(m):
    if not is_admin(m.from_user.id):
        return

    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎟 Create Redeem")
    bot.send_message(m.chat.id, "⚙️ <b>MASTER ADMIN PANEL</b>", reply_markup=kb)

# ---------------- CREATE REDEEM ----------------
@bot.message_handler(func=lambda m: m.text == "🎟 Create Redeem")
def create_r(m):
    if not is_admin(m.from_user.id): return
    bot.send_message(m.chat.id, "Send type: daily / weekly / monthly")
    bot.register_next_step_handler(m, gen_r)

def gen_r(m):
    t = m.text.lower()
    dur = {"daily":86400,"weekly":604800,"monthly":2592000}
    if t not in dur:
        bot.send_message(m.chat.id, "❌ Invalid type")
        return

    code = gen_code()
    data["redeems"][code] = time.time() + dur[t]
    save(data)
    bot.send_message(m.chat.id, f"🎟 Redeem Code:\n<code>{code}</code>")

bot.infinity_polling()
