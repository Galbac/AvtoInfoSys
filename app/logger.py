import logging
from pathlib import Path

LOG_FILE = Path("logs/sync.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "sync_logger") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
