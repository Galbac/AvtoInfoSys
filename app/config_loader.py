import yaml
from pathlib import Path
from typing import Any, Dict


class ConfigError(Exception):
    """Исключение, выбрасываемое при ошибках конфигурации."""
    pass


def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    """Загружает и валидирует YAML-файл конфигурации."""
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigError(f"❌ Файл конфигурации не найден: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"❌ Ошибка разбора YAML: {e}")

    if not isinstance(config, dict):
        raise ConfigError("❌ Конфигурация должна быть словарём верхнего уровня.")

    validate_config(config)
    return config


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
