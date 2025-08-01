# app/database.py
import json
from pathlib import Path
from typing import Dict, Any
from app.logger import get_logger

logger = get_logger()
DB_FILE = Path("synced_db.json")

def load_state() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Загружает состояние: {source_name: {relative_path: {hash, mtime, size}}}
    """
    if not DB_FILE.exists():
        logger.info(f"ℹ️ Файл состояния не найден: {DB_FILE}, возвращаем пустой словарь.")
        return {}
    try:
        with DB_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            else:
                logger.warning(f"⚠️ Неверный формат данных в {DB_FILE}")
                return {}
    except Exception as e:
        logger.warning(f"⚠️ Не удалось загрузить состояние: {e}")
        return {}

def save_state(data: Dict[str, Dict[str, Any]]) -> None:
    """
    Сохраняет состояние синхронизации.
    """
    try:
        with DB_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Состояние сохранено в {DB_FILE}")
    except Exception as e:
        logger.error(f"❌ Не удалось сохранить состояние: {e}")