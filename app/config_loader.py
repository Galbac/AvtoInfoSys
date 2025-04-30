import os
import yaml
from dotenv import load_dotenv
from app.logger import get_logger

logger = get_logger()

def load_config(path="config.yaml"):
    load_dotenv()  # ← Должен быть до чтения переменных

    if not os.path.exists(path):
        logger.error(f"Файл конфигурации {path} не найден.")
        raise FileNotFoundError(f"Файл конфигурации {path} не найден.")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("ADMIN_CHAT_ID")

    if not bot_token or not chat_id:
        logger.error("В .env отсутствуют настройки Telegram.")
        raise ValueError("Отсутствуют BOT_TOKEN или ADMIN_CHAT_ID в .env.")

    config["telegram"] = {
        "bot_token": bot_token,
        "chat_id": chat_id
    }

    folders = []
    shared_folders = config.get("shared_folders", {})
    destination_root = config.get("destination_root", "./synced")

    for name, source in shared_folders.items():
        destination = os.path.join(destination_root, name)
        folders.append({
            "name": name,
            "source": source,
            "destination": destination
        })

    config["folders"] = folders
    return config