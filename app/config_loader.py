#app/config_loader.py
from pathlib import Path
from typing import Any, Dict
import yaml
from app.logger import get_logger

logger = get_logger()

class ConfigError(Exception):
    """Исключение при ошибках конфигурации."""
    pass

def load_config(config_path: str = "") -> dict:
    """
    🔹 Загружает YAML-конфиг.
    - Приоритет: указанный путь → config.yaml → config/config.yaml
    - Автоматически преобразует `destination.path` → `destination.paths`
    - Защита от битых/пустых файлов
    """
    from app.utils import CONFIG_PATHS
    search_paths = [Path(config_path)] if config_path else CONFIG_PATHS

    for path in search_paths:
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    logger.warning(f"⚠️ Конфиг-файл пуст: {path}")
                    return {}
                config = yaml.safe_load(content)
            if not isinstance(config, dict):
                logger.error(f"❌ Некорректный формат YAML: {path}")
                return {}

            # Совместимость: один путь → список
            dest = config.get("destination")
            if isinstance(dest, dict):
                if "path" in dest and "paths" not in dest:
                    dest["paths"] = [dest.pop("path")]  # удаляем старое, добавляем новое
                if isinstance(dest.get("paths"), str):
                    dest["paths"] = [dest["paths"]]

            logger.info(f"✅ Конфиг загружен: {path}")
            return config
        except yaml.YAMLError as e:
            logger.error(f"❌ Ошибка парсинга YAML {path}: {e}")
            return {}
        except PermissionError:
            logger.error(f"❌ Нет доступа к файлу: {path}")
            return {}
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке конфига {path}: {e}")
            return {}

    logger.error("❌ Конфиг не найден в стандартных путях.")
    return {}

def validate_config(config: Dict[str, Any]) -> None:
    """
    🔹 Проверяет структуру конфига.
    Выбрасывает ConfigError при ошибках.
    """
    sources = config.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ConfigError("❌ 'sources' должен быть непустым списком.")

    for idx, source in enumerate(sources, 1):
        if not isinstance(source, dict):
            raise ConfigError(f"❌ Источник #{idx} должен быть словарём.")
        if not source.get("name"):
            raise ConfigError(f"❌ Источник #{idx} не содержит 'name'.")
        if not source.get("path"):
            raise ConfigError(f"❌ Источник #{idx} не содержит 'path'.")
        if not isinstance(source.get("buro", ""), str):
            raise ConfigError(f"❌ 'buro' у источника #{idx} должен быть строкой.")
        if not isinstance(source.get("mounted", True), bool):
            raise ConfigError(f"❌ 'mounted' у источника #{idx} должен быть bool.")

    destination = config.get("destination")
    if not isinstance(destination, dict):
        raise ConfigError("❌ 'destination' должен быть словарём.")
    if not destination.get("paths") or not isinstance(destination["paths"], list) or not destination["paths"]:
        raise ConfigError("❌ Укажите 'destination.paths' как список путей.")

    for path in destination["paths"]:
        if not isinstance(path, str) or not path.strip():
            raise ConfigError(f"❌ Некорректный путь в 'destination.paths': {path}")

    logger.info("✅ Конфиг валидирован.")