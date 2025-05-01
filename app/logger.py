import logging
from pathlib import Path

LOG_FILE = Path("logs/sync.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_logger(name: str = "sync_logger") -> logging.Logger:
    """
    Создаёт и настраивает логгер с именем name.

    :param name: Имя логгера.
    :return: Настроенный экземпляр логгера.
    """
    logger = logging.getLogger(name)

    if hasattr(logger, "_initialized") and logger._initialized:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handlers = [
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]

    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger._initialized = True  # пользовательский флаг, чтобы не добавлять хендлеры повторно
    return logger
