import json
import os
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from dotenv import load_dotenv
from app.logger import get_logger

load_dotenv()
logger = get_logger()

BOT_TOKEN = os.getenv("BOT_TOKEN")
USERS_FILE = Path("data/users.json")
_lock = Lock()

def is_internet_available(url="https://api.telegram.org", timeout=3):
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code in (200, 404)
    except requests.RequestException:
        return False

def load_user_ids():
    if not USERS_FILE.exists():
        return []
    try:
        with USERS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"❌ Ошибка при чтении {USERS_FILE}: {e}")
        return []

def save_user_ids(user_ids):
    try:
        with _lock:
            USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with USERS_FILE.open("w", encoding="utf-8") as f:
                json.dump(user_ids, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении {USERS_FILE}: {e}")

def send_to_user(user_id, content, user_ids, is_file=False):
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в .env файле.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument" if is_file else f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": user_id}
    files = None

    if is_file:
        try:
            with open(content, "rb") as file:
                files = {"document": file}
                response = requests.post(url, data=data, files=files)
        except Exception as e:
            logger.error(f"❌ Исключение при отправке файла пользователю {user_id}: {e}")
            return
    else:
        data["text"] = content
        try:
            response = requests.post(url, data=data)
        except Exception as e:
            logger.error(f"❌ Исключение при отправке сообщения пользователю {user_id}: {e}")
            return

    if response.ok:
        msg = "Отчет" if is_file else "Сообщение"
        logger.info(f"📤 {msg} отправлен пользователю {user_id}")
    else:
        logger.error(f"❌ Ошибка при отправке пользователю {user_id}: {response.status_code} {response.text}")
        if response.status_code == 403:
            with _lock:
                if user_id in user_ids:
                    user_ids.remove(user_id)
                    logger.warning(f"🚫 Пользователь {user_id} удалён из списка (заблокировал бота)")

def send_summary_to_telegram(all_results, all_stats, dry_run=False):
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в .env файле.")
        return

    if not is_internet_available():
        logger.warning("⚠️ Нет подключения к интернету. Пропускаем отправку Telegram-сообщений.")
        return

    user_ids = load_user_ids()
    if not user_ids:
        logger.warning("⚠️ Нет пользователей для отправки сообщений.")
        return

    message = "🧪 [Dry Run]\n📁 Синхронизация завершена." if dry_run else "📁 Синхронизация завершена."
    logger.info(f"📤 Отправка итогового сообщения ({len(user_ids)} пользователей)...")

    user_ids_copy = user_ids.copy()
    max_threads = min(len(user_ids_copy), 30)
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for user_id in user_ids_copy:
            executor.submit(send_to_user, user_id, message, user_ids, is_file=False)

    save_user_ids(user_ids)

def send_report_file_to_telegram(report_path):
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в .env файле.")
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
            executor.submit(send_to_user, user_id, report_path, user_ids, is_file=True)

    save_user_ids(user_ids)
