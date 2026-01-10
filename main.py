import requests
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = "8433897615:AAHE2px-1g5KvJTyMuGfdJoi_XfHx03Lcmw"
GROUP_ID = -1003361941052   # 👈 yahan apna group ID lagao

API_URL = (
    "http://147.135.212.197/crapi/st/viewstats"
    "?token=RVdWRElBUzRGcW9WeneNcmd2cGV9ZJd8e29PVlyPcFxeamxSgWVXfw=="
    "&dt1=2026-01-10"
)

def fetch_cr():
    r = requests.get(API_URL, timeout=10)
    data = r.json()

    if isinstance(data, list) and data:
        data = data[0]

    number = str(data.get("num", ""))
    msg = str(data.get("msg", ""))
    dt = str(data.get("dt", ""))

    if not number.startswith("92"):
        return None

    return number, msg, dt


def cr(update, context):
    result = fetch_cr()
    if not result:
        return

    number, msg, dt = result

    text = (
        "📩 *CR OTP*\n\n"
        f"📱 `{number}`\n"
        f"🕒 `{dt}`\n\n"
        f"{msg}"
    )

    # 👇 DIRECT GROUP POST
    context.bot.send_message(
        chat_id=GROUP_ID,
        text=text,
        parse_mode="Markdown"
    )


def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("cr", cr))
    updater.start_polling()
    updater.idle()


main()
