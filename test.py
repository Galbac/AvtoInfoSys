try:
    with open(r"\\desktop-hshsuuu\Работа\Разное\тест 2.txt", "r", encoding="utf-8") as f:
        print(f.read())
except Exception as e:
    print(f"Ошибка чтения: {e}")

from pathlib import Path

test_path = r"\\Abakarov_m\РАБОТА\ЦЕХ-18\Пуансон_1601_6319_5\02\Деталь02.stc"
p = Path(test_path)

print(f"Путь: {p}")
print(f"Существует: {p.exists()}")
print(f"Размер: {p.stat().st_size if p.exists() else '—'}")

try:
    with open(p, "rb") as f:
        print("Первые 10 байт:", f.read(10))
except PermissionError as e:
    print("Ошибка доступа:", e)
except Exception as e:
    print("Другая ошибка:", e)

# migrate_json_to_sqlite.py
import json
import sqlite3
from pathlib import Path

# Пути
JSON_FILE = Path("synced_db.json")
SQLITE_FILE = Path("synced_db.sqlite3")

# Проверка наличия файлов
if not JSON_FILE.exists():
    print(f"❌ Файл {JSON_FILE} не найден.")
    exit(1)

# Читаем JSON
print(f"🔄 Чтение {JSON_FILE}...")
try:
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✅ Успешно загружено {len(data)} источников")
except Exception as e:
    print(f"❌ Ошибка чтения JSON: {e}")
    exit(1)

# Подключаемся к SQLite (создастся, если нет)
print(f"🔄 Подключение к {SQLITE_FILE}...")
conn = sqlite3.connect(SQLITE_FILE)

# Настройка для производительности
conn.execute("PRAGMA journal_mode = WAL")
conn.execute("PRAGMA synchronous = NORMAL")
conn.execute("PRAGMA cache_size = 10000")

# Создаём таблицу, если не существует
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
print("✅ Таблица file_cache готова")

# Собираем все записи
all_records = []
for source_name, files in data.items():
    for file_key, info in files.items():
        all_records.append((
            source_name,
            file_key,
            info.get("hash"),
            info.get("mtime"),
            info.get("size")
        ))

# Удаляем старые данные из тех же источников
sources = list(data.keys())
if sources:
    placeholders = ",".join(["?" for _ in sources])
    conn.execute(f"DELETE FROM file_cache WHERE source_name IN ({placeholders})", sources)

# Вставляем новые
conn.executemany("""
    INSERT INTO file_cache (source_name, file_key, hash, mtime, size)
    VALUES (?, ?, ?, ?, ?)
""", all_records)

conn.commit()
conn.close()

# Финал
size_mb = SQLITE_FILE.stat().st_size / (1024 * 1024)
print(f"✅ Успешно перенесено {len(all_records)} записей")
print(f"📊 Новый размер базы: {size_mb:.2f} MB")
print(f"🎉 Миграция завершена: {JSON_FILE} → {SQLITE_FILE}")
