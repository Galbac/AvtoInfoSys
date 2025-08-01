# app/smb_utils.py
from pathlib import Path
from shutil import copy2
from typing import List, Tuple, Dict
from app.hashing import calculate_hash, get_file_info
from app.logger import get_logger
from app.database import load_state, save_state
from tqdm import tqdm

logger = get_logger()

def list_files(path: Path) -> List[Path]:
    return [f for f in path.rglob("*") if f.is_file()]

def sync_folder(
    name: str,
    source_path: str,
    dest_paths: List[str],
    report_path_root: str,
    dry_run: bool = False
) -> Tuple[List[Tuple[str, str, Dict]], Dict[str, int]]:
    source = Path(source_path)
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
    db[name] = {}  # Очищаем кэш для обновления

    stats = {"added": 0, "modified": 0, "copied": 0}
    changed_files: List[Tuple[str, str, Dict]] = []

    files = list_files(source)
    # 🔹 Убрали logger.info — он мешает tqdm
    # logger.info(f"📁 {name}: найдено {len(files)} файлов для сканирования...")

    # 🔹 Используем tqdm с leave=False, чтобы чистить после себя
    with tqdm(
        total=len(files),
        desc=f"🔄 {name}",
        unit="ф",
        unit_scale=True,
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

                # Проверяем кэш
                cached = source_cache.get(str(relative_path))
                if cached and cached["mtime"] == src_mtime and cached["size"] == src_size:
                    src_hash = cached["hash"]
                else:
                    src_hash = calculate_hash(src_file)

                if not src_hash:
                    pbar.update(1)
                    continue

                # Сохраняем в кэш
                db[name][str(relative_path)] = {
                    "hash": src_hash,
                    "mtime": src_mtime,
                    "size": src_size
                }

                # Проверка назначения
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

    # Сохраняем кэш
    save_state(db)
    logger.info(f"✅ Хеши для '{name}' сохранены немедленно.")
    return changed_files, stats