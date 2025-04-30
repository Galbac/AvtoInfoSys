import os
import requests
from app.config_loader import load_config, logger

config = load_config()
BOT_TOKEN = config.get("BOT_TOKEN")
CHAT_ID = config.get("ADMIN_CHAT_ID")


def is_internet_available(url="https://api.telegram.org", timeout=3):
    """Проверяет наличие подключения к интернету через HTTP-запрос."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200 or response.status_code == 404  # 404 тоже признак доступа
    except requests.RequestException:
        return False


def send_summary_to_telegram(all_results, all_stats, dry_run=False):
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("❌ Не заданы BOT_TOKEN или ADMIN_CHAT_ID в config.yaml.")
        return

    if not is_internet_available():
        logger.warning("⚠️ Нет подключения к интернету. Пропускаем отправку Telegram-сообщения.")
        return

    message = "📁 Синхронизация завершена."
    if dry_run:
        message = "🧪 [Dry Run]\n" + message

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": message}
        )
        if response.ok:
            logger.info("📤 Итоговое сообщение отправлено в Telegram")
        else:
            logger.error(f"❌ Ошибка Telegram: {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"❌ Исключение при отправке Telegram-сообщения: {e}")


def send_report_file_to_telegram(report_path):
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("❌ Не заданы BOT_TOKEN или ADMIN_CHAT_ID в config.yaml.")
        return

    if not is_internet_available():
        logger.warning("⚠️ Нет подключения к интернету. Пропускаем отправку отчета в Telegram.")
        return

    try:
        with open(report_path, "rb") as file:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                data={"chat_id": CHAT_ID},
                files={"document": file}
            )
        if response.ok:
            logger.info("📤 Отчет отправлен в Telegram")
        else:
            logger.error(f"❌ Ошибка Telegram: {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"❌ Исключение при отправке отчета в Telegram: {e}")
