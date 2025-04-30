#telegram_notify
import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from app.config_loader import load_config
from app.logger import get_logger

logger = get_logger()
config = load_config()
BOT_TOKEN = config.get("BOT_TOKEN")
USERS_FILE = "data/users.json"
_lock = Lock()


def is_internet_available(url="https://api.telegram.org", timeout=3):
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code in (200, 404)
    except requests.RequestException:
        return False


def load_user_ids():
    if not os.path.exists(USERS_FILE):
        return []

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception as e:
        logger.error(f"❌ Ошибка при чтении {USERS_FILE}: {e}")
    return []


def save_user_ids(user_ids):
    try:
        with _lock:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(user_ids, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении {USERS_FILE}: {e}")


def send_message_to_user(user_id, message_text, user_ids):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": user_id, "text": message_text}
        )
        if response.ok:
            logger.info(f"📤 Сообщение отправлено пользователю {user_id}")
        else:
            logger.error(f"❌ Ошибка при отправке пользователю {user_id}: {response.status_code} {response.text}")
            if response.status_code == 403:
                with _lock:
                    if user_id in user_ids:
                        user_ids.remove(user_id)
                        logger.warning(f"🚫 Пользователь {user_id} удалён из списка (заблокировал бота)")
    except Exception as e:
        logger.error(f"❌ Исключение при отправке пользователю {user_id}: {e}")


def send_file_to_user(user_id, file_path, user_ids):
    try:
        with open(file_path, "rb") as file:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                data={"chat_id": user_id},
                files={"document": file}
            )
        if response.ok:
            logger.info(f"📤 Отчет отправлен пользователю {user_id}")
        else:
            logger.error(f"❌ Ошибка при отправке отчета пользователю {user_id}: {response.status_code} {response.text}")
            if response.status_code == 403:
                with _lock:
                    if user_id in user_ids:
                        user_ids.remove(user_id)
                        logger.warning(f"🚫 Пользователь {user_id} удалён из списка (заблокировал бота)")
    except Exception as e:
        logger.error(f"❌ Исключение при отправке отчета пользователю {user_id}: {e}")


def send_summary_to_telegram(all_results, all_stats, dry_run=False):
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан в config.yaml.")
        return

    if not is_internet_available():
        logger.warning("⚠️ Нет подключения к интернету. Пропускаем отправку Telegram-сообщений.")
        return

    user_ids = load_user_ids()
    if not user_ids:
        logger.warning("⚠️ Нет пользователей для отправки сообщений.")
        return

    message = "📁 Синхронизация завершена."
    if dry_run:
        message = "🧪 [Dry Run]\n" + message

    logger.info(f"📤 Отправка итогового сообщения ({len(user_ids)} пользователей)...")

    user_ids_copy = user_ids.copy()
    max_threads = min(len(user_ids_copy), 30)
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for user_id in user_ids_copy:
            executor.submit(send_message_to_user, user_id, message, user_ids)

    save_user_ids(user_ids)


def send_report_file_to_telegram(report_path):
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не задан в config.yaml.")
        return

    if not is_internet_available():
        logger.warning("⚠️ Нет подключения к интернету. Пропускаем отправку отчетов.")
        return

    user_ids = load_user_ids()
    if not user_ids:
        logger.warning("⚠️ Нет пользователей для отправки отчетов.")
        return

    logger.info(f"📤 Отправка отчета ({len(user_ids)} пользователей)...")

    user_ids_copy = user_ids.copy()
    max_threads = min(len(user_ids_copy), 30)
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for user_id in user_ids_copy:
            executor.submit(send_file_to_user, user_id, report_path, user_ids)

    save_user_ids(user_ids)
