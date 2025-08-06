# app/database.py
import json
import threading
import copy
from pathlib import Path
from typing import Dict, Any
from app.logger import get_logger

logger = get_logger()

DB_FILE = Path("synced_db.json")
_save_lock = threading.Lock()  # Защита от параллельной записи


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
    Потокобезопасно: только один поток может писать в файл.
    Использует временный файл для атомарной записи.
    """
    with _save_lock:
        temp_file = DB_FILE.with_suffix(".json.tmp")
        try:
            # Создаём глубокую копию, чтобы избежать изменений во время dump
            safe_data = copy.deepcopy(data)

            # Записываем во временный файл
            with temp_file.open("w", encoding="utf-8") as f:
                json.dump(safe_data, f, ensure_ascii=False, indent=2)

            # Атомарная замена: удаляем старый, переименовываем новый
            if DB_FILE.exists():
                DB_FILE.unlink()
            temp_file.rename(DB_FILE)

            # Логируем размер
            size_kb = DB_FILE.stat().st_size / 1024
            logger.info(f"✅ Состояние сохранено в {DB_FILE} | Размер: {size_kb:.1f} KB")

        except Exception as e:
            logger.error(f"❌ Не удалось сохранить состояние: {e}")
            if temp_file.exists():
                temp_file.unlink()