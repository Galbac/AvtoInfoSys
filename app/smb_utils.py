# app/smb_utils.py

from pathlib import Path
from shutil import copy2
from app.hashing import calculate_hash
from app.logger import get_logger

logger = get_logger()


def list_files(path):
    return [f for f in Path(path).rglob("*") if f.is_file()]


def sync_folder(name, source_path, dest_root, dry_run=False):
    source = Path(source_path)
    destination = Path(dest_root) / name

    added = modified = copied = 0
    changed_files = []

    for src_file in list_files(source):
        relative_path = src_file.relative_to(source)
        dest_file = destination / relative_path

        if not dest_file.exists():
            if not dry_run:
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                copy2(src_file, dest_file)
            added += 1
            copied += 1
            changed_files.append(str(relative_path))
        else:
            src_hash = calculate_hash(src_file)
            dest_hash = calculate_hash(dest_file)
            if src_hash != dest_hash:
                if not dry_run:
                    copy2(src_file, dest_file)
                modified += 1
                copied += 1
                changed_files.append(str(relative_path))

    stats = {
        "added": added,
        "modified": modified,
        "copied": copied
    }

    return changed_files, stats
