# config_loader.py
import yaml
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Подгружаем из окружения, если отсутствуют
    config["BOT_TOKEN"] = config.get("BOT_TOKEN") or os.getenv("BOT_TOKEN")
    config["ADMIN_CHAT_ID"] = config.get("ADMIN_CHAT_ID") or os.getenv("ADMIN_CHAT_ID")

    return config

# Логгер
log_path = os.path.join(os.path.dirname(__file__), "..", "sync.log")
os.makedirs(os.path.dirname(log_path), exist_ok=True)

logger = logging.getLogger("sync_logger")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")

file_handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8")
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
