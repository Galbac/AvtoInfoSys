# app/database.py
import sqlite3
import threading
from pathlib import Path
from typing import Dict, Any
from app.logger import get_logger

logger = get_logger()

DB_FILE = Path("synced_db.sqlite3")
_save_lock = threading.Lock()
_initialized = False  # Защита от повторной инициализации

def init_db():
    """Создаёт таблицу, если не существует. Вызывается один раз."""
    global _initialized
    if _initialized:
        return
    with _save_lock:
        if _initialized:  # Двойная проверка
            return
        try:
            conn = sqlite3.connect(DB_FILE)
            # Оптимизация производительности
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")
            conn.execute("PRAGMA temp_store = MEMORY")
            conn.execute("PRAGMA foreign_keys = ON")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_cache (
                    source_name TEXT NOT NULL,
                    file_key TEXT NOT NULL,
                    hash TEXT,
                    mtime REAL,
                    size INTEGER,
                    PRIMARY KEY (source_name, file_key)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON file_cache(source_name)")
            conn.commit()
            conn.close()
            logger.info(f"✅ База данных инициализирована: {DB_FILE}")
            _initialized = True
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы: {e}")

def load_state() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Загружает состояние из SQLite."""
    if not DB_FILE.exists():
        logger.info("ℹ️ База данных не найдена. Создаём новую...")
        init_db()
        return {}

    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT source_name, file_key, hash, mtime, size FROM file_cache")
        rows = cursor.fetchall()
        conn.close()

        data = {}
        for row in rows:
            source = row["source_name"]
            if source not in data:
                data[source] = {}
            data[source][row["file_key"]] = {
                "hash": row["hash"],
                "mtime": row["mtime"],
                "size": row["size"]
            }

        logger.info(f"✅ Состояние загружено из SQLite | Записей: {len(rows)}")
        return data

    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке состояния: {e}")
        return {}

def save_state(data: Dict[str, Dict[str, Any]]) -> None:
    """Сохраняет состояние в SQLite с использованием executemany."""
    with _save_lock:
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Подготавливаем данные
            all_data = []
            for source_name, files in data.items():
                cursor.execute("DELETE FROM file_cache WHERE source_name = ?", (source_name,))
                for file_key, info in files.items():
                    all_data.append((
                        source_name,
                        file_key,
                        info.get("hash"),
                        info.get("mtime"),
                        info.get("size")
                    ))

            # Массовая вставка
            cursor.executemany("""
                INSERT INTO file_cache (source_name, file_key, hash, mtime, size)
                VALUES (?, ?, ?, ?, ?)
            """, all_data)

            conn.commit()
            conn.close()

            # Логируем размер
            if DB_FILE.exists():
                size_mb = DB_FILE.stat().st_size / (1024 * 1024)
                logger.info(f"✅ Состояние сохранено | Размер БД: {size_mb:.2f} MB")

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения состояния: {e}")