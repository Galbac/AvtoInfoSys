import json
import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
RECIPIENTS_FILE = BASE_DIR / "users.json"


def load_config(config_path: str = "") -> dict:
    """
    Загружает конфигурацию из YAML-файла.
    Сначала ищет по переданному пути, затем — в стандартных местах.
    """
    search_paths = [Path(config_path)] if config_path else [
        BASE_DIR / "config.yaml",
        BASE_DIR / "config" / "config.yaml"
    ]

    for path in search_paths:
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                print(f"❌ Ошибка при разборе YAML: {e}")
                return {}

    print("❌ Конфигурационный файл config.yaml не найден.")
    return {}


def load_recipients() -> list[int]:
    """Загружает список Telegram ID получателей."""
    if not RECIPIENTS_FILE.exists():
        return []
    try:
        with RECIPIENTS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка при чтении users.json: {e}")
        return []


def save_recipient(user_id: int) -> None:
    """Добавляет Telegram ID получателя в список, если его ещё нет."""
    recipients = load_recipients()
    if user_id not in recipients:
        recipients.append(user_id)
        try:
            with RECIPIENTS_FILE.open("w", encoding="utf-8") as f:
                json.dump(recipients, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"❌ Ошибка при сохранении в users.json: {e}")
