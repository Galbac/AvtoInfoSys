import hashlib
from pathlib import Path
from typing import Optional
from app.logger import get_logger

logger = get_logger()


def calculate_hash(file_path: Path) -> Optional[str]:
    """
    Безопасно вычисляет SHA-256 хеш файла.

    :param file_path: Путь к файлу
    :return: Хеш в hex-строке или None, если ошибка
    """
    if not file_path.exists():
        logger.warning(f"⚠️ Файл не найден: {file_path}")
        return None
    if not file_path.is_file():
        logger.warning(f"⚠️ Не файл (пропущен): {file_path}")
        return None

    hasher = hashlib.sha256()

    try:
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        hash_hex = hasher.hexdigest()
        logger.debug(f"✅ Вычислен хеш для {file_path}: {hash_hex}")
        return hash_hex
    except Exception as e:
        logger.error(f"❌ Ошибка при чтении файла {file_path}: {e}")
        return None


# Обратная совместимость
compute_file_hash = calculate_hash
