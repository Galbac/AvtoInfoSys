# app/hashing.py
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from app.logger import get_logger

logger = get_logger()

def get_file_info(file_path: Path) -> Optional[Tuple[float, int]]:
    """
    Возвращает (mtime, size) файла.
    """
    try:
        stat = file_path.stat()
        return stat.st_mtime, stat.st_size
    except Exception as e:
        logger.debug(f"⚠️ Не удалось получить метаданные {file_path}: {e}")
        return None

def calculate_hash(file_path: Path) -> Optional[str]:
    """
    Вычисляет SHA-256 хеш файла.
    """
    if not file_path.exists() or not file_path.is_file():
        return None
    hasher = hashlib.sha256()
    try:
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"❌ Ошибка при чтении файла {file_path}: {e}")
        return None