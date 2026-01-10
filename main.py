import json
import re
import time
import requests
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# ======================
# CONFIG
# ======================

BOT_TOKEN = "8433897615:AAHE2px-1g5KvJTyMuGfdJoi_XfHx03Lcmw"
CR_API = "http://147.135.212.197/crapi/st/viewstats"
CR_TOKEN = "RVdWRElBUzRGcW9WeneNcmd2cGV9ZJd8e29PVlyPcFxeamxSgWVXfw=="

GROUP_IDS = [
    -1003361941052,  # apna group id
]

OTP_FILE = "otp_store.json"

# ======================
# UTILS
# ======================

def load_store():
    try:
        with open(OTP_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_store(data):
    with open(OTP_FILE, "w") as f:
        json.dump(data, f)

def extract_otp(text):
    m = re.search(r"\b(\d{4,8})\b", text)
    return m.group(1) if m else None

# ======================
# COMMANDS
# ======================

def start(update: Update, context: CallbackContext):
    update.message.reply_text("✅ CR Bot Running")

def otpfor(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Usage: /otpfor <number>")
        return

    number = context.args[0]
    store = load_store()

    if number in store:
        update.message.reply_text(
            f"🔐 OTP for {number}: {store[number]}"
        )
    else:
        update.message.reply_text("❌ No OTP found")

# ======================
# CR WORKER
# ======================

def cr_worker(bot: Bot):
    print("🚀 CR Worker Started")
    last = None

    while True:
        try:
            r = requests.get(
                CR_API,
                params={"token": CR_TOKEN},
                timeout=10
            )

            if r.status_code == 200:
                data = r.json()

                number = str(data.get("num") or data.get("number") or "")
                message = str(data.get("msg") or data.get("message") or "")

                if number and message:
                    uniq = number + message
                    if uniq != last:
                        last = uniq

                        otp = extract_otp(message)
                        if otp:
                            store = load_store()
                            store[number] = otp
                            save_store(store)

                        text = f"📞 {number}\n💬 {message}"
                        for gid in GROUP_IDS:
                            bot.send_message(gid, text)

                        print("Sent:", number)

        except Exception as e:
            print("CR ERROR:", e)

        time.sleep(3)

# ======================
# MAIN
# ======================

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("otpfor", otpfor))

    updater.start_polling()
    print("🤖 Bot Polling Started")

    cr_worker(updater.bot)

if __name__ == "__main__":
    main()
