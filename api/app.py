import requests
import time
import re
import pycountry
from datetime import datetime

TELEGRAM_BOT_TOKEN = '7815634776:AAHE9U0wlYB3m0bemuqgPx2Y9W7_gdWGE58'
TELEGRAM_CHAT_ID = '-1003361941052'

BUTTON_1_NAME = "📢 Join Channel"
BUTTON_1_LINK = "https://t.me/jndtech1"

BUTTON_2_NAME = "👨‍💻 Admin Support"
BUTTON_2_LINK = "https://t.me/junaidniz786"

API_URL = "http://51.89.99.105/NumberPanel/ints/client/res/data_smscdr.php"

HEADERS = {
    "Host": "51.89.99.105",
    "User-Agent": "Mozilla/5.0 (Linux; Android 15; V2423 Build/AP3A.240905.015.A2_D1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7499.34 Mobile Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "http://139.99.63.204/ints/client/SMSCDRStats",
    "Accept-Language": "en-US,en;q=0.9,ur-PK;q=0.8,ur;q=0.7",
    "Cookie": "PHPSESSID=ffsl513e49c72lt3sc0lsc6ld0" 
}

sent_messages_cache = []

def get_flag_emoji(country_text):
    try:
        clean_name = re.split(r'\d', country_text)[0].strip()
        country = pycountry.countries.search_fuzzy(clean_name)[0]
        code = country.alpha_2
        OFFSET = 127397
        return "".join([chr(ord(c) + OFFSET) for c in code])
    except:
        return "🏳️"

def extract_otp_code(message):
    match = re.search(r'\b(\d{3,8}|\d{3}-\d{3})\b', message)
    if match:
        return match.group(0)
    return "Not Found"

def format_phone_number(number):
    s_num = str(number)
    if len(s_num) > 7:
        return s_num[:3] + "*" * (len(s_num) - 7) + s_num[-4:]
    return s_num

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": BUTTON_1_NAME, "url": BUTTON_1_LINK},
                {"text": BUTTON_2_NAME, "url": BUTTON_2_LINK}
            ]
        ]
    }
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def get_sms_data():
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        params = {
            "fdate1": f"{current_date} 00:00:00",
            "fdate2": f"{current_date} 23:59:59",
            "frange": "", "fnum": "", "fcli": "", "fgdate": "", "fgmonth": "",
            "fgrange": "", "fgnumber": "", "fgcli": "", "fg": "0",
            "sEcho": "1", "iColumns": "7", "sColumns": ",,,,,,",
            "iDisplayStart": "0", "iDisplayLength": "25",
            "mDataProp_0": "0", "mDataProp_1": "1", "mDataProp_2": "2",
            "mDataProp_3": "3", "mDataProp_4": "4", "mDataProp_5": "5",
            "mDataProp_6": "6",
            "sSearch": "", "bRegex": "false",
            "iSortCol_0": "0", "sSortDir_0": "desc",
            "iSortingCols": "1",
            "_": int(time.time() * 1000)
        }
        response = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

def main():
    print("Bot Started...")
    
    while True:
        data = get_sms_data()
        
        if data and "aaData" in data:
            rows = data["aaData"]
            
            for row in rows:
                if len(row) < 5 or "Your WhatsApp code" not in str(row[4]):
                    if len(row) > 2 and row[3] == 0: 
                         continue

                time_stamp = row[0]
                country_raw = row[1]
                phone_number = row[2]
                service_name = row[3]
                sms_content = row[4]
                
                unique_id = f"{phone_number}_{sms_content}"
                
                if unique_id not in sent_messages_cache:
                    clean_country_name = re.split(r'\d', country_raw)[0].strip()
                    flag = get_flag_emoji(clean_country_name)
                    otp_code = extract_otp_code(sms_content)
                    masked_number = format_phone_number(phone_number)
                    
                    header = f"*{service_name}* {flag} *New OTP Received*"
                    
                    msg_text = (
                        f"{header}\n"
                        f">━━━━━━━━━━━━━━\n"
                        f">⏰ *Time:* `{time_stamp}`\n"
                        f">\n"
                        f">🌍 *Country:* `{flag} {clean_country_name}`\n"
                        f">\n"
                        f">📱 *Number:* `+{masked_number}`\n"
                        f">\n"
                        f">💬 *Service:* `{service_name}`\n"
                        f">\n"
                        f">🔢 *OTP Code:* `{otp_code}`\n"
                        f">\n"
                        f">✉️ *Message:* `{sms_content}`\n"
                        f">━━━━━━━━━━━━━━"
                    )
                    
                    send_telegram_message(msg_text)
                    print(f"Sent message to {masked_number}")
                    
                    sent_messages_cache.append(unique_id)
                    if len(sent_messages_cache) > 100:
                        sent_messages_cache.pop(0)
        
        time.sleep(3)

if __name__ == "__main__":
    main()


