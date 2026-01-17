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
# ⚙️ CONFIGURATION
# =========================================================
BOT_TOKEN = "8495469799:AAEeO1X4uIgVBBH1A-NQTOLbVOoLjOB0Z1A"
TARGET_GROUP_ID = "-1003361941052"

# IVAS Portal Details
LOGIN_URL = "http://ivas.tempnum.qzz.io/login"
PAGE_URL = "http://ivas.tempnum.qzz.io/portal/sms/received"

ACCOUNTS = {
    "Sami": {"email": "samiullahjappa90@gmail.com", "password": "Samiullah923"},
    "Jafar": {"email": "jafaralijappa020@gmail.com", "password": "Jafar5020"}
}

RAILWAY_SERVICES = ["IRCTC", "RAIL", "UTS", "IXIGO", "CONFIRM", "TRAIN", "PNT"]

class RailwayEngine:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.current_user = None

    def login(self, email, password):
        try:
            print(f"🔐 Logging in for {email}...")
            # Step 1: Get CSRF Token
            res = self.scraper.get(LOGIN_URL)
            soup = BeautifulSoup(res.text, 'html.parser')
            token = soup.find('input', {'name': '_token'})['value']
            
            # Step 2: Post Credentials
            payload = {"_token": token, "email": email, "password": password}
            res = self.scraper.post(LOGIN_URL, data=payload)
            
            if "logout" in res.text.lower() or res.status_code in [200, 302]:
                self.current_user = email
                print(f"✅ Login Successful: {email}")
                return True
            return False
        except Exception as e:
            print(f"❌ Login Error: {e}")
            return False

    async def fetch_sms(self, app):
        conn = sqlite3.connect("railway_bot.db", check_same_thread=False)
        conn.execute("CREATE TABLE IF NOT EXISTS history(otp TEXT, num TEXT)")
        
        while True:
            for name, creds in ACCOUNTS.items():
                if self.current_user != creds['email']:
                    self.login(creds['email'], creds['password'])

                try:
                    resp = self.scraper.get(PAGE_URL)
                    if "login" in resp.url: # Session expired
                        self.login(creds['email'], creds['password'])
                        resp = self.scraper.get(PAGE_URL)

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
                                    
                                    # Send Telegram Notification
                                    text = (f"🚆 *RAILWAY OTP RECEIVED* 🎫\n\n"
                                            f"📱 *Number:* `{num}`\n"
                                            f"🔑 *OTP Code:* `{otp}`\n\n"
                                            f"💬 *Message:* _{msg}_")
                                    
                                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Channel", url="https://t.me/SigmaSamiOffical")],
                                                              [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Samiorbit")]])
                                    
                                    await app.bot.send_message(TARGET_GROUP_ID, text, parse_mode="Markdown", reply_markup=kb)
                except Exception as e:
                    print(f"Error fetching data: {e}")
            await asyncio.sleep(5)

async def main():
    engine = RailwayEngine()
    application = Application.builder().token(BOT_TOKEN).build()
    
    async with application:
        await application.initialize()
        await application.start()
        await engine.fetch_sms(application)

if __name__ == "__main__":
    asyncio.run(main())
