import requests
from django.conf import settings


def send_telegram_message(message: str):
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    chat_id = getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", None)

    if not token or not chat_id:
        print("⚠️ Telegram не настроен")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload, timeout=5)
        if response.status_code != 200:
            print(f"❌ Ошибка отправки Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Исключение при отправке Telegram: {e}")
