import asyncio
import os
import cloudscraper
import re
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

# CONFIGURATION
BOT_TOKEN = "8495469799:AAEeO1X4uIgVBBH1A-NQTOLbVOoLjOB0Z1A"
TARGET_GROUP_ID = "-1003361941052"
RAILWAY_SERVICES = ["IRCTC", "RAIL", "UTS", "IXIGO", "CONFIRM", "TRAIN", "PNT"]

async def fetch_and_monitor(app):
    conn = sqlite3.connect("railway_bot.db", check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS history(otp TEXT, num TEXT)")
    scraper = cloudscraper.create_scraper()
    print("🚀 Monitoring Started Successfully...")
    
    while True:
        try:
            resp = scraper.get("http://ivas.tempnum.qzz.io/portal/sms/received")
            # Yahan html.parser use kiya hai taaki lxml ki zarurat na pade
            soup = BeautifulSoup(resp.text, 'html.parser')
            rows = soup.select("table tbody tr")
            
            for row in rows[:10]:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    num, msg = cols[0].text.strip(), cols[1].text.strip()
                    otp_match = re.search(r"\b\d{4,6}\b", msg)
                    
                    if otp_match and any(k in msg.upper() for k in RAILWAY_SERVICES):
                        otp = otp_match.group(0)
                        cur = conn.cursor()
                        if not cur.execute("SELECT 1 FROM history WHERE otp=? AND num=?", (otp, num)).fetchone():
                            cur.execute("INSERT INTO history VALUES (?,?)", (otp, num))
                            conn.commit()
                            
                            text = (f"🚆 *RAILWAY OTP RECEIVED* 🎫\n\n"
                                    f"📱 *Number:* `{num}`\n"
                                    f"🔑 *OTP Code:* `{otp}`\n\n"
                                    f"💬 *Message:* _{msg}_")
                            
                            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Channel", url="https://t.me/SigmaSamiOffical")]])
                            await app.bot.send_message(TARGET_GROUP_ID, text, parse_mode="Markdown", reply_markup=kb)
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(5)

async def main():
    # Railway compatibility ke liye Application use karein Updater nahi
    application = Application.builder().token(BOT_TOKEN).build()
    async with application:
        await application.initialize()
        await application.start()
        await fetch_and_monitor(application)

if __name__ == "__main__":
    asyncio.run(main())
