# app/sync_core.py

from concurrent.futures import ThreadPoolExecutor, as_completed
from app.logger import get_logger
from app.config_loader import load_config
from app.reporter import save_html_report
from app.telegram_notify import send_report_file_to_telegram
from app.smb_utils import sync_folder  # ✅ правильный импорт

logger = get_logger()


def sync_one_folder(name, network_path, destination_root, dry_run):
    logger.info(f"🔍 Сканируем папку: {name}")
    try:
        result, stats = sync_folder(name, network_path, destination_root, dry_run)
        return name, result, stats
    except Exception as e:
        logger.error(f"❌ Ошибка при синхронизации {name}: {e}")
        return name, [], {"added": 0, "modified": 0, "copied": 0}


def start_sync(config_path="config.yaml", dry_run=False):
    config = load_config(config_path)
    destination_root = config["destination_root"]
    shared_folders = config["shared_folders"]

    logger.info("🚀 Начинаем синхронизацию...")

    all_results = {}
    all_stats = {}

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(sync_one_folder, name, network_path, destination_root, dry_run)
            for name, network_path in shared_folders.items()
        ]

        for future in as_completed(futures):
            name, result, stats = future.result()
            all_results[name] = result
            all_stats[name] = stats

    report_path = save_html_report(all_results, all_stats, dry_run)

    try:
        send_report_file_to_telegram(report_path)
        logger.info("📤 Отчет отправлен в Telegram")
    except Exception as e:
        logger.error(f"Ошибка Telegram: {e}")

    logger.info("✅ Синхронизация завершена")
