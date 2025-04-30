from pathlib import Path
import yaml
from app.logger import get_logger

logger = get_logger()

def load_config(path="config.yaml"):
    """
    Загружает конфигурацию из YAML.
    Пытается найти файл по указанному пути, затем в ./config/config.yaml.
    """
    search_paths = [
        Path(path),
        Path("config") / "config.yaml"
    ]

    for config_path in search_paths:
        if config_path.exists():
            try:
                with config_path.open("r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except yaml.YAMLError as e:
                logger.error(f"❌ Ошибка разбора YAML: {e}")
                return {}

    logger.error("❌ Файл config.yaml не найден.")
    return {}
