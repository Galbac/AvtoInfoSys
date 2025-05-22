from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Tuple

from app.logger import get_logger
from app.config_loader import load_config
from app.reporter import save_html_report
from app.telegram_notify import send_report_file_to_telegram, is_internet_available

logger = get_logger()

def sync_one_folder(
    name: str,
    network_path: str,
    destination_paths: List[str],
    report_path_root: str,
    dry_run: bool
) -> Tuple[str, List[Tuple[str, str]], Dict[str, int]]:
    logger.info(f"🔍 Сканируем папку: {name}")
    try:
        from app.smb_utils import sync_folder
        result, stats = sync_folder(name, network_path, destination_paths, report_path_root, dry_run)
        return name, result, stats
    except Exception as e:
        logger.exception(f"❌ Ошибка при синхронизации {name}: {e}")
        return name, [], {"added": 0, "modified": 0, "copied": 0}

def prepare_results_by_bureau(
    all_results: Dict[str, List[Tuple[str, str]]],
    all_stats: Dict[str, Dict[str, int]],
    sources: List[Dict]
) -> Tuple[Dict[str, Dict[str, List[Tuple[str, str]]]], Dict[str, Dict[str, Dict[str, int]]]]:
    results_by_bureau = {}
    stats_by_bureau = {}

    for source in sources:
        name = source.get("name")
        buro = source.get("buro", "Без бюро")

        results_by_bureau.setdefault(buro, {})[name] = all_results.get(name, [])
        stats_by_bureau.setdefault(buro, {})[name] = all_stats.get(name, {"added": 0, "modified": 0, "copied": 0})

    return results_by_bureau, stats_by_bureau

def start_sync(config_path: str = "config.yaml", dry_run: bool = False) -> None:
    logger.info("🚀 Запуск синхронизации...")

    internet_available = is_internet_available()
    if not internet_available:
        logger.warning("⚠️ Интернет недоступен. Отправка в Telegram будет отключена.")

    config = load_config(config_path)
    destination = config.get("destination", {})
    destination_paths = destination.get("paths", [])
    if isinstance(destination_paths, str):
        destination_paths = [destination_paths]

    report_path_root = destination_paths[0] if destination_paths else None
    sources = config.get("sources", [])

    if not destination_paths or not sources:
        logger.error("❌ Конфигурация неполная: отсутствует 'destination.paths' или список 'sources'")
        return

    all_results: Dict[str, List[Tuple[str, str]]] = {}
    all_stats: Dict[str, Dict[str, int]] = {}

    max_workers = min(32, (len(sources) or 1))  # Ограничиваем число потоков

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                sync_one_folder, src["name"], src["path"], destination_paths, report_path_root, dry_run
            ): src["name"]
            for src in sources
        }

        for future in as_completed(futures):
            name = futures[future]
            try:
                folder_name, result, stats = future.result()
                all_results[folder_name] = result
                all_stats[folder_name] = stats
                logger.info(f"✅ Синхронизирована папка: {folder_name} — добавлено: {stats.get('added',0)}, изменено: {stats.get('modified',0)}")
            except Exception as e:
                logger.exception(f"❌ Ошибка при обработке папки {name}: {e}")

    results_by_bureau, stats_by_bureau = prepare_results_by_bureau(all_results, all_stats, sources)

    report_datetime = datetime.now()
    report_path = save_html_report(results_by_bureau, stats_by_bureau, report_datetime)

    if internet_available:
        try:
            send_report_file_to_telegram(report_path)
            logger.info("📤 Отчет отправлен в Telegram")
        except Exception as e:
            logger.exception(f"❌ Не удалось отправить отчет в Telegram: {e}")
    else:
        logger.info(f"💾 Интернет недоступен, отчет сохранён локально: {report_path}")

    logger.info("✅ Синхронизация завершена")
