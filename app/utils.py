import json
import os

import yaml
from dotenv import load_dotenv
from pathlib import Path
from app.logger import get_logger

load_dotenv()
logger = get_logger()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATHS = [BASE_DIR / "config.yaml", BASE_DIR / "config" / "config.yaml"]
RECIPIENTS_FILE = BASE_DIR / "users.json"


def load_config(config_path: str = "") -> dict:
    """
    Загружает конфигурацию из YAML-файла.
    Приоритет: переданный путь → config.yaml в BASE_DIR → config/config.yaml.
    """
    search_paths = [Path(config_path)] if config_path else CONFIG_PATHS

    for path in search_paths:
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                    return config
            except yaml.YAMLError as e:
                print(f"❌ Ошибка при разборе YAML-файла: {e}")
                return {}

    print("❌ Конфигурационный файл config.yaml не найден.")
    return {}


def load_recipients() -> list[int]:
    users_file = os.getenv("USERS_FILE", "./users.json")

    try:
        with open(users_file, "r", encoding="utf-8") as f:
            users = json.load(f)

        if not isinstance(users, list) or not all(isinstance(uid, int) for uid in users):
            logger.error(f"❌ Неверный формат файла {users_file}. Ожидается список целых чисел.")
            return []

        return users

    except FileNotFoundError:
        logger.error(f"❌ Файл с пользователями не найден: {users_file}")
    except json.JSONDecodeError:
        logger.error(f"❌ Ошибка разбора JSON в файле: {users_file}")
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка при загрузке пользователей: {e}")

    return []


def save_recipient(user_id: int) -> bool:
    """
    Добавляет Telegram ID в список, если он ещё не добавлен.
    Возвращает True, если пользователь был добавлен.
    """
    recipients = load_recipients()
    if user_id in recipients:
        return False

    recipients.append(user_id)
    try:
        with RECIPIENTS_FILE.open("w", encoding="utf-8") as f:
            json.dump(recipients, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        print(f"❌ Ошибка при сохранении users.json: {e}")
        return False
