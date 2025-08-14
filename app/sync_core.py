# app/sync_core.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Set
from app.logger import get_logger
from app.config_loader import load_config
from app.reporter import save_html_report

logger = get_logger()

# Глобальные переменные
_successful_sources: Set[str] = set()
_sync_results: Dict[str, List[Tuple[str, str, Dict]]] = {}
_sync_stats: Dict[str, Dict[str, int]] = {}
_dest_paths: List[str] = []
_report_root: str = ""
_dry_run: bool = False
_lock = threading.Lock()

# Управление фоновым потоком
_monitor_active = False
_monitor_thread: threading.Thread | None = None


def can_ping(host: str) -> bool:
    """Проверяет доступность хоста через ping."""
    import subprocess
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "1000", host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception:
        return False


def is_source_accessible(path: str) -> bool:
    """Проверяет доступность источника: ping + exists."""
    try:
        if path.startswith("\\\\"):
            parts = path.split("\\")
            if len(parts) > 2:
                host = parts[2]
                if not can_ping(host):
                    return False
            else:
                return False
        return Path(path).exists()
    except Exception:
        return False


def sync_one_folder_wrapper(source: dict) -> Tuple[str, List[Tuple[str, str, Dict]], Dict[str, int]]:
    """Обёртка для выполнения в потоке."""
    name = source["name"]
    path = source["path"]
    logger.info(f"🔍 Попытка синхронизировать: {name} ({path})")
    try:
        from app.smb_utils import sync_folder
        result, stats = sync_folder(name, path, _dest_paths, _report_root, _dry_run)
        return name, result, stats
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при синхронизации {name}: {e}")
        return name, [], {"added": 0, "modified": 0, "copied": 0}


def prepare_results_by_bureau(
    all_results: Dict[str, List[Tuple[str, str, Dict]]],
    all_stats: Dict[str, Dict[str, int]],
    sources: List[dict]
) -> Tuple[Dict, Dict]:
    """Группирует результаты по бюро."""
    results_by_bureau = {}
    stats_by_bureau = {}
    for source in sources:
        name = source["name"]
        buro = source.get("buro", "Без бюро")
        results_by_bureau.setdefault(buro, {})[name] = all_results.get(name, [])
        stats_by_bureau.setdefault(buro, {})[name] = all_stats.get(name, {
            "added": 0, "modified": 0, "copied": 0
        })
    return results_by_bureau, stats_by_bureau


def background_monitor(sources: List[dict], interval: float = 2.0) -> None:
    """
    🔁 Фоновый мониторинг: проверяет недоступные источники КАЖДЫЕ 2 СЕКУНДЫ.
    Как только источник стал доступен — сразу синхронизирует.
    Работает параллельно с основной синхронизацией.
    """
    global _successful_sources, _monitor_active, _sync_results, _sync_stats
    logger.info(f"🔁 Фоновый мониторинг запущен: проверка каждые {interval:.1f} секунд...")

    while _monitor_active:
        time.sleep(interval)
        if not _monitor_active:
            break

        candidates = []
        with _lock:
            for src in sources:
                if src["name"] not in _successful_sources and is_source_accessible(src["path"]):
                    candidates.append(src)

        if not candidates:
            continue

        logger.info(f"🔁 Мгновенная синхронизация: найдено {len(candidates)} доступных источников")
        max_workers = min(5, len(candidates))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(sync_one_folder_wrapper, src): src["name"]
                for src in candidates
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    folder_name, result, stats = future.result()
                    with _lock:
                        _sync_results[folder_name] = result
                        _sync_stats[folder_name] = stats
                        _successful_sources.add(folder_name)
                    logger.info(f"✅ Мгновенно синхронизировано: {folder_name}")
                except Exception as e:
                    logger.error(f"❌ Ошибка в фоне {name}: {e}")

    logger.info("✅ Фоновый мониторинг остановлен.")


def start_sync(config_path: str = "config.yaml", dry_run: bool = False) -> None:
    """
    Главная функция.
    - Запускает фоновый мониторинг СРАЗУ
    - Основная синхронизация работает параллельно
    - Фон проверяет каждые 2 секунды
    - Отчёт — в конце
    """
    global _successful_sources, _sync_results, _sync_stats
    global _dest_paths, _report_root, _dry_run, _monitor_active, _monitor_thread

    # Сброс состояния
    _successful_sources = set()
    _sync_results = {}
    _sync_stats = {}
    _dry_run = dry_run
    _monitor_active = False
    _monitor_thread = None

    logger.info("🚀 Запуск синхронизации...")
    start_time = time.time()

    # Загрузка конфига
    config = load_config(config_path)
    if not config:
        logger.error("❌ Конфиг не загружен — формируем пустой отчёт")
        sources = []
    else:
        sources = config.get("sources", [])
        if not sources:
            logger.warning("⚠️ Список источников пуст")
        else:
            logger.info(f"📋 Найдено источников: {len(sources)}")

    # Пути назначения
    destination = config.get("destination", {}) if config else {}
    dest_paths = destination.get("paths", [])
    if isinstance(dest_paths, str):
        dest_paths = [dest_paths]
    _dest_paths = dest_paths
    _report_root = dest_paths[0] if dest_paths else ""

    # 1. Проверка доступности
    accessible_sources = []
    delayed_sources = []

    for src in sources:
        if is_source_accessible(src["path"]):
            accessible_sources.append(src)
        else:
            logger.warning(f"⏸️ Источник недоступен: {src['name']} → {src['path']}")
            delayed_sources.append(src)

    # Запускаем фоновый мониторинг ДО основной синхронизации
    expected_total = len(sources)
    if delayed_sources:
        _monitor_active = True
        _monitor_thread = threading.Thread(
            target=background_monitor,
            args=(sources, 2.0),
            daemon=True
        )
        _monitor_thread.start()
        logger.info(f"🔁 Фоновый мониторинг запущен: будет проверять каждые 2 секунды. Ожидаем {len(delayed_sources)} источников.")
    else:
        logger.info("✅ Все источники доступны. Фоновый мониторинг не нужен.")

    # 2. Основная синхронизация доступных источников
    if accessible_sources:
        max_workers = min(20, len(accessible_sources))
        logger.info(f"🔄 Синхронизируем {len(accessible_sources)} источников...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(sync_one_folder_wrapper, src): src["name"]
                for src in accessible_sources
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    folder_name, result, stats = future.result()
                    _sync_results[folder_name] = result
                    _sync_stats[folder_name] = stats
                    _successful_sources.add(folder_name)
                    logger.info(f"✅ Успешно: {folder_name}")
                except Exception as e:
                    logger.error(f"❌ Ошибка в потоке {name}: {e}")
    else:
        logger.info("✅ Нет доступных источников для синхронизации.")

    # 3. Умное ожидание: ждём, пока фон найдёт оставшиеся, но не бесконечно
    elapsed = time.time() - start_time
    wait_time = max(60.0 - elapsed, 5.0)  # минимум 5 секунд ожидания
    check_interval = 0.5
    checks_without_progress = 0
    last_count = len(_successful_sources)

    logger.info(f"⏱️ Ожидание появления недоступных источников: {wait_time:.1f} сек...")

    # Ждём, но с отслеживанием прогресса
    for _ in range(int(wait_time / check_interval)):
        time.sleep(check_interval)
        current_count = len(_successful_sources)
        if current_count > last_count:
            checks_without_progress = 0  # был прогресс
            last_count = current_count
            logger.debug(f"🟢 Прогресс: синхронизировано {_successful_sources}")
        else:
            checks_without_progress += 1

        # Если уже все синхронизированы — выходим
        if current_count >= expected_total:
            logger.info("✅ Все источники синхронизированы.")
            break

        # Если 10 секунд без прогресса — прекращаем
        if checks_without_progress >= (10.0 / check_interval):
            logger.warning(f"🛑 Прекращаем ожидание: нет прогресса более 10 секунд. Успешно: {current_count}/{expected_total}")
            break
    else:
        logger.info(f"⏳ Время ожидания исчерпано. Успешно синхронизировано: {len(_successful_sources)}/{expected_total}")

    # 4. Останавливаем фоновый мониторинг
    if _monitor_active:
        _monitor_active = False
        if _monitor_thread and _monitor_thread.is_alive():
            _monitor_thread.join(timeout=2)
        logger.info("✅ Фоновый мониторинг остановлен.")
    else:
        logger.info("✅ Фоновый мониторинг не был запущен.")

    # 5. Формирование отчёта
    results_by_bureau, stats_by_bureau = prepare_results_by_bureau(_sync_results, _sync_stats, sources)
    try:
        report_path = save_html_report(results_by_bureau, stats_by_bureau, datetime.now())
        logger.info(f"📄 ОТЧЁТ СФОРМИРОВАН: {report_path}")
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации отчёта: {e}")
        logger.exception(e)

    logger.info("✅ Синхронизация завершена.")