# app/sync_core.py

import os
import shutil
from pathlib import Path
from typing import Dict
from app.config_loader import load_config
from app.database import load_state, save_state
from app.hashing import calculate_file_hash
from app.logger import get_logger
from app.reporter import generate_html_report
from app.telegram_notify import send_report_file_to_telegram

logger = get_logger()

def sync_folder(source: str, destination: str, previous_state: Dict[str, str], dry_run: bool = False) -> Dict[str, str]:
    changes = {}

    for root, _, files in os.walk(source):
        for file in files:
            source_path = os.path.join(root, file)
            rel_path = os.path.relpath(source_path, source)
            dest_path = os.path.join(destination, rel_path)

            try:
                current_hash = calculate_file_hash(source_path)
            except Exception as e:
                logger.warning(f"❌ Пропущен (ошибка хеша): {source_path} — {e}")
                continue

            if previous_state.get(rel_path) != current_hash:
                changes[rel_path] = current_hash

                if not dry_run:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    try:
                        shutil.copy2(source_path, dest_path)
                        logger.info(f"✅ Скопировано: {source_path} → {dest_path}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка копирования {source_path}: {e}")
                else:
                    logger.info(f"[Dry-run] Обнаружено изменение: {source_path}")

    return changes

def start_sync(config_path="config.yaml", dry_run=False):
    logger.info("🚀 Начинаем синхронизацию...")

    config = load_config(config_path)
    previous_state = load_state()

    all_results = {}
    new_state = {}

    destination_root = Path(config.get("destination_root", "./synced"))

    for name, source in config.get("shared_folders", {}).items():
        destination = destination_root / name
        logger.info(f"🔍 Сканируем папку: {name}")
        changes = sync_folder(source, str(destination), previous_state.get(name, {}), dry_run)
        all_results[name] = changes
        new_state[name] = {**previous_state.get(name, {}), **changes}

    if not dry_run:
        save_state(new_state)

    report_path = generate_html_report(all_results, dry_run)

    if report_path:
        send_report_file_to_telegram(report_path)

    logger.info("✅ Синхронизация завершена")
