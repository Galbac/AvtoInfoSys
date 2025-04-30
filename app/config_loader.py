#config_loader.py
import yaml

from dotenv import load_dotenv

load_dotenv()

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
