from pathlib import Path
from shutil import copy2
from typing import List, Tuple, Dict
from app.hashing import calculate_hash
from app.logger import get_logger

logger = get_logger()


def list_files(path: Path) -> List[Path]:
    """
    Рекурсивно возвращает список всех файлов в указанной директории.
    """
    return [f for f in path.rglob("*") if f.is_file()]


def sync_folder(
    name: str,
    source_path: str,
    dest_root: str,
    dry_run: bool = False
) -> Tuple[List[Tuple[str, str]], Dict[str, int]]:
    """
    Синхронизирует одну локально смонтированную сетевую папку с локальной директорией.

    :param name: Название группы/пользователя (используется как подпапка)
    :param source_path: Путь к исходной (сетевой) папке
    :param dest_root: Корневая папка назначения
    :param dry_run: Только логика без копирования (режим симуляции)
    :return: (список изменённых файлов с пометками, статистика по операциям)
    """
    source = Path(source_path)
    destination = Path(dest_root) / name

    if not source.exists():
        logger.warning(f"⚠️ Источник не найден: {source}")
        return [], {"added": 0, "modified": 0, "copied": 0}

    stats = {"added": 0, "modified": 0, "copied": 0}
    changed_files: List[Tuple[str, str]] = []

    for src_file in list_files(source):
        try:
            relative_path = src_file.relative_to(source)
            dest_file = destination / relative_path

            if not dest_file.exists():
                if not dry_run:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    copy2(src_file, dest_file)
                stats["added"] += 1
                stats["copied"] += 1
                changed_files.append((str(relative_path), "added"))
                logger.debug(f"➕ Добавлен: {relative_path}")
            else:
                src_hash = calculate_hash(src_file)
                dest_hash = calculate_hash(dest_file)

                if src_hash and dest_hash and src_hash != dest_hash:
                    if not dry_run:
                        copy2(src_file, dest_file)
                    stats["modified"] += 1
                    stats["copied"] += 1
                    changed_files.append((str(relative_path), "modified"))
                    logger.debug(f"✏️ Обновлен: {relative_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке файла {src_file}: {e}")

    return changed_files, stats
