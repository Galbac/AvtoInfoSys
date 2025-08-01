# app/sync_core.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Dict, List, Tuple
from app.logger import get_logger
from app.config_loader import load_config
from app.reporter import save_html_report

logger = get_logger()

def can_ping(host: str) -> bool:
    """Быстрая проверка доступности по имени (через ping)."""
    import subprocess
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "1000", host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except:
        return False

def is_source_accessible(path: str) -> bool:
    """Проверяет доступность сетевого пути: сначала ping, потом exists."""
    try:
        # Извлекаем имя хоста из пути \\host\share
        if path.startswith("\\\\"):
            host = path.split("\\")[2]
            if not can_ping(host):
                return False
        p = Path(path)
        return p.exists()
    except Exception:
        return False

def save_state_async(data: Dict):
    """Сохраняет состояние в фоне."""
    def _save():
        from app.database import save_state
        save_state(data)
    Thread(target=_save, daemon=True).start()

def sync_one_folder_wrapper(
    source: Dict,
    destination_paths: List[str],
    report_path_root: str,
    dry_run: bool
) -> Tuple[str, List[Tuple[str, str, Dict]], Dict[str, int]]:
    name = source["name"]
    network_path = source["path"]
    logger.info(f"🔍 Сканируем папку: {name} ({network_path})")
    try:
        from app.smb_utils import sync_folder
        result, stats = sync_folder(name, network_path, destination_paths, report_path_root, dry_run)
        # Сохраняем кэш в фоне
        from app.database import load_state
        db = load_state()
        Thread(target=lambda: save_state_async(db), daemon=True).start()
        return name, result, stats
    except Exception as e:
        logger.error(f"❌ Ошибка при синхронизации {name}: {e}")
        return name, [], {"added": 0, "modified": 0, "copied": 0}

def prepare_results_by_bureau(
    all_results: Dict[str, List[Tuple[str, str, Dict]]],
    all_stats: Dict[str, Dict[str, int]],
    sources: List[Dict]
) -> Tuple[Dict[str, Dict[str, List[Tuple[str, str, Dict]]]], Dict[str, Dict[str, Dict[str, int]]]]:
    results_by_bureau = {}
    stats_by_bureau = {}
    for source in sources:
        name = source.get("name")
        bureau = source.get("buro", "Без бюро")
        if bureau not in results_by_bureau:
            results_by_bureau[bureau] = {}
        results_by_bureau[bureau][name] = all_results.get(name, [])
        if bureau not in stats_by_bureau:
            stats_by_bureau[bureau] = {}
        stats_by_bureau[bureau][name] = all_stats.get(name, {"added": 0, "modified": 0, "copied": 0})
    return results_by_bureau, stats_by_bureau

def start_sync(config_path: str = "config.yaml", dry_run: bool = False) -> None:
    logger.info("🚀 Запуск синхронизации...")
    config = load_config(config_path)
    destination = config.get("destination", {})
    destination_paths = destination.get("paths", [])
    if isinstance(destination_paths, str):
        destination_paths = [destination_paths]
    report_path_root = destination_paths[0] if destination_paths else None
    sources = config.get("sources", [])
    if not destination_paths or not sources:
        logger.error("❌ Конфигурация неполная")
        return

    accessible_sources = []
    delayed_sources = []

    for src in sources:
        if is_source_accessible(src["path"]):
            accessible_sources.append(src)
        else:
            logger.warning(f"⏸️ Источник временно недоступен (отложен): {src['name']}")
            delayed_sources.append(src)

    all_results: Dict[str, List[Tuple[str, str, Dict]]] = {}
    all_stats: Dict[str, Dict[str, int]] = {}

    max_workers = min(20, len(accessible_sources) or 1)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                sync_one_folder_wrapper, src, destination_paths, report_path_root, dry_run
            ): src["name"]
            for src in accessible_sources
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                folder_name, result, stats = future.result()
                all_results[folder_name] = result
                all_stats[folder_name] = stats
                logger.info(f"✅ Готово: {folder_name}")
            except Exception as e:
                logger.error(f"❌ Ошибка в потоке {name}: {e}")

    if delayed_sources:
        logger.info(f"🔁 Повторная попытка для {len(delayed_sources)} недоступных...")
        retry_sources = [src for src in delayed_sources if is_source_accessible(src["path"])]
        with ThreadPoolExecutor(max_workers=min(20, len(retry_sources) or 1)) as executor:
            futures = {
                executor.submit(
                    sync_one_folder_wrapper, src, destination_paths, report_path_root, dry_run
                ): src["name"]
                for src in retry_sources
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    folder_name, result, stats = future.result()
                    all_results[folder_name] = result
                    all_stats[folder_name] = stats
                    logger.info(f"✅ Готово: {folder_name}")
                except Exception as e:
                    logger.error(f"❌ Ошибка в потоке {name}: {e}")

        failed = [src["name"] for src in delayed_sources if src not in retry_sources]
        if failed:
            logger.warning(f"❌ Не удалось подключиться к: {', '.join(failed)}")

    results_by_bureau, stats_by_bureau = prepare_results_by_bureau(all_results, all_stats, sources)
    report_datetime = datetime.now()
    report_path = save_html_report(results_by_bureau, stats_by_bureau, report_datetime)
    logger.info(f"✅ Отчёт сохранён: {report_path}")
    logger.info("✅ Синхронизация завершена (даже при частичных ошибках)")