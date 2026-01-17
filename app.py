import asyncio
import sqlite3
import re
import os
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

# =========================================================
# ⚙️ CONFIGURATION
# =========================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8495469799:AAEeO1X4uIgVBBH1A-NQTOLbVOoLjOB0Z1A")
TARGET_GROUP_ID = "-1003361941052"

# Links
CHANNEL_URL = "https://t.me/+c4VCxBCT3-QzZGFk"
DEV_URL = "https://t.me/junaidniz786"

ACCOUNTS = {
    "Sami": {"email": "ahtishamwrites67@gmail.com ", "password": "Ahtisham786."},
    "Jafar": {"email": "jafaralijappa020@gmail.com", "password": "Jafar5020"}
}

RAILWAY_SERVICES = ["IRCTC", "RAIL", "UTS", "IXIGO", "CONFIRM", "TRAIN", "PNT"]
POLL_INTERVAL = 4 
BASE_URL = "http://ivas.tempnum.qzz.io"
PAGE_URL = f"{BASE_URL}/portal/sms/received"

# =========================================================
# 🚆 MONITORING LOGIC
# =========================================================

async def bot_loop(app: Application):
    conn = sqlite3.connect("railway_bot.db", check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS history(otp TEXT, num TEXT)")
    
    scraper = cloudscraper.create_scraper()
    print("🚆 Railway Monitor is LIVE...")

    while True:
        for name, creds in ACCOUNTS.items():
            try:
                # Scraping Logic
                resp = scraper.get(PAGE_URL)
                soup = BeautifulSoup(resp.text, 'lxml')
                rows = soup.select("table tbody tr")
                
                for row in rows[:10]:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        num = cols[0].get_text(strip=True)
                        msg = cols[1].get_text(strip=True)
                        
                        otp_match = re.search(r"\b\d{4,6}\b", msg)
                        
                        # Railway Check
                        if otp_match and any(k in msg.upper() for k in RAILWAY_SERVICES):
                            otp = otp_match.group(0)
                            
                            cur = conn.cursor()
                            if not cur.execute("SELECT 1 FROM history WHERE otp=? AND num=?", (otp, num)).fetchone():
                                cur.execute("INSERT INTO history VALUES (?,?)", (otp, num))
                                conn.commit()
                                
                                # --- UI Elements ---
                                text = (
                                    f"🚆 *RAILWAY OTP RECEIVED* 🎫\n"
                                    f"━━━━━━━━━━━━━━━━━━━━\n"
                                    f"📱 *Number:* `{num}`\n"
                                    f"🔑 *OTP Code:* `{otp}`\n\n"
                                    f"💬 *Message:* _{msg}_\n"
                                    f"━━━━━━━━━━━━━━━━━━━━\n"
                                    f"⏰ *Time:* {datetime.now().strftime('%I:%M:%S %p')}"
                                )
                                
                                keyboard = InlineKeyboardMarkup([
                                    [InlineKeyboardButton("📢 Channel", url=CHANNEL_URL)],
                                    [InlineKeyboardButton("👨‍💻 Developer", url=DEV_URL)]
                                ])

                                await app.bot.send_message(
                                    chat_id=TARGET_GROUP_ID,
                                    text=text,
                                    parse_mode="Markdown",
                                    reply_markup=keyboard
                                )
                                print(f"✅ Sent: {otp} to Telegram")

            except Exception as e:
                print(f"Error fetching data: {e}")
        
        await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    application = Application.builder().token(BOT_TOKEN).build()
    
    loop = asyncio.get_event_loop()
    loop.create_task(bot_loop(application))
    application.run_polling()
