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
) -> Tuple[str, List[str], Dict[str, int]]:
    """
    Синхронизирует одну сетевую папку.
    """
    logger.info(f"🔍 Сканируем папку: {name}")
    try:
        result, stats = sync_folder(name, network_path, destination_root, dry_run)
        return name, result, stats
    except Exception as e:
        logger.exception(f"❌ Ошибка при синхронизации {name}: {e}")
        return name, [], {"added": 0, "modified": 0, "copied": 0}


def start_sync(config_path: str = "config.yaml", dry_run: bool = False) -> None:
    """
    Запускает синхронизацию всех папок, указанных в конфигурации.
    """
    logger.info("🚀 Запуск синхронизации...")

    config = load_config(config_path)
    destination = config.get("destination", {})
    destination_root = destination.get("path")
    sources = config.get("sources", [])

    if not destination_root or not sources:
        logger.error("❌ Конфигурация неполная: отсутствует 'destination.path' или список 'sources'")
        return

    all_results: Dict[str, List[str]] = {}
    all_stats: Dict[str, Dict[str, int]] = {}

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(sync_one_folder, src["name"], src["path"], destination_root, dry_run): src["name"]
            for src in sources
        }

        for future in as_completed(futures):
            name = futures[future]
            try:
                folder_name, result, stats = future.result()
                all_results[folder_name] = result
                all_stats[folder_name] = stats
            except Exception as e:
                logger.exception(f"❌ Ошибка при обработке папки {name}: {e}")

    report_path = save_html_report(all_results, all_stats, dry_run)

    try:
        send_report_file_to_telegram(report_path)
        logger.info("📤 Отчет отправлен в Telegram")
    except Exception as e:
        logger.exception(f"❌ Не удалось отправить отчет в Telegram: {e}")

    logger.info("✅ Синхронизация завершена")
