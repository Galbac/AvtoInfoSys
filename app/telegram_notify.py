import os
import requests
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from dotenv import load_dotenv

from app.logger import get_logger
from app.utils import load_recipients

load_dotenv()
logger = get_logger()

BOT_TOKEN = os.getenv("BOT_TOKEN")
_lock = Lock()


def is_internet_available(url="https://api.telegram.org", timeout=3) -> bool:
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code in (200, 404)
    except requests.RequestException:
        return False


def send_to_user(user_id: int, content: str, user_ids: list[int], is_file: bool = False) -> None:
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в .env файле.")
        return

    url = (
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        if is_file else
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    )

    data = {"chat_id": user_id}
    files = None

    try:
        if is_file:
            with open(content, "rb") as file:
                files = {"document": file}
                response = requests.post(url, data=data, files=files)
        else:
            data["text"] = content
            response = requests.post(url, data=data)
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке {'файла' if is_file else 'сообщения'} пользователю {user_id}: {e}")
        return

    if response.ok:
        logger.info(f"📤 {'Отчет' if is_file else 'Сообщение'} отправлен пользователю {user_id}")
    else:
        logger.error(f"❌ Ответ Telegram: {response.status_code} {response.text}")
        if response.status_code == 403:
            with _lock:
                if user_id in user_ids:
                    user_ids.remove(user_id)
                    logger.warning(f"🚫 Пользователь {user_id} удалён из списка (заблокировал бота)")


def send_summary_to_telegram(all_results, all_stats, dry_run: bool = False) -> None:
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в .env файле.")
        return
    if not is_internet_available():
        logger.warning("⚠️ Нет интернета. Пропуск отправки Telegram-сообщения.")
        return

    user_ids = load_recipients()
    if not user_ids:
        logger.warning("⚠️ Нет пользователей для отправки.")
        return

    message = "🧪 [Dry Run]\n📁 Синхронизация завершена." if dry_run else "📁 Синхронизация завершена."
    logger.info(f"📤 Отправка итогового сообщения ({len(user_ids)} пользователей)...")

    with ThreadPoolExecutor(max_workers=min(len(user_ids), 30)) as executor:
        for user_id in user_ids.copy():
            executor.submit(send_to_user, user_id, message, user_ids, is_file=False)


def send_report_file_to_telegram(report_path: str) -> None:
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в .env файле.")
        return
    if not is_internet_available():
        logger.warning("⚠️ Нет интернета. Пропуск отправки отчета.")
        return

    user_ids = load_recipients()
    if not user_ids:
        logger.warning("⚠️ Нет пользователей для отправки.")
        return

    logger.info(f"📤 Отправка отчета ({len(user_ids)} пользователей)...")

    with ThreadPoolExecutor(max_workers=min(len(user_ids), 30)) as executor:
        for user_id in user_ids.copy():
            executor.submit(send_to_user, user_id, report_path, user_ids, is_file=True)
