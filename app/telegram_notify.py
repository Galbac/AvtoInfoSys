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

def is_internet_available(url: str = "https://api.telegram.org", timeout: int = 3) -> bool:
    """Проверяет доступность интернета по URL с таймаутом."""
    try:
        response = requests.get(url, timeout=timeout)
        # 200 OK и 404 Not Found считаем как доступность API Telegram
        return response.status_code in (200, 404)
    except requests.RequestException:
        return False


def send_to_user(user_id: int, content: str, user_ids: list[int], is_file: bool = False) -> bool:
    """
    Отправляет сообщение или файл пользователю через Telegram Bot API.
    При ошибке 403 удаляет пользователя из списка user_ids.

    :param user_id: ID пользователя Telegram
    :param content: текст сообщения или путь к файлу
    :param user_ids: общий список пользователей для обновления при блокировке
    :param is_file: если True, отправляется файл
    :return: True при успешной отправке, иначе False
    """
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в .env файле.")
        return False

    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    url = f"{base_url}/sendDocument" if is_file else f"{base_url}/sendMessage"

    data = {"chat_id": user_id}
    files = None

    try:
        if is_file:
            with open(content, "rb") as file:
                files = {"document": file}
                response = requests.post(url, data=data, files=files, timeout=10)
        else:
            data["text"] = content
            response = requests.post(url, data=data, timeout=10)
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке {'файла' if is_file else 'сообщения'} пользователю {user_id}: {e}")
        return False

    if response.ok:
        logger.info(f"📤 {'Отчет' if is_file else 'Сообщение'} отправлен пользователю {user_id}")
        return True
    else:
        logger.error(f"❌ Ответ Telegram: {response.status_code} {response.text}")
        if response.status_code == 403:
            with _lock:
                if user_id in user_ids:
                    user_ids.remove(user_id)
                    logger.warning(f"🚫 Пользователь {user_id} удалён из списка (заблокировал бота)")
        return False


def send_summary_to_telegram(all_results, all_stats, dry_run: bool = False) -> None:
    """
    Отправляет итоговое текстовое сообщение всем получателям из списка.
    Использует пул потоков для параллельной отправки.
    """
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
        # Используем копию списка, т.к. он может изменяться в send_to_user
        for user_id in user_ids.copy():
            executor.submit(send_to_user, user_id, message, user_ids, is_file=False)


def send_report_file_to_telegram(report_path: str) -> bool:
    """
    Отправляет файл отчёта всем получателям.
    Возвращает True, если хотя бы одна отправка успешна.
    """
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в .env файле.")
        return False
    if not is_internet_available():
        logger.warning("⚠️ Нет интернета. Пропуск отправки отчета.")
        return False

    user_ids = load_recipients()
    if not user_ids:
        logger.warning("⚠️ Нет пользователей для отправки.")
        return False

    logger.info(f"📤 Отправка отчета ({len(user_ids)} пользователей)...")

    success_count = 0
    with ThreadPoolExecutor(max_workers=min(len(user_ids), 30)) as executor:
        futures = [
            executor.submit(send_to_user, user_id, report_path, user_ids, is_file=True)
            for user_id in user_ids.copy()
        ]

        for future in futures:
            try:
                if future.result():
                    success_count += 1
            except Exception as e:
                logger.error(f"❌ Ошибка в потоке отправки: {e}")

    return success_count > 0
