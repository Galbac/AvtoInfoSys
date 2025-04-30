import os
import requests
from app.logger import get_logger

logger = get_logger()

def send_report_file_to_telegram(file_path: str):
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("ADMIN_CHAT_ID")

    if not bot_token or not chat_id:
        logger.error("Ошибка при отправке отчета в Telegram: отсутствует BOT_TOKEN или ADMIN_CHAT_ID в .env.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    try:
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"chat_id": chat_id}
            response = requests.post(url, data=data, files=files)

        if response.status_code != 200:
            logger.error(f"Не удалось отправить отчет в Telegram: {response.text}")
        else:
            logger.info("📤 Отчет отправлен в Telegram")
    except Exception as e:
        logger.error(f"Ошибка при отправке отчета в Telegram: {e}")
