# app/smb_utils.py
import os
from pathlib import Path
from shutil import copy2
from typing import List, Tuple, Dict
from tqdm import tqdm
from app.database import load_state, save_state
from app.hashing import calculate_hash, get_file_info
from app.logger import get_logger

logger = get_logger()


def make_relative_key(source_root: Path, file_path: Path) -> str:
    """
    Создаёт нормализованный ключ для кэша.
    Использует os.path.relpath для корректной работы с UNC.
    """
    try:
        rel = os.path.relpath(str(file_path), str(source_root))
        return os.path.normpath(rel).replace("\\", "/").lower()
    except Exception as e:
        logger.warning(f"⚠️ Не удалось вычислить относительный путь для {file_path}: {e}")
        # Резервный способ
        try:
            src_str = str(source_root).rstrip("\\/")
            file_str = str(file_path)
            if file_str.lower().startswith(src_str.lower()):
                rel = file_str[len(src_str):].lstrip("\\/")
                return rel.replace("\\", "/").lower()
        except:
            pass
        return "unknown/" + file_path.name


def list_files(path: Path) -> List[Path]:
    """Рекурсивно получает список файлов."""
    if not path.exists():
        return []
    try:
        return [f for f in path.rglob("*") if f.is_file()]
    except Exception as e:
        logger.warning(f"⚠️ Ошибка при сканировании {path}: {e}")
        return []


def sync_folder(
    name: str,
    source_path: str,
    dest_paths: List[str],
    report_path_root: str,
    dry_run: bool = False
) -> Tuple[List[Tuple[str, str, Dict]], Dict[str, int]]:
    """
    Синхронизирует сетевую папку с локальной.
    Исправлено: корректная обработка UNC-путей.
    """
    source = Path(source_path)
    logger.info(f"📁 Источник: {source}")

    if not source.exists():
        logger.warning(f"⚠️ Источник недоступен: {source}")
        return [], {"added": 0, "modified": 0, "copied": 0}

    # 🔹 Нормализуем пути назначения
    dest_dirs = []
    for p in dest_paths:
        # Убираем лишние слеши, нормализуем
        clean_p = str(Path(p.strip()))
        dest_dirs.append(Path(clean_p))

    # 🔹 Путь для отчёта (если нужен)
    if report_path_root:
        report_root = Path(report_path_root) / name
    else:
        report_root = None

    # 🔹 Загружаем кэш
    db = load_state()
    source_cache = db.get(name, {})

    stats = {"added": 0, "modified": 0, "copied": 0}
    changed_files: List[Tuple[str, str, Dict]] = []

    files = list_files(source)
    total_files = len(files)

    with tqdm(
        total=total_files,
        desc=f"🔄 {name}",
        unit="ф",
        ncols=100,
        leave=False,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
    ) as pbar:
        for src_file in files:
            try:
                # ✅ Используем os.path.relpath
                try:
                    rel_path_str = os.path.relpath(str(src_file), str(source))
                    relative_path = Path(rel_path_str)
                except Exception as e:
                    logger.warning(f"⚠️ relpath failed for {src_file}: {e}")
                    pbar.update(1)
                    continue

                # 🔹 Целевые пути: НОРМАЛИЗОВАННЫЕ
                target_files = []
                for d in dest_dirs:
                    try:
                        # Гарантируем, что путь корректный
                        target = d / name / relative_path
                        target_files.append(target)
                    except Exception as e:
                        logger.error(f"❌ Ошибка построения пути назначения: {d} / {name} / {relative_path} | {e}")
                        continue

                main_target = (report_root / relative_path) if report_root else target_files[0] if target_files else None
                if not main_target:
                    pbar.update(1)
                    continue

                src_info = get_file_info(src_file)
                if not src_info:
                    pbar.update(1)
                    continue
                src_mtime, src_size = src_info

                # 🔹 Генерируем ключ для кэша
                cache_key = make_relative_key(source, src_file)
                cached = source_cache.get(cache_key)

                # 🔹 Проверяем по mtime и size (с погрешностью 2 сек)
                if (cached and
                    cached["size"] == src_size and
                    abs(cached["mtime"] - src_mtime) <= 2.0):
                    src_hash = cached["hash"]
                else:
                    src_hash = calculate_hash(src_file)
                    if not src_hash:
                        pbar.update(1)
                        continue

                # 🔹 Обновляем кэш
                if name not in db:
                    db[name] = {}
                db[name][cache_key] = {
                    "hash": src_hash,
                    "mtime": src_mtime,
                    "size": src_size
                }

                # 🔹 Сохраняем кэш каждые 50 файлов
                if len(db[name]) % 50 == 0:
                    save_state(db)

                # 🔹 Копирование
                if not main_target.exists():
                    if not dry_run:
                        for dest_file in target_files:
                            try:
                                # 🔹 Гарантируем, что родительская папка создана
                                dest_file.parent.mkdir(parents=True, exist_ok=True)
                                copy2(src_file, dest_file)
                            except PermissionError as e:
                                logger.error(f"❌ Нет прав на запись: {dest_file} | {e}")
                            except Exception as e:
                                logger.error(f"❌ Ошибка копирования {src_file} → {dest_file}: {e}")
                    stats["added"] += 1
                    stats["copied"] += 1
                    changed_files.append((str(relative_path), "added", {
                        "size": src_size,
                        "mtime": src_mtime
                    }))
                else:
                    old_info = get_file_info(main_target)
                    old_mtime, old_size = old_info if old_info else ("unknown", "unknown")
                    dest_hash = calculate_hash(main_target)
                    if dest_hash and src_hash != dest_hash:
                        if not dry_run:
                            for dest_file in target_files:
                                try:
                                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                                    copy2(src_file, dest_file)
                                except PermissionError as e:
                                    logger.error(f"❌ Нет прав на запись: {dest_file} | {e}")
                                except Exception as e:
                                    logger.error(f"❌ Ошибка обновления {dest_file}: {e}")
                        stats["modified"] += 1
                        stats["copied"] += 1
                        changed_files.append((str(relative_path), "modified", {
                            "size": src_size,
                            "mtime": src_mtime,
                            "old_size": old_size,
                            "old_mtime": old_mtime
                        }))
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке файла {src_file}: {e}")
            finally:
                pbar.update(1)

    # 🔹 Очистка кэша: удаляем записи для удалённых файлов
    current_files = {make_relative_key(source, f) for f in files}
    if name in db:
        stale_keys = [k for k in db[name].keys() if k not in current_files]
        for k in stale_keys:
            del db[name][k]
        if stale_keys:
            logger.debug(f"🗑️ Удалено {len(stale_keys)} устаревших записей из кэша '{name}'")

    # 🔹 Финальное сохранение
    save_state(db)
    logger.info(f"✅ Кэш для '{name}' полностью сохранён.")
    return changed_files, stats