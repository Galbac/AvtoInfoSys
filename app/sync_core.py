# app/sync_core.py

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

from app.logger import get_logger
from app.config_loader import load_config
from app.reporter import save_html_report
from app.telegram_notify import send_report_file_to_telegram
from app.smb_utils import sync_folder

logger = get_logger()


def sync_one_folder(
    name: str,
    network_path: str,
    destination_root: str,
    dry_run: bool
) -> Tuple[str, List[Dict], Dict[str, int]]:
    """
    Синхронизирует одну сетевую папку.

    Возвращает:
        - имя папки
        - список результатов (изменённых файлов)
        - статистику по действиям
    """
    logger.info(f"🔍 Сканируем папку: {name}")
    try:
        result, stats = sync_folder(name, network_path, destination_root, dry_run)
        return name, result, stats
    except Exception as e:
        logger.exception(f"❌ Ошибка при синхронизации {name}")
        return name, [], {"added": 0, "modified": 0, "copied": 0}


def start_sync(config_path: str = "config.yaml", dry_run: bool = False) -> None:
    """
    Запускает синхронизацию всех указанных в конфиге папок.
    """
    logger.info("🚀 Запуск синхронизации...")

    config = load_config(config_path)
    destination_root = config.get("destination_root")
    shared_folders = config.get("shared_folders")

    if not destination_root or not shared_folders:
        logger.error("❌ Конфигурация неполная: отсутствует 'destination_root' или 'shared_folders'")
        return

    all_results: Dict[str, List[Dict]] = {}
    all_stats: Dict[str, Dict[str, int]] = {}

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(sync_one_folder, name, path, destination_root, dry_run): name
            for name, path in shared_folders.items()
        }

        for future in as_completed(futures):
            try:
                name, result, stats = future.result()
                all_results[name] = result
                all_stats[name] = stats
            except Exception as e:
                name = futures[future]
                logger.exception(f"❌ Ошибка при обработке папки {name}")

    report_path = save_html_report(all_results, all_stats, dry_run)

    try:
        send_report_file_to_telegram(report_path)
        logger.info("📤 Отчет отправлен в Telegram")
    except Exception as e:
        logger.exception("❌ Не удалось отправить отчет в Telegram")

    logger.info("✅ Синхронизация завершена")
