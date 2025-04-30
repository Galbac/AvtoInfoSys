#logger.py
import logging
from logging.handlers import RotatingFileHandler
import os
import json
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

LOG_FILE = os.getenv("LOG_FILE", "logs/sync.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Создание директории для логов
LOG_DIR = os.path.dirname(LOG_FILE)
if LOG_DIR and not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Кастомный JSON-форматтер
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
        }
        return json.dumps(log_record, ensure_ascii=False)

def get_logger(name: str = "sync_logger") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # JSON форматтер
    formatter = JsonFormatter()

    # Консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Файл с ротацией
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
