#database.py
import json

from pathlib import Path

DB_FILE = Path("synced_db.json")


def is_file_already_synced(ip, filename, filehash):
    if not DB_FILE.exists():
        return False
    with open(DB_FILE) as f:
        db = json.load(f)
    return db.get(ip, {}).get(filename) == filehash


def save_file_record(ip, filename, filehash):
    db = {}
    if DB_FILE.exists():
        with open(DB_FILE) as f:
            db = json.load(f)

    # Отложенный импорт logger

    db.setdefault(ip, {})[filename] = filehash
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)
