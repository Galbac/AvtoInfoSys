#app/utils.py
from pathlib import Path
from app.logger import get_logger

logger = get_logger()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATHS = [BASE_DIR / "config.yaml", BASE_DIR / "config" / "config.yaml"]