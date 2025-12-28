import telebot
import time
import random
import string

BOT_TOKEN = "8569662345:AAGdjpXHCKq8lYDc9DVQplDRk5bRosN7nwg"
ADMIN_IDS = [7011937754]  # 👈 apni Telegram ID

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ================= STORAGE (MEMORY BASED) =================
CHANNELS = []
REDEEMS = {}     # code: expiry_time
USED_USERS = set()
CONNECTED_BOTS = {}

# ================= UTILS =================
def is_admin(uid):
    return uid in ADMIN_IDS

def gen_code():
    return ''.join(random.choices(string.ascii_uppercase, k=7))

# ================= START =================
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

# ================= ABOUT =================
@bot.message_handler(func=lambda m: m.text == "ℹ️ About")
def about(m):
    bot.send_message(
        m.chat.id,
        "🔐 Secure OTP Bot Controller\n\n"
        "• Redeem based access\n"
        "• Admin controlled\n"
        "• Railway compatible\n"
        "• One redeem = one user"
    )

# ================= REDEEM =================
@bot.message_handler(func=lambda m: m.text == "🎟 Redeem Code")
def redeem(m):
    bot.send_message(m.chat.id, "Send your redeem code:")
    bot.register_next_step_handler(m, apply_redeem)

def apply_redeem(m):
    code = m.text.strip().upper()
    uid = m.from_user.id

    if code not in REDEEMS:
        bot.send_message(uid, "❌ Invalid code")
        return

    if uid in USED_USERS:
        bot.send_message(uid, "❌ You already used a redeem")
        return

    if time.time() > REDEEMS[code]:
        bot.send_message(uid, "❌ Redeem expired")
        return

    USED_USERS.add(uid)
    bot.send_message(uid, "✅ Redeem successful! Now you can connect your bot.")

# ================= CONTACT BOT OTP =================
@bot.message_handler(func=lambda m: m.text == "🔗 Contact Bot OTP")
def contact(m):
    uid = m.from_user.id
    if uid not in USED_USERS:
        bot.send_message(uid, "❌ Redeem required before connecting bot.")
        return

    bot.send_message(
        uid,
        "🤖 <b>Send your BOT TOKEN</b>\n\n"
        "After verify, open your bot and send:\n"
        "<code>/admin</code>"
    )
    bot.register_next_step_handler(m, receive_token)

def receive_token(m):
    token = m.text.strip()
    uid = m.from_user.id
    CONNECTED_BOTS[uid] = token

    bot.send_message(
        uid,
        "✅ <b>Bot connected successfully</b>\n\n"
        "Now go to your bot and type:\n"
        "<code>/admin</code>"
    )

# ================= ADMIN PANEL =================
@bot.message_handler(commands=["admin"])
def admin(m):
    if not is_admin(m.from_user.id):
        return

    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎟 Create Redeem", "📢 Add Channel")
    kb.add("📋 List Channels")
    bot.send_message(m.chat.id, "⚙️ <b>MASTER ADMIN PANEL</b>", reply_markup=kb)

# ================= CREATE REDEEM =================
@bot.message_handler(func=lambda m: m.text == "🎟 Create Redeem")
def create_redeem(m):
    if not is_admin(m.from_user.id): return
    bot.send_message(m.chat.id, "Send type: daily / weekly / monthly")
    bot.register_next_step_handler(m, gen_redeem)

def gen_redeem(m):
    t = m.text.lower()
    durations = {
        "daily": 86400,
        "weekly": 604800,
        "monthly": 2592000
    }

    if t not in durations:
        bot.send_message(m.chat.id, "❌ Invalid type")
        return

    code = gen_code()
    REDEEMS[code] = time.time() + durations[t]

    bot.send_message(
        m.chat.id,
        f"🎟 <b>Redeem Created</b>\n\nCode: <code>{code}</code>\nType: {t}"
    )

# ================= CHANNEL =================
@bot.message_handler(func=lambda m: m.text == "📢 Add Channel")
def add_channel(m):
    if not is_admin(m.from_user.id): return
    bot.send_message(m.chat.id, "Send channel ID:")
    bot.register_next_step_handler(m, save_channel)

def save_channel(m):
    cid = m.text.strip()
    if cid not in CHANNELS:
        CHANNELS.append(cid)
    bot.send_message(m.chat.id, "✅ Channel added")

@bot.message_handler(func=lambda m: m.text == "📋 List Channels")
def list_channels(m):
    if not is_admin(m.from_user.id): return
    text = "\n".join(CHANNELS) if CHANNELS else "No channels added"
    bot.send_message(m.chat.id, text)

# ================= RUN =================
bot.infinity_polling()
