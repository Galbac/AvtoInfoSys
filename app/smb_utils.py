#smb_utils.py
from pathlib import Path
from shutil import copy2


def list_files(path):
    return [f for f in Path(path).rglob("*") if f.is_file()]


def download_file(src, dest_dir):
    dest_dir.mkdir(parents=True, exist_ok=True)
    copy2(src, dest_dir / src.name)
