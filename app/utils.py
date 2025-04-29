# app/utils.py

import yaml
import hashlib
import requests
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def calculate_file_hash(file_path):
    hash_func = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def send_telegram_message(message: str):
    token = os.getenv("TG_BOT_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")

    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Ошибка при отправке в Telegram: {e}")
