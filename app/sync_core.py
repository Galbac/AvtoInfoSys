from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
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
    destination_paths: list[str],
    report_path_root: str,
    dry_run: bool
) -> Tuple[str, List[str], Dict[str, int]]:
    logger.info(f"🔍 Сканируем папку: {name}")
    try:
        result, stats = sync_folder(name, network_path, destination_paths, report_path_root, dry_run)
        return name, result, stats
    except Exception as e:
        logger.exception(f"❌ Ошибка при синхронизации {name}: {e}")
        return name, [], {"added": 0, "modified": 0, "copied": 0}



def start_sync(config_path: str = "config.yaml", dry_run: bool = False) -> None:
    logger.info("🚀 Запуск синхронизации...")

    config = load_config(config_path)
    destination = config.get("destination", {})
    destination_paths = destination.get("paths")
    sources = config.get("sources", [])

    if not destination_paths or not sources:
        logger.error("❌ Конфигурация неполная: отсутствует 'destination.paths' или список 'sources'")
        return

    all_results: Dict[str, List[str]] = {}
    all_stats: Dict[str, Dict[str, int]] = {}

    with ThreadPoolExecutor() as executor:
        futures = []

        for src in sources:
            for dest_path in destination_paths:
                futures.append(
                    executor.submit(sync_one_folder, src["name"], src["path"], dest_path, dry_run)
                )

        for future in as_completed(futures):
            try:
                folder_name, result, stats = future.result()

                # Объединение результатов по имени
                if folder_name not in all_results:
                    all_results[folder_name] = []
                    all_stats[folder_name] = {"added": 0, "modified": 0, "copied": 0}

                all_results[folder_name].extend(result)
                for k in stats:
                    all_stats[folder_name][k] += stats[k]
            except Exception as e:
                logger.exception("❌ Ошибка при обработке результата синхронизации: %s", e)

    report_datetime = datetime.now()
    report_path = save_html_report(all_results, all_stats, report_datetime)

    try:
        send_report_file_to_telegram(report_path)
        logger.info("📤 Отчет отправлен в Telegram")
    except Exception as e:
        logger.exception(f"❌ Не удалось отправить отчет в Telegram: {e}")

    logger.info("✅ Синхронизация завершена")

