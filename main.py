import requests
from bs4 import BeautifulSoup
import time
import re
import sys
import signal
import sqlite3
import os
import threading
import hashlib
import queue
import random
from datetime import datetime, timedelta
# Import library Telegram untuk membuat tombol
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# --- Configuration ---
BOT_NAME = "Junaid Niz OTP"
USERNAME = "Junaidniz786"
PASSWORD = "Junaidniz786"
DB_FILE = "sms_database_np.db" 

# --- LINK BUTTON CONFIGURATION ---
# Ganti link di bawah ini sesuai keinginan
CHANNEL_LINK = "https://t.me/malikotpzone9"
OWNER_LINK = "https://t.me/Whatsappseller01"
BUTTON_TEXT1 = "Number Channel 🚀"
BUTTON_TEXT2 = "Owner 👑"

# --- Telegram Configuration ---
TELEGRAM_BOT_TOKEN = "8125227719:AAHIz2lrF7jMGea_qB_ccimMSRscvKarHj8"
DEFAULT_GROUP_CHAT_ID = "-1003361941052" 
DM_CHAT_ID = "7011937754" 

# --- API Endpoints ---
BASE_URL = "http://139.99.63.204/ints"
DOMAIN_URL = "http://139.99.63.204/ints"
LOGIN_PAGE_URL = f"{BASE_URL}/login"
SMS_HTML_PAGE_URL = f"{BASE_URL}/client/SMSCDRStats" 

POTENTIAL_API_URLS = [
    f"{BASE_URL}/client/res/data_smscdr.php",
    f"{DOMAIN_URL}/res/data_smscdr.php",
    f"{BASE_URL}/res/data_smscdr.php"
]
working_api_url = None 

# --- Global variables ---
db_connection = None
stop_event = threading.Event()
reported_sms_hashes_cache = set()

# --- Data for Formatting ---

COUNTRY_CODES = {
    '1': ('USA/Canada', '🇺🇸'), '7': ('Russia/Kazakhstan', '🇷🇺'), '20': ('Egypt', '🇪🇬'), '27': ('South Africa', '🇿🇦'),
    '30': ('Greece', '🇬🇷'), '31': ('Netherlands', '🇳🇱'), '32': ('Belgium', '🇧🇪'), '33': ('France', '🇫🇷'),
    '34': ('Spain', '🇪🇸'), '36': ('Hungary', '🇭🇺'), '39': ('Italy', '🇮🇹'), '40': ('Romania', '🇷🇴'),
    '41': ('Switzerland', '🇨🇭'), '43': ('Austria', '🇦🇹'), '44': ('United Kingdom', '🇬🇧'), '45': ('Denmark', '🇩🇰'),
    '46': ('Sweden', '🇸🇪'), '47': ('Norway', '🇳🇴'), '48': ('Poland', '🇵🇱'), '49': ('Germany', '🇩🇪'),
    '51': ('Peru', '🇵🇪'), '52': ('Mexico', '🇲🇽'), '53': ('Cuba', '🇨🇺'), '54': ('Argentina', '🇦🇷'),
    '55': ('Brazil', '🇧🇷'), '56': ('Chile', '🇨🇱'), '57': ('Colombia', '🇨🇴'), '58': ('Venezuela', '🇻🇪'),
    '60': ('Malaysia', '🇲🇾'), '61': ('Australia', '🇦🇺'), '62': ('Indonesia', '🇮🇩'), '63': ('Philippines', '🇵🇭'),
    '64': ('New Zealand', '🇳🇿'), '65': ('Singapore', '🇸🇬'), '66': ('Thailand', '🇹🇭'), '81': ('Japan', '🇯🇵'),
    '82': ('South Korea', '🇰🇷'), '84': ('Viet Nam', '🇻🇳'), '86': ('China', '🇨🇳'), '90': ('Turkey', '🇹🇷'),
    '91': ('India', '🇮🇳'), '92': ('Pakistan', '🇵🇰'), '93': ('Afghanistan', '🇦🇫'), '94': ('Sri Lanka', '🇱🇰'),
    '95': ('Myanmar', '🇲🇲'), '98': ('Iran', '🇮🇷'), '211': ('South Sudan', '🇸🇸'), '212': ('Morocco', '🇲🇦'),
    '213': ('Algeria', '🇩🇿'), '216': ('Tunisia', '🇹🇳'), '218': ('Libya', '🇱🇾'), '220': ('Gambia', '🇬🇲'),
    '221': ('Senegal', '🇸🇳'), '222': ('Mauritania', '🇲🇷'), '223': ('Mali', '🇲🇱'), '224': ('Guinea', '🇬🇳'),
    '225': ("Côte d'Ivoire", '🇨🇮'), '226': ('Burkina Faso', '🇧🇫'), '227': ('Niger', '🇳🇪'), '228': ('Togo', '🇹🇬'),
    '229': ('Benin', '🇧🇯'), '230': ('Mauritius', '🇲🇺'), '231': ('Liberia', '🇱🇷'), '232': ('Sierra Leone', '🇸🇱'),
    '233': ('Ghana', '🇬🇭'), '234': ('Nigeria', '🇳🇬'), '235': ('Chad', '🇹🇩'), '236': ('Central African Republic', '🇨🇫'),
    '237': ('Cameroon', '🇨🇲'), '238': ('Cape Verde', '🇨🇻'), '239': ('Sao Tome and Principe', '🇸🇹'),
    '240': ('Equatorial Guinea', '🇬🇶'), '241': ('Gabon', '🇬🇦'), '242': ('Congo', '🇨🇬'),
    '243': ('DR Congo', '🇨🇩'), '244': ('Angola', '🇦🇴'), '245': ('Guinea-Bissau', '🇬🇼'), '248': ('Seychelles', '🇸🇨'),
    '249': ('Sudan', '🇸🇩'), '250': ('Rwanda', '🇷🇼'), '251': ('Ethiopia', '🇪🇹'), '252': ('Somalia', '🇸🇴'),
    '253': ('Djibouti', '🇩🇯'), '254': ('Kenya', '🇰🇪'), '255': ('Tanzania', '🇹🇿'), '256': ('Uganda', '🇺🇬'),
    '257': ('Burundi', '🇧🇮'), '258': ('Mozambique', '🇲🇿'), '260': ('Zambia', '🇿🇲'), '261': ('Madagascar', '🇲🇬'),
    '263': ('Zimbabwe', '🇿🇼'), '264': ('Namibia', '🇳🇦'), '265': ('Malawi', '🇲🇼'), '266': ('Lesotho', '🇱🇸'),
    '267': ('Botswana', '🇧🇼'), '268': ('Eswatini', '🇸🇿'), '269': ('Comoros', '🇰🇲'), '290': ('Saint Helena', '🇸🇭'),
    '291': ('Eritrea', '🇪🇷'), '297': ('Aruba', '🇦🇼'), '298': ('Faroe Islands', '🇫🇴'), '299': ('Greenland', '🇬🇱'),
    '350': ('Gibraltar', '🇬🇮'), '351': ('Portugal', '🇵🇹'), '352': ('Luxembourg', '🇱🇺'), '353': ('Ireland', '🇮🇪'),
    '354': ('Iceland', '🇮🇸'), '355': ('Albania', '🇦🇱'), '356': ('Malta', '🇲🇹'), '357': ('Cyprus', '🇨🇾'),
    '358': ('Finland', '🇫🇮'), '359': ('Bulgaria', '🇧🇬'), '370': ('Lithuania', '🇱🇹'), '371': ('Latvia', '🇱🇻'),
    '372': ('Estonia', '🇪🇪'), '373': ('Moldova', '🇲🇩'), '374': ('Armenia', '🇦🇲'), '375': ('Belarus', '🇧🇾'),
    '376': ('Andorra', '🇦🇩'), '377': ('Monaco', '🇲🇨'), '378': ('San Marino', '🇸🇲'), '380': ('Ukraine', '🇺🇦'),
    '381': ('Serbia', '🇷🇸'), '382': ('Montenegro', '🇲🇪'), '385': ('Croatia', '🇭🇷'), '386': ('Slovenia', '🇸🇮'),
    '387': ('Bosnia and Herzegovina', '🇧🇦'), '389': ('North Macedonia', '🇲🇰'), '420': ('Czech Republic', '🇨🇿'),
    '421': ('Slovakia', '🇸🇰'), '423': ('Liechtenstein', '🇱🇮'), '501': ('Belize', '🇧🇿'), '502': ('Guatemala', '🇬🇹'),
    '503': ('El Salvador', '🇸🇻'), '504': ('Honduras', '🇭🇳'), '505': ('Nicaragua', '🇳🇮'), '506': ('Costa Rica', '🇨🇷'),
    '507': ('Panama', '🇵🇦'), '509': ('Haiti', '🇭🇹'), '590': ('Guadeloupe', '🇬🇵'), '591': ('Bolivia', '🇧🇴'),
    '592': ('Guyana', '🇬🇾'), '593': ('Ecuador', '🇪🇨'), '595': ('Paraguay', '🇵🇾'), '597': ('Suriname', '🇸🇷'),
    '598': ('Uruguay', '🇺🇾'), '673': ('Brunei', '🇧🇳'), '675': ('Papua New Guinea', '🇵🇬'), '676': ('Tonga', '🇹🇴'),
    '677': ('Solomon Islands', '🇸🇧'), '678': ('Vanuatu', '🇻🇺'), '679': ('Fiji', '🇫🇯'), '685': ('Samoa', '🇼🇸'),
    '689': ('French Polynesia', '🇵🇫'), '852': ('Hong Kong', '🇭🇰'), '853': ('Macau', '🇲🇴'), '855': ('Cambodia', '🇰🇭'),
    '856': ('Laos', '🇱🇦'), '880': ('Bangladesh', '🇧🇩'), '886': ('Taiwan', '🇹🇼'), '960': ('Maldives', '🇲🇻'),
    '961': ('Lebanon', '🇱🇧'), '962': ('Jordan', '🇯🇴'), '963': ('Syria', '🇸🇾'), '964': ('Iraq', '🇮🇶'),
    '965': ('Kuwait', '🇰🇼'), '966': ('Saudi Arabia', '🇸🇦'), '967': ('Yemen', '🇾🇪'), '968': ('Oman', '🇴🇲'),
    '970': ('Palestine', '🇵🇸'), '971': ('United Arab Emirates', '🇦🇪'), '972': ('Israel', '🇮🇱'),
    '973': ('Bahrain', '🇧🇭'), '974': ('Qatar', '🇶🇦'), '975': ('Bhutan', '🇧🇹'), '976': ('Mongolia', '🇲🇳'),
    '977': ('Nepal', '🇳🇵'), '992': ('Tajikistan', '🇹🇯'), '993': ('Turkmenistan', '🇹🇲'), '994': ('Azerbaijan', '🇦🇿'),
    '995': ('Georgia', '🇬🇪'), '996': ('Kyrgyzstan', '🇰🇬'), '998': ('Uzbekistan', '🇺🇿'),
}

# (Ditambahkan karena kode asli kekurangan variabel ini tapi menggunakannya)
QURANIC_VERSES = [
    ("Verse Text Placeholder", "Surah Info Placeholder"),
]

def get_country_info(phone_number):
    for i in range(4, 0, -1):
        prefix = phone_number[:i]
        if prefix in COUNTRY_CODES: return COUNTRY_CODES[prefix]
    return ('Unknown', '❓')

def detect_service(sender_name, message_text):
    full_text = (sender_name + " " + message_text).lower()
    services = ['whatsapp', 'facebook', 'google', 'telegram', 'instagram', 'discord', 'twitter', 'snapchat', 'imo', 'tiktok']
    for service in services:
        if service in full_text: return service.capitalize()
    return sender_name if sender_name else "Unknown"

# MODIFIED: Mengembalikan teks pesan DAN markup keyboard
def format_telegram_message(recipient_number, sender_name, message, otp, sms_time):
    country_name, country_flag = get_country_info(recipient_number)
    service_name = detect_service(sender_name, message)
    verse, surah_info = random.choice(QURANIC_VERSES)

    message_text = f"""✅ {country_flag} *{country_name} {service_name} OTP Code Received!🔥*
━━━━━━━━━━━━━━━━━━━━
📱 *Number:* `{recipient_number}`
🌍 *Country:* {country_flag} {country_name}
⚙️ *Service:* {service_name}
🔒 *OTP Code:* `{otp}`
⏳ *Time:* `{sms_time}`
━━━━━━━━━━━━━━━━━━━━
*Message:*
```{message}```
━━━━━━━━━━━━━━━━━━━━
```Note
🔑 Wait for the next OTP!
— don't wory!```
*BOT BY  @junaidniz786*"""

    # Buat Inline Keyboard (Tombol URL)
    keyboard = [
        [InlineKeyboardButton(BUTTON_TEXT1, url=CHANNEL_LINK)],
        [InlineKeyboardButton(BUTTON_TEXT2, url=OWNER_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return message_text, reply_markup

class TelegramSender:
    def __init__(self, token, stop_signal):
        self.token, self.queue, self.stop_event = token, queue.Queue(), stop_signal
        self.thread = threading.Thread(target=self._worker, daemon=True)
    def start(self): self.thread.start(); print("[*] Telegram Sender thread started.")
    
    def _worker(self):
        while not self.stop_event.is_set():
            try:
                # MODIFIED: Unpack 4 item (termasuk markup)
                chat_id, text, markup, sms_hash = self.queue.get(timeout=1)
                # MODIFIED: pass markup ke _send_message
                if self._send_message(chat_id, text, markup): add_sms_to_reported_db(sms_hash)
                self.queue.task_done()
            except queue.Empty: continue
    
    # MODIFIED: Terima parameter reply_markup
    def _send_message(self, chat_id, text, reply_markup=None):
        api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
        
        # Tambahkan reply_markup ke payload jika ada
        if reply_markup:
            payload['reply_markup'] = reply_markup.to_dict()

        try:
            r = requests.post(api_url, json=payload, timeout=20)
            if r.status_code != 200: print(f"[!] Telegram API Error: {r.status_code} - {r.text}")
            return r.status_code == 200
        except Exception as e:
            print(f"[!] Failed to send message to Telegram: {e}"); return False
    
    # MODIFIED: Terima markup di queue
    def queue_message(self, chat_id, text, markup, sms_hash): 
        self.queue.put((chat_id, text, markup, sms_hash))

telegram_sender = TelegramSender(TELEGRAM_BOT_TOKEN, stop_event)

def setup_database():
    global db_connection, reported_sms_hashes_cache
    try:
        db_connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        cursor = db_connection.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS reported_sms (hash TEXT PRIMARY KEY)')
        reported_sms_hashes_cache = {row[0] for row in cursor.execute("SELECT hash FROM reported_sms")}
        db_connection.commit(); print(f"[*] Database connected. Loaded {len(reported_sms_hashes_cache)} hashes.")
        return True
    except sqlite3.Error as e: print(f"[!!!] DATABASE ERROR: {e}"); return False

def add_sms_to_reported_db(sms_hash):
    try:
        with db_connection: db_connection.execute("INSERT INTO reported_sms (hash) VALUES (?)", (sms_hash,))
    except sqlite3.Error: pass

def send_operational_message(chat_id, text):
    try: requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={'chat_id': chat_id, 'text': f"{text}\n\n🤖 _{BOT_NAME}_", 'parse_mode': 'Markdown'}, timeout=15)
    except Exception: pass

def graceful_shutdown(signum, frame):
    print("\n[!!!] Shutdown signal detected. Stopping.")
    stop_event.set()
    time.sleep(1)
    if db_connection: db_connection.close()
    sys.exit(0)

def solve_math_captcha(captcha_text):
    match = re.search(r'(\d+)\s*([+*])\s*(\d+)', captcha_text)
    if not match: return None
    n1, op, n2 = int(match.group(1)), match.group(2), int(match.group(3))
    result = n1 + n2 if op == '+' else n1 * n2
    print(f"[*] Solved Captcha: {n1} {op} {n2} = {result}")
    return result

def start_watching_sms(session, destination_chat_id):
    global working_api_url
    polling_interval = 1
    
    while not stop_event.is_set():
        try:
            print(f"[*] Fetching SMS data... ({time.strftime('%H:%M:%S')})")
            print(f"    - Current session cookies: {session.cookies.get_dict()}")

            if not working_api_url:
                print("[!] Working API URL not set. Trying to find it again...")
                for url_to_test in POTENTIAL_API_URLS:
                    try:
                        test_response = session.get(url_to_test, timeout=20, params={'sEcho': '1'})
                        if test_response.status_code != 404:
                            print(f"[SUCCESS] Found working API URL: {url_to_test}")
                            working_api_url = url_to_test; break
                    except requests.exceptions.RequestException: pass
                if not working_api_url:
                    print("[!!!] CRITICAL: Could not find a working API URL. Bot cannot proceed.")
                    graceful_shutdown(None, None)

            date_to, date_from = datetime.now(), datetime.now() - timedelta(days=1)
            params = {'fdate1': date_from.strftime('%Y-%m-%d %H:%M:%S'), 'fdate2': date_to.strftime('%Y-%m-%d %H:%M:%S')}
            api_headers = {"Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest", "Referer": SMS_HTML_PAGE_URL}
            
            response = session.get(working_api_url, params=params, headers=api_headers, timeout=30)
            
            print(f"    - API Status Code: {response.status_code}")
            # print(f"    - API Response (first 150 chars): {response.text[:150]}") # Debugging

            response.raise_for_status()
            json_data = response.json()
            
            if 'aaData' in json_data and isinstance(json_data['aaData'], list):
                sms_list = json_data['aaData']
                print(f"    - Found {len(sms_list)} SMS entries in the API response.")
                
                for sms_data in reversed(sms_list):
                    if len(sms_data) > 5:
                        dt, rc, sn, msg = str(sms_data[0]), str(sms_data[2]), str(sms_data[3]), str(sms_data[4])
                        
                        if not msg or not rc or rc.strip() == '0' or len(rc.strip()) < 5:
                            # print(f"    - Ignoring invalid/empty SMS data: Number='{rc}', Message='{msg}'")
                            continue

                        h = hashlib.md5(f"{dt}-{rc}-{msg}".encode()).hexdigest()
                        
                        print(f"    - Processing SMS for {rc}. Hash: {h}")
                        if h not in reported_sms_hashes_cache:
                            reported_sms_hashes_cache.add(h)
                            print(f"    - [+] New SMS Queued! For: {rc}")
                            otp_match = re.search(r'\b(\d{3}[-\s]\d{3})\b|\b(\d{4,8})\b', msg)
                            otp = otp_match.group(0) if otp_match else "N/A"
                            
                            # MODIFIED: Mendapatkan text DAN markup
                            notification_message, markup = format_telegram_message(rc, sn, msg, otp, dt)
                            # MODIFIED: Kirim text dan markup ke queue
                            telegram_sender.queue_message(destination_chat_id, notification_message, markup, h)
                        else:
                            # print(f"    - [-] Duplicate SMS ignored (hash already in cache).")
                            pass
            else:
                print("[!] API response format is not as expected. 'aaData' key not found or is not a list.")
            
            print("-" * 40)
            time.sleep(polling_interval)
            
        except requests.exceptions.RequestException as e: print(f"[!] Network error: {e}. Retrying..."); time.sleep(30)
        except Exception as e: print(f"[!!!] CRITICAL ERROR in SMS watch loop: {e}"); time.sleep(30)

def main():
    signal.signal(signal.SIGINT, graceful_shutdown)
    print("="*60 + "\n--- NumberPanel OTP Bot (v4.8 Format Update) ---\n" + "="*60)
    if not setup_database(): return
    
    try:
        with requests.Session() as session:
            session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'})
            print("\n[*] Step 1: Logging in...")
            r = session.get(LOGIN_PAGE_URL, timeout=20); soup = BeautifulSoup(r.text, 'html.parser')
            form = soup.find('form');
            if not form: raise Exception("Could not find <form> tag.")
            post_url = form.get('action')
            if not post_url.startswith('http'): post_url = f"{BASE_URL}/{post_url.lstrip('/')}"
            
            payload = {}
            for tag in form.find_all('input'):
                n, v, p = tag.get('name'), tag.get('value', ''), tag.get('placeholder', '').lower()
                if not n: continue
                if 'user' in p: payload[n] = USERNAME
                elif 'pass' in p: payload[n] = PASSWORD
                elif 'ans' in p:
                    el = soup.find(string=re.compile(r'What is \d+ \s*[+*]\s* \d+'))
                    if not el: raise Exception("Could not find captcha text.")
                    payload[n] = solve_math_captcha(el)
                else: payload[n] = v
            
            r = session.post(post_url, data=payload, headers={'Referer': LOGIN_PAGE_URL})
            
            if "dashboard" in r.url.lower() or "Logout" in r.text:
                print("[SUCCESS] Authentication complete!")
                print(f"    - Final URL: {r.url}")
                print(f"    - Final Session Cookies: {session.cookies.get_dict()}")
                telegram_sender.start()
                send_operational_message(DM_CHAT_ID, "✅ *Bot Started & Logged In!*\n\nWatching for SMS on NumberPanel.")
                start_watching_sms(session, DEFAULT_GROUP_CHAT_ID)
            else:
                print("\n[!!!] AUTHENTICATION FAILED.")
                e_div = BeautifulSoup(r.text, 'html.parser').find('div', class_='alert-danger')
                print(f"    - Reason: {e_div.get_text(strip=True)}" if e_div else f"    - Status: {r.status_code}, URL: {r.url}. Check credentials.")
                print(f"    - Full response on failure: {r.text[:500]}")
    except Exception as e:
        print(f"\n[!!!] Critical startup error: {e}")

if __name__ == "__main__":
    main()
