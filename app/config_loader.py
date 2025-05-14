import yaml
from pathlib import Path
from typing import Any, Dict

from app.utils import CONFIG_PATHS


class ConfigError(Exception):
    """Исключение, выбрасываемое при ошибках конфигурации."""
    pass


def load_config(config_path: str = "") -> dict:
    search_paths = [Path(config_path)] if config_path else CONFIG_PATHS

    for path in search_paths:
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                    # Совместимость: если указана только одна папка
                    if "destination" in config:
                        dest = config["destination"]
                        if "path" in dest and "paths" not in dest:
                            dest["paths"] = [dest["path"]]
                    return config
            except yaml.YAMLError as e:
                print(f"❌ Ошибка при разборе YAML-файла: {e}")
                return {}

    print("❌ Конфигурационный файл config.yaml не найден.")
    return {}



def validate_config(config: Dict[str, Any]) -> None:
    """Проверяет структуру конфигурационного словаря."""
    sources = config.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ConfigError("❌ В конфигурации должен быть непустой список 'sources'.")

    for idx, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise ConfigError(f"❌ Источник #{idx} должен быть словарём.")
        if "path" not in source:
            raise ConfigError(f"❌ Источник #{idx} не содержит ключ 'path'.")
        if not isinstance(source.get("mounted", True), bool):
            raise ConfigError(f"❌ 'mounted' у источника #{idx} должен быть логическим значением.")

    destination = config.get("destination")
    if not isinstance(destination, dict):
        raise ConfigError("❌ Блок 'destination' должен быть словарём.")
    if "path" not in destination:
        raise ConfigError("❌ В 'destination' должен быть указан 'path'.")
    if not isinstance(destination.get("mounted", True), bool):
        raise ConfigError("❌ 'mounted' в 'destination' должен быть логическим значением.")

    telegram = config.get("telegram")
    if telegram:
        if not isinstance(telegram, dict):
            raise ConfigError("❌ 'telegram' должен быть словарём.")
        if not telegram.get("token") or not telegram.get("chat_id"):
            raise ConfigError("❌ В 'telegram' должны быть указаны 'token' и 'chat_id'.")
