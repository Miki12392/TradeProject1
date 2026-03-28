import requests
from config.settings import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_msg(msg: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[LOG] {msg}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
        if response.status_code != 200:
            print(f"❌ [TELEGRAM ERROR] Kod: {response.status_code}, Treść: {response.text}")
    except Exception as e:
        print(f"❌ [CONNECTION ERROR] {e}")