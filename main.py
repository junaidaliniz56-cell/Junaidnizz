import asyncio
import os
import cloudscraper
import re
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

# =========================================================
# ⚙️ CONFIGURATION (UPDATED)
# =========================================================
BOT_TOKEN = "8495469799:AAEeO1X4uIgVBBH1A-NQTOLbVOoLjOB0Z1A"
TARGET_GROUP_ID = "-1003361941052"

# Links
CHANNEL_URL = "https://t.me/SigmaSamiOffical"
DEV_URL = "https://t.me/Samiorbit"

ACCOUNTS = {
    "Sami": {"email": "ahtishamwrites67@gmail.com", "Ahtisham786.": "Samiullah923"},
    "Jafar": {"email": "jafaralijappa020@gmail.com", "password": "Jafar5020"}
}

RAILWAY_SERVICES = ["IRCTC", "RAIL", "UTS", "IXIGO", "CONFIRM", "TRAIN", "PNT"]
POLL_INTERVAL = 5 

# =========================================================
# 🚆 MONITORING LOGIC
# =========================================================

async def fetch_and_monitor(app: Application):
    conn = sqlite3.connect("railway_bot.db", check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS history(otp TEXT, num TEXT)")
    
    scraper = cloudscraper.create_scraper()
    print("🚆 Railway Monitor is LIVE and Scanning...")

    while True:
        for name, creds in ACCOUNTS.items():
            try:
                resp = scraper.get("http://ivas.tempnum.qzz.io/portal/sms/received")
                soup = BeautifulSoup(resp.text, 'html.parser')
                rows = soup.select("table tbody tr")
                
                for row in rows[:10]:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        num = cols[0].get_text(strip=True)
                        msg = cols[1].get_text(strip=True)
                        
                        otp_match = re.search(r"\b\d{4,6}\b", msg)
                        
                        if otp_match and any(k in msg.upper() for k in RAILWAY_SERVICES):
                            otp = otp_match.group(0)
                            
                            cur = conn.cursor()
                            if not cur.execute("SELECT 1 FROM history WHERE otp=? AND num=?", (otp, num)).fetchone():
                                cur.execute("INSERT INTO history VALUES (?,?)", (otp, num))
                                conn.commit()
                                
                                text = (
                                    f"🚆 *RAILWAY OTP RECEIVED* 🎫\n"
                                    f"━━━━━━━━━━━━━━━━━━━━\n"
                                    f"📱 *Number:* `{num}`\n"
                                    f"🔑 *OTP Code:* `{otp}`\n\n"
                                    f"💬 *Message:* _{msg}_\n"
                                    f"━━━━━━━━━━━━━━━━━━━━\n"
                                    f"⏰ *Time:* {datetime.now().strftime('%I:%M:%S %p')}"
                                )
                                
                                kb = InlineKeyboardMarkup([
                                    [InlineKeyboardButton("📢 Channel", url=CHANNEL_URL)],
                                    [InlineKeyboardButton("👨‍💻 Developer", url=DEV_URL)]
                                ])

                                await app.bot.send_message(TARGET_GROUP_ID, text, parse_mode="Markdown", reply_markup=kb)
                                print(f"✅ Sent Railway OTP: {otp}")

            except Exception as e:
                print(f"Fetch Error: {e}")
        
        await asyncio.sleep(POLL_INTERVAL)

async def main():
    # Application build
    application = Application.builder().token(BOT_TOKEN).build()
    
    async with application:
        await application.initialize()
        await application.start()
        # Background loop shuru karein
        await fetch_and_monitor(application)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
