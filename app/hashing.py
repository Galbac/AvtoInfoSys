#hashing.py
import hashlib

import os

def calculate_file_hash(file_path):
    """Вычисление хеша файла с использованием SHA-256."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден.")

    hash_func = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Ошибка при вычислении хеша для файла {file_path}: {e}")
