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
    try:
        rel = file_path.relative_to(source_root)
    except ValueError:
        # Унифицируем части пути
        source_parts = [p.lower().strip("\\/") for p in source_root.parts]
        file_parts = [p.lower().strip("\\/") for p in file_path.parts]
        # Удаляем общий префикс
        min_len = min(len(source_parts), len(file_parts))
        i = 0
        while i < min_len and source_parts[i] == file_parts[i]:
            i += 1
        if i > 0:
            rel = Path(*file_parts[i:])
        else:
            rel = Path(*file_parts[1:])  # убираем \\host
    return os.path.normpath(str(rel)).replace("\\", "/").lower()



def list_files(path: Path) -> List[Path]:
    """Рекурсивно получает список файлов."""
    return [f for f in path.rglob("*") if f.is_file()]


def sync_folder(
        name: str,
        source_path: str,
        dest_paths: List[str],
        report_path_root: str,
        dry_run: bool = False
) -> Tuple[List[Tuple[str, str, Dict]], Dict[str, int]]:
    source = Path(source_path)
    logger.info(f"📁 Источник: {source} | Путь: {source.resolve() if source.exists() else source}")
    if not source.exists():
        logger.warning(f"⚠️ Источник недоступен (пропускаем): {source}")
        return [], {"added": 0, "modified": 0, "copied": 0}

    if report_path_root:
        report_root = Path(report_path_root) / name
    else:
        report_root = None

    dest_dirs = [Path(p) / name for p in dest_paths]

    # Загружаем кэш
    db = load_state()
    source_cache = db.get(name, {})
    stats = {"added": 0, "modified": 0, "copied": 0}
    changed_files: List[Tuple[str, str, Dict]] = []
    files = list_files(source)

    processed_count = 0
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
                relative_path = src_file.relative_to(source)
                target_files = [d / relative_path for d in dest_dirs]
                main_target = report_root / relative_path if report_root else target_files[0]
                src_info = get_file_info(src_file)
                if not src_info:
                    pbar.update(1)
                    continue
                src_mtime, src_size = src_info

                # 🔹 ЕДИНСТВЕННЫЙ ключ — везде используется make_relative_key
                rel_path_str = make_relative_key(source, src_file)
                cached = source_cache.get(rel_path_str)

                # 🔹 Проверка: размер + mtime с погрешностью 5 секунд
                if (cached and
                        cached["size"] == src_size and
                        abs(cached["mtime"] - src_mtime) <= 5.0):
                    src_hash = cached["hash"]
                else:
                    src_hash = calculate_hash(src_file)
                    if not src_hash:
                        pbar.update(1)
                        continue

                # 🔥 Обновляем кэш
                if name not in db:
                    db[name] = {}
                db[name][rel_path_str] = {
                    "hash": src_hash,
                    "mtime": src_mtime,
                    "size": src_size
                }
                logger.debug(f"🔑 Ключ добавлен: {rel_path_str} | Файл: {src_file}")

                # 🔥 Сохраняем каждые 50 файлов
                processed_count += 1
                if processed_count % 50 == 0:
                    save_state(db)
                    logger.debug(f"💾 Сохранён кэш после {processed_count} файлов в '{name}'")

                # 🔹 Проверка назначения
                if not main_target.exists():
                    if not dry_run:
                        for dest_file in target_files:
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            copy2(src_file, dest_file)
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
                                copy2(src_file, dest_file)
                        stats["modified"] += 1
                        stats["copied"] += 1
                        changed_files.append((str(relative_path), "modified", {
                            "size": src_size,
                            "mtime": src_mtime,
                            "old_size": old_size,
                            "old_mtime": old_mtime
                        }))
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке {src_file}: {e}")
            finally:
                pbar.update(1)

    # 🔹 ОЧИСТКА: используем ТУ ЖЕ функцию make_relative_key!
    current_files = {make_relative_key(source, f) for f in files}
    logger.debug(f"🔍 Текущие файлы (ключи): {len(current_files)}")
    for cf in sorted(current_files):
        logger.debug(f"  📄 {cf}")

    if name in db:
        for old_file in list(db[name].keys()):
            if old_file not in current_files:
                logger.warning(f"🗑️ Удалён из кэша: '{old_file}' (не найден в текущих)")
                del db[name][old_file]
    if name in db:
        total = len(db[name])
        unique = len(set(db[name].keys()))
        if total != unique:
            logger.warning(f"⚠️ Найдены дубли ключей в '{name}': {total - unique} дублей")

    # 🔹 Финальное сохранение
    save_state(db)
    logger.info(f"✅ Кэш для '{name}' полностью сохранён.")
    return changed_files, stats
