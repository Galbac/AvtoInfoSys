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
    if not file_path.is_file():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    hasher = hashlib.sha256()

    try:
        with file_path.open("rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    except OSError as e:
        raise RuntimeError(f"Ошибка при чтении файла '{file_path}': {e}") from e


# Обратная совместимость
compute_file_hash = calculate_hash
