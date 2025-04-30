# app/smb_utils.py

# app/smb_utils.py

from pathlib import Path
from shutil import copy2
from typing import List, Tuple, Dict
from app.hashing import calculate_hash
from app.logger import get_logger

logger = get_logger()


def list_files(path: Path) -> List[Path]:
    """Возвращает список всех файлов в указанной директории (рекурсивно)."""
    return [f for f in path.rglob("*") if f.is_file()]


def sync_folder(
        name: str,
        source_path: str,
        dest_root: str,
        dry_run: bool = False
) -> Tuple[List[str], Dict[str, int]]:
    """
    Синхронизирует одну сетевую папку с локальным каталогом назначения.

    :param name: Название папки (например, имя пользователя)
    :param source_path: Сетевой путь к исходной папке
    :param dest_root: Корневая папка назначения
    :param dry_run: Если True — ничего не копируется, только логика
    :return: Список изменённых файлов и статистика
    """
    source = Path(source_path)
    destination = Path(dest_root) / name

    if not source.exists():
        logger.warning(f"⚠️ Источник не найден: {source}")
        return [], {"added": 0, "modified": 0, "copied": 0}

    added = modified = copied = 0
    changed_files = []

    for src_file in list_files(source):
        relative_path = src_file.relative_to(source)
        dest_file = destination / relative_path

        try:
            if not dest_file.exists():
                if not dry_run:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    copy2(src_file, dest_file)
                added += 1
                copied += 1
                changed_files.append(str(relative_path))
                logger.debug(f"➕ Добавлен: {relative_path}")
            else:
                src_hash = calculate_hash(src_file)
                dest_hash = calculate_hash(dest_file)
                if src_hash != dest_hash:
                    if not dry_run:
                        copy2(src_file, dest_file)
                    modified += 1
                    copied += 1
                    changed_files.append(str(relative_path))
                    logger.debug(f"✏️ Обновлен: {relative_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке {relative_path}: {e}")

    stats = {
        "added": added,
        "modified": modified,
        "copied": copied,
    }

    return changed_files, stats
