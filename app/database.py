import json
import os
from typing import Dict

DB_FILE = "synced_db.json"

def load_state() -> Dict[str, Dict[str, str]]:
    """Загрузить состояние синхронизированных файлов из JSON."""
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(data: Dict[str, Dict[str, str]]):
    """Сохранить состояние синхронизированных файлов в JSON."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
