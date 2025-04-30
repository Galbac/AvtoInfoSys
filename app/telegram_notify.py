import json
import os
import requests
from app.config_loader import load_config, logger

USER_DATA_FILE = 'data/users.json'
config = load_config()
BOT_TOKEN = config.get("BOT_TOKEN")


def is_internet_available(url="https://api.telegram.org", timeout=3):
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code in (200, 404)
    except requests.RequestException:
        return False


def load_user_ids():
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
            if isinstance(users, list):
                return users
            logger.error("❌ users.json должен содержать список чисел (ID)")
    except Exception as e:
        logger.error(f"❌ Ошибка чтения users.json: {e}")
    return []


def send_report_file_to_telegram(report_path):
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан в config.yaml.")
        return

    if not is_internet_available():
        logger.warning("⚠️ Нет подключения к интернету. Пропускаем отправку отчета в Telegram.")
        return

    user_ids = load_user_ids()
    if not user_ids:
        logger.warning("⚠️ Нет пользователей для отправки отчета.")
        return

    for user_id in user_ids:
        try:
            with open(report_path, "rb") as file:
                response = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                    data={"chat_id": user_id},
                    files={"document": file}
                )
            if response.ok:
                logger.info(f"📤 Отчет отправлен пользователю {user_id}")
            else:
                logger.error(f"❌ Ошибка при отправке пользователю {user_id}: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"❌ Исключение при отправке пользователю {user_id}: {e}")
