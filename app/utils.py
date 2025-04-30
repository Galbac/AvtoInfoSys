# app/utils.py

import json
import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

RECIPIENTS_FILE = "users.json"


def load_config():
    """
    Загружает конфигурацию из YAML файла.
    Ищет сначала в корне проекта, потом в папке ./config.
    """
    base_dir = Path(__file__).resolve().parent.parent  # корень проекта
    possible_paths = [
        base_dir / "config.yaml",
        base_dir / "config" / "config.yaml"
    ]

    for config_path in possible_paths:
        if config_path.exists():
            try:
                with config_path.open("r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"Ошибка при разборе YAML: {e}")
                return {}

    print("❌ Ошибка: config.yaml не найден.")
    return {}


def load_recipients():
    """Загружает список получателей из файла."""
    if not os.path.exists(RECIPIENTS_FILE):
        return []
    try:
        with open(RECIPIENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Ошибка при чтении списка получателей: {e}")
        return []


def save_recipient(user_id: int):
    """Сохраняет нового получателя в файл, если его ещё нет в списке."""
    recipients = load_recipients()
    if user_id not in recipients:
        recipients.append(user_id)
        try:
            with open(RECIPIENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(recipients, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка при сохранении получателя: {e}")
