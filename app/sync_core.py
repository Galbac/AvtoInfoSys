from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Tuple

from app.logger import get_logger
from app.config_loader import load_config
from app.reporter import save_html_report
from app.telegram_notify import send_report_file_to_telegram

logger = get_logger()

def sync_one_folder(
    name: str,
    network_path: str,
    destination_paths: list[str],
    report_path_root: str,
    dry_run: bool
) -> Tuple[str, List[Tuple[str, str]], Dict[str, int]]:
    """
    Синхронизирует одну сетевую папку.
    Возвращает: (имя пользователя, список (файл, статус), статистику)
    """
    logger.info(f"🔍 Сканируем папку: {name}")
    try:
        from app.smb_utils import sync_folder
        result, stats = sync_folder(name, network_path, destination_paths, report_path_root, dry_run)
        # result — должен быть List[Tuple[str, str]], где str — имя файла, str — статус ("added"/"modified" и т.п.)
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

    # У каждого source есть 'name' и 'buro'
    for source in sources:
        name = source.get("name")
        buro = source.get("buro", "Без бюро")

        # Инициализируем словари, если нужно
        if buro not in results_by_bureau:
            results_by_bureau[buro] = {}
            stats_by_bureau[buro] = {}

        results_by_bureau[buro][name] = all_results.get(name, [])
        stats_by_bureau[buro][name] = all_stats.get(name, {"added": 0, "modified": 0, "copied": 0})

    return results_by_bureau, stats_by_bureau

from app.telegram_notify import send_report_file_to_telegram, is_internet_available

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

    with ThreadPoolExecutor() as executor:
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
            except Exception as e:
                logger.exception(f"❌ Ошибка при обработке папки {name}: {e}")

    # Подготовка данных по бюро
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

