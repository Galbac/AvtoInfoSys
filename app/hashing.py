import hashlib
from pathlib import Path


def calculate_hash(file_path: Path) -> str:
    """
    Вычисляет SHA-256 хеш файла.

    :param file_path: Путь к файлу
    :return: Хеш строки в формате hex
    :raises FileNotFoundError: если файл не существует
    :raises RuntimeError: если возникает ошибка при чтении
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    hash_func = hashlib.sha256()
    try:
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Ошибка при чтении файла {file_path}: {e}")


# Совместимость со старым кодом
compute_file_hash = calculate_hash
