import time
import requests
import json
import re
import os
from datetime import datetime, date, timedelta
from urllib.parse import quote_plus
from pathlib import Path
import sqlite3
import telebot
from telebot import types
import threading
import random

BASE = "http://139.99.63.204"
AJAX_PATH = "/ints/agent/res/data_smscdr.php"
LOGIN_PAGE_URL = BASE + "/ints/login"
LOGIN_POST_URL = BASE + "/ints/signin"
USERNAME = "Junaidniz786" 
PASSWORD = "Junaidniz786"
BOT_TOKEN = "8550802106:AAFCYSUjiV0PnaGpfloLMYwfwiomoijwVcw"
CHAT_IDS = [
    "-1003361941052",
]
REFRESH_INTERVAL = 7
TIMEOUT = 100
MAX_RETRIES = 5
RETRY_DELAY = 5
IDX_DATE = 0
IDX_NUMBER = 2
IDX_SMS = 5
SENT_MESSAGES_FILE = "sent_messages.json"


ADMIN_IDS = [7011937754, 0000]  
DB_PATH = "bot.db"
FORCE_SUB_CHANNEL = None
FORCE_SUB_ENABLED = False


if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN must be set in Secrets (Environment Variables)")
if not CHAT_IDS:
    raise SystemExit("❌ CHAT_IDS must be configured")
if not USERNAME or not PASSWORD:
    print("⚠️  WARNING: SITE_USERNAME and SITE_PASSWORD not set in Secrets")
    print("⚠️  Bot will continue but login may fail")


COUNTRY_CODES = {
    "1": ("USA/Canada", "🇺🇸", "USA/CANADA"),
    "7": ("Russia", "🇷🇺", "RUSSIA"),
    "20": ("Egypt", "🇪🇬", "EGYPT"),
    "27": ("South Africa", "🇿🇦", "SOUTH AFRICA"),
    "30": ("Greece", "🇬🇷", "GREECE"),
    "31": ("Netherlands", "🇳🇱", "NETHERLANDS"),
    "32": ("Belgium", "🇧🇪", "BELGIUM"),
    "33": ("France", "🇫🇷", "FRANCE"),
    "34": ("Spain", "🇪🇸", "SPAIN"),
    "36": ("Hungary", "🇭🇺", "HUNGARY"),
    "39": ("Italy", "🇮🇹", "ITALY"),
    "40": ("Romania", "🇷🇴", "ROMANIA"),
    "41": ("Switzerland", "🇨🇭", "SWITZERLAND"),
    "43": ("Austria", "🇦🇹", "AUSTRIA"),
    "44": ("UK", "🇬🇧", "UK"),
    "45": ("Denmark", "🇩🇰", "DENMARK"),
    "46": ("Sweden", "🇸🇪", "SWEDEN"),
    "47": ("Norway", "🇳🇴", "NORWAY"),
    "48": ("Poland", "🇵🇱", "POLAND"),
    "49": ("Germany", "🇩🇪", "GERMANY"),
    "51": ("Peru", "🇵🇪", "PERU"),
    "52": ("Mexico", "🇲🇽", "MEXICO"),
    "53": ("Cuba", "🇨🇺", "CUBA"),
    "54": ("Argentina", "🇦🇷", "ARGENTINA"),
    "55": ("Brazil", "🇧🇷", "BRAZIL"),
    "56": ("Chile", "🇨🇱", "CHILE"),
    "57": ("Colombia", "🇨🇴", "COLOMBIA"),
    "58": ("Venezuela", "🇻🇪", "VENEZUELA"),
    "60": ("Malaysia", "🇲🇾", "MALAYSIA"),
    "61": ("Australia", "🇦🇺", "AUSTRALIA"),
    "62": ("Indonesia", "🇮🇩", "INDONESIA"),
    "63": ("Philippines", "🇵🇭", "PHILIPPINES"),
    "64": ("New Zealand", "🇳🇿", "NEW ZEALAND"),
    "65": ("Singapore", "🇸🇬", "SINGAPORE"),
    "66": ("Thailand", "🇹🇭", "THAILAND"),
    "81": ("Japan", "🇯🇵", "JAPAN"),
    "82": ("South Korea", "🇰🇷", "SOUTH KOREA"),
    "84": ("Vietnam", "🇻🇳", "VIETNAM"),
    "86": ("China", "🇨🇳", "CHINA"),
    "90": ("Turkey", "🇹🇷", "TURKEY"),
    "91": ("India", "🇮🇳", "INDIA"),
    "92": ("Pakistan", "🇵🇰", "PAKISTAN"),
    "93": ("Afghanistan", "🇦🇫", "AFGHANISTAN"),
    "94": ("Sri Lanka", "🇱🇰", "SRI LANKA"),
    "95": ("Myanmar", "🇲🇲", "MYANMAR"),
    "98": ("Iran", "🇮🇷", "IRAN"),
    "211": ("South Sudan", "🇸🇸", "SOUTH SUDAN"),
    "212": ("Morocco", "🇲🇦", "MOROCCO"),
    "213": ("Algeria", "🇩🇿", "ALGERIA"),
    "216": ("Tunisia", "🇹🇳", "TUNISIA"),
    "218": ("Libya", "🇱🇾", "LIBYA"),
    "220": ("Gambia", "🇬🇲", "GAMBIA"),
    "221": ("Senegal", "🇸🇳", "SENEGAL"),
    "222": ("Mauritania", "🇲🇷", "MAURITANIA"),
    "223": ("Mali", "🇲🇱", "MALI"),
    "224": ("Guinea", "🇬🇳", "GUINEA"),
    "225": ("Ivory Coast", "🇨🇮", "IVORY COAST"),
    "226": ("Burkina Faso", "🇧🇫", "BURKINA FASO"),
    "227": ("Niger", "🇳🇪", "NIGER"),
    "228": ("Togo", "🇹🇬", "TOGO"),
    "229": ("Benin", "🇧🇯", "BENIN"),
    "230": ("Mauritius", "🇲🇺", "MAURITIUS"),
    "231": ("Liberia", "🇱🇷", "LIBERIA"),
    "232": ("Sierra Leone", "🇸🇱", "SIERRA LEONE"),
    "233": ("Ghana", "🇬🇭", "GHANA"),
    "234": ("Nigeria", "🇳🇬", "NIGERIA"),
    "235": ("Chad", "🇹🇩", "CHAD"),
    "236": ("CAR", "🇨🇫", "CENTRAL AFRICAN REP"),
    "237": ("Cameroon", "🇨🇲", "CAMEROON"),
    "238": ("Cape Verde", "🇨🇻", "CAPE VERDE"),
    "239": ("Sao Tome", "🇸🇹", "SAO TOME"),
    "240": ("Eq. Guinea", "🇬🇶", "EQUATORIAL GUINEA"),
    "241": ("Gabon", "🇬🇦", "GABON"),
    "242": ("Congo", "🇨🇬", "CONGO"),
    "243": ("DR Congo", "🇨🇩", "DR CONGO"),
    "244": ("Angola", "🇦🇴", "ANGOLA"),
    "245": ("Guinea-Bissau", "🇬🇼", "GUINEA-BISSAU"),
    "248": ("Seychelles", "🇸🇨", "SEYCHELLES"),
    "249": ("Sudan", "🇸🇩", "SUDAN"),
    "250": ("Rwanda", "🇷🇼", "RWANDA"),
    "251": ("Ethiopia", "🇪🇹", "ETHIOPIA"),
    "252": ("Somalia", "🇸🇴", "SOMALIA"),
    "253": ("Djibouti", "🇩🇯", "DJIBOUTI"),
    "254": ("Kenya", "🇰🇪", "KENYA"),
    "255": ("Tanzania", "🇹🇿", "TANZANIA"),
    "256": ("Uganda", "🇺🇬", "UGANDA"),
    "257": ("Burundi", "🇧🇮", "BURUNDI"),
    "258": ("Mozambique", "🇲🇿", "MOZAMBIQUE"),
    "260": ("Zambia", "🇿🇲", "ZAMBIA"),
    "261": ("Madagascar", "🇲🇬", "MADAGASCAR"),
    "262": ("Reunion", "🇷🇪", "REUNION"),
    "263": ("Zimbabwe", "🇿🇼", "ZIMBABWE"),
    "264": ("Namibia", "🇳🇦", "NAMIBIA"),
    "265": ("Malawi", "🇲🇼", "MALAWI"),
    "266": ("Lesotho", "🇱🇸", "LESOTHO"),
    "267": ("Botswana", "🇧🇼", "BOTSWANA"),
    "268": ("Eswatini", "🇸🇿", "ESWATINI"),
    "269": ("Comoros", "🇰🇲", "COMOROS"),
    "350": ("Gibraltar", "🇬🇮", "GIBRALTAR"),
    "351": ("Portugal", "🇵🇹", "PORTUGAL"),
    "352": ("Luxembourg", "🇱🇺", "LUXEMBOURG"),
    "353": ("Ireland", "🇮🇪", "IRELAND"),
    "354": ("Iceland", "🇮🇸", "ICELAND"),
    "355": ("Albania", "🇦🇱", "ALBANIA"),
    "356": ("Malta", "🇲🇹", "MALTA"),
    "357": ("Cyprus", "🇨🇾", "CYPRUS"),
    "358": ("Finland", "🇫🇮", "FINLAND"),
    "359": ("Bulgaria", "🇧🇬", "BULGARIA"),
    "370": ("Lithuania", "🇱🇹", "LITHUANIA"),
    "371": ("Latvia", "🇱🇻", "LATVIA"),
    "372": ("Estonia", "🇪🇪", "ESTONIA"),
    "373": ("Moldova", "🇲🇩", "MOLDOVA"),
    "374": ("Armenia", "🇦🇲", "ARMENIA"),
    "375": ("Belarus", "🇧🇾", "BELARUS"),
    "376": ("Andorra", "🇦🇩", "ANDORRA"),
    "377": ("Monaco", "🇲🇨", "MONACO"),
    "378": ("San Marino", "🇸🇲", "SAN MARINO"),
    "380": ("Ukraine", "🇺🇦", "UKRAINE"),
    "381": ("Serbia", "🇷🇸", "SERBIA"),
    "382": ("Montenegro", "🇲🇪", "MONTENEGRO"),
    "383": ("Kosovo", "🇽🇰", "KOSOVO"),
    "385": ("Croatia", "🇭🇷", "CROATIA"),
    "386": ("Slovenia", "🇸🇮", "SLOVENIA"),
    "387": ("Bosnia", "🇧🇦", "BOSNIA"),
    "389": ("N. Macedonia", "🇲🇰", "NORTH MACEDONIA"),
    "420": ("Czech Rep", "🇨🇿", "CZECH REPUBLIC"),
    "421": ("Slovakia", "🇸🇰", "SLOVAKIA"),
    "423": ("Liechtenstein", "🇱🇮", "LIECHTENSTEIN"),
    "500": ("Falkland", "🇫🇰", "FALKLAND ISLANDS"),
    "501": ("Belize", "🇧🇿", "BELIZE"),
    "502": ("Guatemala", "🇬🇹", "GUATEMALA"),
    "503": ("El Salvador", "🇸🇻", "EL SALVADOR"),
    "504": ("Honduras", "🇭🇳", "HONDURAS"),
    "505": ("Nicaragua", "🇳🇮", "NICARAGUA"),
    "506": ("Costa Rica", "🇨🇷", "COSTA RICA"),
    "507": ("Panama", "🇵🇦", "PANAMA"),
    "509": ("Haiti", "🇭🇹", "HAITI"),
    "591": ("Bolivia", "🇧🇴", "BOLIVIA"),
    "592": ("Guyana", "🇬🇾", "GUYANA"),
    "593": ("Ecuador", "🇪🇨", "ECUADOR"),
    "595": ("Paraguay", "🇵🇾", "PARAGUAY"),
    "597": ("Suriname", "🇸🇷", "SURINAME"),
    "598": ("Uruguay", "🇺🇾", "URUGUAY"),
    "670": ("Timor-Leste", "🇹🇱", "TIMOR-LESTE"),
    "673": ("Brunei", "🇧🇳", "BRUNEI"),
    "674": ("Nauru", "🇳🇷", "NAURU"),
    "675": ("PNG", "🇵🇬", "PAPUA NEW GUINEA"),
    "676": ("Tonga", "🇹🇴", "TONGA"),
    "677": ("Solomon Is", "🇸🇧", "SOLOMON ISLANDS"),
    "678": ("Vanuatu", "🇻🇺", "VANUATU"),
    "679": ("Fiji", "🇫🇯", "FIJI"),
    "680": ("Palau", "🇵🇼", "PALAU"),
    "685": ("Samoa", "🇼🇸", "SAMOA"),
    "686": ("Kiribati", "🇰🇮", "KIRIBATI"),
    "687": ("New Caledonia", "🇳🇨", "NEW CALEDONIA"),
    "688": ("Tuvalu", "🇹🇻", "TUVALU"),
    "689": ("Fr Polynesia", "🇵🇫", "FRENCH POLYNESIA"),
    "691": ("Micronesia", "🇫🇲", "MICRONESIA"),
    "692": ("Marshall Is", "🇲🇭", "MARSHALL ISLANDS"),
    "850": ("North Korea", "🇰🇵", "NORTH KOREA"),
    "852": ("Hong Kong", "🇭🇰", "HONG KONG"),
    "853": ("Macau", "🇲🇴", "MACAU"),
    "855": ("Cambodia", "🇰🇭", "CAMBODIA"),
    "856": ("Laos", "🇱🇦", "LAOS"),
    "960": ("Maldives", "🇲🇻", "MALDIVES"),
    "961": ("Lebanon", "🇱🇧", "LEBANON"),
    "962": ("Jordan", "🇯🇴", "JORDAN"),
    "963": ("Syria", "🇸🇾", "SYRIA"),
    "964": ("Iraq", "🇮🇶", "IRAQ"),
    "965": ("Kuwait", "🇰🇼", "KUWAIT"),
    "966": ("Saudi Arabia", "🇸🇦", "SAUDI ARABIA"),
    "967": ("Yemen", "🇾🇪", "YEMEN"),
    "968": ("Oman", "🇴🇲", "OMAN"),
    "970": ("Palestine", "🇵🇸", "PALESTINE"),
    "971": ("UAE", "🇦🇪", "UAE"),
    "972": ("Israel", "💩", "ISRAEL"),
    "973": ("Bahrain", "🇧🇭", "BAHRAIN"),
    "974": ("Qatar", "🇶🇦", "QATAR"),
    "975": ("Bhutan", "🇧🇹", "BHUTAN"),
    "976": ("Mongolia", "🇲🇳", "MONGOLIA"),
    "977": ("Nepal", "🇳🇵", "NEPAL"),
    "992": ("Tajikistan", "🇹🇯", "TAJIKISTAN"),
    "993": ("Turkmenistan", "🇹🇲", "TURKMENISTAN"),
    "994": ("Azerbaijan", "🇦🇿", "AZERBAIJAN"),
    "995": ("Georgia", "🇬🇪", "GEORGIA"),
    "996": ("Kyrgyzstan", "🇰🇬", "KYRGYZSTAN"),
    "998": ("Uzbekistan", "🇺🇿", "UZBEKISTAN"),
}

# ======================
# 🧰 Database Management Functions (Updated)
# ======================
def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM bot_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# ======================
# 🧠 Database Initialization (With New Tables)
# ======================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            country_code TEXT,
            assigned_number TEXT,
            is_banned INTEGER DEFAULT 0,
            private_combo_country TEXT DEFAULT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT UNIQUE,
            numbers TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT,
            otp TEXT,
            full_message TEXT,
            timestamp TEXT,
            assigned_to INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dashboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_url TEXT,
            ajax_path TEXT,
            login_page TEXT,
            login_post TEXT,
            username TEXT,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS private_combos (
            user_id INTEGER,
            country_code TEXT,
            numbers TEXT,
            PRIMARY KEY (user_id, country_code)
        )
    ''')
    # ✅ New Force Subscription Channels Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS force_sub_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_url TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1
        )
    ''')

    # Initialize old settings (for backward compatibility)
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('force_sub_channel', '')")
    c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES ('force_sub_enabled', '0')")

    # 🔄 Automatically migrate old channel (if exists) to new table
    c.execute("SELECT value FROM bot_settings WHERE key = 'force_sub_channel'")
    old_channel = c.fetchone()
    if old_channel and old_channel[0].strip():
        channel = old_channel[0].strip()
        # Ensure it's not a duplicate
        c.execute("SELECT 1 FROM force_sub_channels WHERE channel_url = ?", (channel,))
        if not c.fetchone():
            enabled = 1 if get_setting("force_sub_enabled") == "1" else 0
            c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, ?)",
                      (channel, "Main Channel", enabled))

    conn.commit()
    conn.close()

init_db()

# ======================
# 🧰 Database Management Functions (Updated)
# ======================

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user(user_id, username="", first_name="", last_name="", country_code=None, assigned_number=None, private_combo_country=None):
    """
    Saves or updates user data using a single query (INSERT OR REPLACE).
    Prevents race conditions in multi-threaded environments.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    existing_data = get_user(user_id)
    if existing_data:
        if country_code is None:
            country_code = existing_data[4]
        if assigned_number is None:
            assigned_number = existing_data[5]
        if private_combo_country is None:
            private_combo_country = existing_data[7]

    c.execute("""
        REPLACE INTO users (user_id, username, first_name, last_name, country_code, assigned_number, is_banned, private_combo_country)
        VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT is_banned FROM users WHERE user_id=?), 0), ?)
    """, (
        user_id,
        username,
        first_name,
        last_name,
        country_code,
        assigned_number,
        user_id,
        private_combo_country
    ))
    conn.commit()
    conn.close()


def ban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    user = get_user(user_id)
    return user and user[6] == 1

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_combo(country_code, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("SELECT numbers FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
        row = c.fetchone()
        if row:
            conn.close()
            return json.loads(row[0])
    c.execute("SELECT numbers FROM combos WHERE country_code=?", (country_code,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def save_combo(country_code, numbers, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("REPLACE INTO private_combos (user_id, country_code, numbers) VALUES (?, ?, ?)",
                  (user_id, country_code, json.dumps(numbers)))
    else:
        c.execute("REPLACE INTO combos (country_code, numbers) VALUES (?, ?)",
                  (country_code, json.dumps(numbers)))
    conn.commit()
    conn.close()

def delete_combo(country_code, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("DELETE FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
    else:
        c.execute("DELETE FROM combos WHERE country_code=?", (country_code,))
    conn.commit()
    conn.close()

def get_all_combos():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT country_code FROM combos")
    combos = [row[0] for row in c.fetchall()]
    conn.close()
    return combos

def assign_number_to_user(user_id, number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (number, user_id))
    conn.commit()
    conn.close()

def get_user_by_number(number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE assigned_number=?", (number,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def log_otp(number, otp, full_message, assigned_to=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO otp_logs (number, otp, full_message, timestamp, assigned_to) VALUES (?, ?, ?, ?, ?)",
              (number, otp, full_message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), assigned_to))
    conn.commit()
    conn.close()

def release_number(old_number):
    if not old_number:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (old_number,))
    conn.commit()
    conn.close()

def get_otp_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM otp_logs")
    logs = c.fetchall()
    conn.close()
    return logs

def get_user_info(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

# --- Multiple Force Subscription Channels Management ---
def get_all_force_sub_channels(enabled_only=True):
    """Fetch channels (enabled only or all)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if enabled_only:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels WHERE enabled = 1 ORDER BY id")
    else:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def add_force_sub_channel(channel_url, description=""):
    """Add new channel (duplicates not allowed)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, 1)",
                  (channel_url.strip(), description.strip()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Duplicate channel
    finally:
        conn.close()

def delete_force_sub_channel(channel_id):
    """Delete channel by ID"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM force_sub_channels WHERE id = ?", (channel_id,))
    changed = c.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def toggle_force_sub_channel(channel_id):
    """Enable/Disable channel"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE force_sub_channels SET enabled = 1 - enabled WHERE id = ?", (channel_id,))
    conn.commit()
    conn.close()

# ======================
# 🔐 Force Subscription Functions
# ======================
def force_sub_check(user_id):
    """Verify user is subscribed to ALL enabled channels"""
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return True 

    for _, url, _ in channels:
        try:
            if url.startswith("https://t.me/"):
                ch = "@" + url.split("/")[-1]
            elif url.starts
