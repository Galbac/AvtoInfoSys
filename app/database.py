import json
from pathlib import Path
from typing import Dict

DB_FILE = Path("synced_db.json")


def load_state() -> Dict[str, Dict[str, str]]:
    """
    Загружает состояние синхронизированных файлов из JSON-файла.

    :return: Словарь вида {папка: {путь_файла: хеш}}.
    """
    if not DB_FILE.exists():
        return {}

    try:
        with DB_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            else:
                print(f"[WARN] Неверный формат данных в {DB_FILE}, ожидается словарь.")
                return {}
    except (json.JSONDecodeError, OSError) as e:
        print(f"[WARN] Не удалось загрузить состояние из {DB_FILE}: {e}")
        return {}


def save_state(data: Dict[str, Dict[str, str]]) -> None:
    """
    Сохраняет текущее состояние синхронизированных файлов в JSON-файл.

    :param data: Словарь вида {папка: {путь_файла: хеш}}.
    """
    try:
        with DB_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[ERROR] Не удалось сохранить состояние в {DB_FILE}: {e}")
