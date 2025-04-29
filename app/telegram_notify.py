from dotenv import load_dotenv
import os

load_dotenv()  # Загрузит переменные окружения из .env файла

def send_telegram_message(message: str):
    token = os.getenv("TG_BOT_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")

    if not token or not chat_id:
        print("Telegram bot token or chat ID not found.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Ошибка при отправке в Telegram: {e}")
