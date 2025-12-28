import telebot
import requests
import json
import os
import re
import threading
import time
from telebot import types

# ================= CONFIG =================
BOT_TOKEN = "8546188939:AAGCchjT0fnBRmgeKVz87S1i7cIkhVOfZHI"
ADMINS = [7011937754]

DATA_FILE = "data.json"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ================= STORAGE =================
def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {
        "numbers": {},          # country: [numbers]
        "channels": [],         # join check
        "otp_groups": [],       # otp post groups
        "sms_apis": [],         # sms api urls
        "user_otps": {}         # uid: [otp history]
    }

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load()
STATE = {}

def is_admin(uid): 
    return uid in ADMINS

# ================= JOIN CHECK =================
def check_join(uid):
    for ch in data["channels"]:
        try:
            m = bot.get_chat_member(ch["id"], uid)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ================= OTP UTILS =================
def extract_otp(text):
    m = re.search(r"\b\d{4,6}\b", text)
    return m.group(0) if m else "N/A"

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    if not check_join(m.chat.id):
        kb = types.InlineKeyboardMarkup()
        for ch in data["channels"]:
            kb.add(types.InlineKeyboardButton(
                f"Join {ch['name']}", url=ch["link"]
            ))
        kb.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
        bot.send_message(m.chat.id, "❌ Join required channels", reply_markup=kb)
        return
    show_countries(m.chat.id)

@bot.callback_query_handler(func=lambda c: c.data=="verify")
def verify(c):
    if check_join(c.from_user.id):
        show_countries(c.from_user.id)
    else:
        bot.answer_callback_query(c.id, "❌ Join all channels", show_alert=True)

# ================= USER PANEL =================
def show_countries(uid):
    if not data["numbers"]:
        bot.send_message(uid, "❌ No numbers available")
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    for c in data["numbers"]:
        kb.add(types.InlineKeyboardButton(
            f"{country_flag(c)} {c} ({len(data['numbers'][c])})",
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
    save()

    data["user_otps"].setdefault(str(c.from_user.id), [])
    save()

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔄 Change Number", callback_data=f"country|{country}"))
    kb.add(types.InlineKeyboardButton("🌍 Change Country", callback_data="back"))
    if data["otp_groups"]:
        kb.add(types.InlineKeyboardButton("📢 OTP Group", url=data["otp_groups"][0]["link"]))
    kb.add(types.InlineKeyboardButton("📜 View Past OTPs", callback_data="past"))

    bot.edit_message_text(
        f"<b>📞 Your Number</b>\n\n<code>{num}</code>"
        c.message.chat.id,
        c.message.message_id,
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda c: c.data=="back")
def back(c):
    show_countries(c.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data=="past")
def past(c):
    otps = data["user_otps"].get(str(c.from_user.id), [])
    txt = "\n".join(otps[-10:]) or "No OTPs yet"
    bot.answer_callback_query(c.id)
    bot.send_message(c.from_user.id, f"<b>📜 Past OTPs</b>\n\n{txt}")

# ================= ADMIN PANEL =================
@bot.message_handler(commands=["admin"])
def admin(m):
    if not is_admin(m.chat.id): return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Add Numbers","📋 Number List")
    kb.add("➕ Add Channel","📢 Channels")
    kb.add("➕ Add SMS API","🔌 SMS APIs")
    kb.add("➕ Add OTP Group","📢 OTP Groups")
    kb.add("❌ Close")
    bot.send_message(m.chat.id,"🛠 Admin Panel",reply_markup=kb)

# ---------- ADD NUMBERS ----------
@bot.message_handler(func=lambda m: m.text=="➕ Add Numbers")
def add_numbers(m):
    STATE[m.chat.id]="country"
    bot.send_message(m.chat.id,"🌍 Send Country Name")

@bot.message_handler(func=lambda m: STATE.get(m.chat.id)=="country")
def get_country(m):
    STATE[m.chat.id]={"country":m.text}
    bot.send_message(m.chat.id,"📄 Send number.txt")

@bot.message_handler(content_types=["document"])
def recv_file(m):
    st=STATE.get(m.chat.id)
    if not st or "country" not in st: return
    file=bot.download_file(bot.get_file(m.document.file_id).file_path)
    nums=file.decode().splitlines()
    c=st["country"]
    data["numbers"].setdefault(c,[]).extend(nums)
    save()
    STATE.pop(m.chat.id)
    bot.send_message(m.chat.id,f"✅ {len(nums)} numbers added")

# ---------- NUMBER LIST ----------
@bot.message_handler(func=lambda m: m.text=="📋 Number List")
def num_list(m):
    kb=types.InlineKeyboardMarkup()
    for c in data["numbers"]:
        kb.add(types.InlineKeyboardButton(
            f"{c} ❌",callback_data=f"delnum|{c}"
        ))
    bot.send_message(m.chat.id,"Tap to delete country",reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delnum|"))
def delnum(c):
    del data["numbers"][c.data.split("|")[1]]
    save()
    bot.edit_message_text("Deleted",c.message.chat.id,c.message.message_id)

# ---------- CHANNEL ----------
@bot.message_handler(func=lambda m: m.text=="➕ Add Channel")
def add_ch(m):
    STATE[m.chat.id]={}
    bot.send_message(m.chat.id,"Channel Name")

@bot.message_handler(func=lambda m: isinstance(STATE.get(m.chat.id),dict) and "name" not in STATE[m.chat.id])
def ch_name(m):
    STATE[m.chat.id]["name"]=m.text
    bot.send_message(m.chat.id,"Channel Link")

@bot.message_handler(func=lambda m: isinstance(STATE.get(m.chat.id),dict) and "name" in STATE[m.chat.id])
def ch_link(m):
    ch=STATE[m.chat.id]
    data["channels"].append({
        "name":ch["name"],
        "link":m.text,
        "id":m.text.replace("https://t.me/","@")
    })
    save()
    STATE.pop(m.chat.id)
    bot.send_message(m.chat.id,"✅ Channel added")

@bot.message_handler(func=lambda m: m.text=="📢 Channels")
def ch_list(m):
    txt="\n".join([c["name"] for c in data["channels"]]) or "No channels"
    bot.send_message(m.chat.id,txt)

# ---------- SMS API ----------
@bot.message_handler(func=lambda m: m.text=="➕ Add SMS API")
def add_api(m):
    bot.send_message(m.chat.id,"Send SMS API URL")
    STATE[m.chat.id]="api"

@bot.message_handler(func=lambda m: STATE.get(m.chat.id)=="api")
def save_api(m):
    data["sms_apis"].append(m.text)
    save()
    STATE.pop(m.chat.id)
    bot.send_message(m.chat.id,"✅ API added")

@bot.message_handler(func=lambda m: m.text=="🔌 SMS APIs")
def list_api(m):
    txt="\n".join(data["sms_apis"]) or "No APIs"
    bot.send_message(m.chat.id,txt)

# ---------- OTP GROUP ----------
@bot.message_handler(func=lambda m: m.text=="➕ Add OTP Group")
def add_otp_group(m):
    STATE[m.chat.id]="otpgrp"
    bot.send_message(m.chat.id,"Send OTP Group Link")

@bot.message_handler(func=lambda m: STATE.get(m.chat.id)=="otpgrp")
def save_otp_group(m):
    data["otp_groups"].append({"link":m.text})
    save()
    STATE.pop(m.chat.id)
    bot.send_message(m.chat.id,"✅ OTP Group added")

@bot.message_handler(func=lambda m: m.text=="📢 OTP Groups")
def list_otp_groups(m):
    txt="\n".join([g["link"] for g in data["otp_groups"]]) or "No OTP groups"
    bot.send_message(m.chat.id,txt)

@bot.message_handler(func=lambda m: m.text=="❌ Close")
def close(m):
    bot.send_message(m.chat.id,"Closed",reply_markup=types.ReplyKeyboardRemove())

# ================= SMS WORKER =================
def sms_worker(api):
    last=None
    while True:
        try:
            r=requests.get(api,timeout=10).json()
            rows=r.get("aaData",[])
            if not rows: 
                time.sleep(3); continue
            row=rows[0]
            msg=row[-1]
            num=row[2]
            otp=extract_otp(msg)
            key=num+otp
            if key==last: 
                time.sleep(3); continue
            last=key

            text=f"<b>📩 New OTP</b>\n\n📞 <code>{num}</code>\n🔑 <code>{otp}</code>\n\n<pre>{msg}</pre>"

            for g in data["otp_groups"]:
                try:
                    bot.send_message(g["link"],text)
                except: pass

            for u in data["user_otps"]:
                data["user_otps"][u].append(f"{num} → {otp}")
                data["user_otps"][u]=data["user_otps"][u][-10:]
            save()

        except: pass
        time.sleep(3)

for api in data["sms_apis"]:
    threading.Thread(target=sms_worker,args=(api,),daemon=True).start()

print("🤖 Bot Running")
bot.infinity_polling()
