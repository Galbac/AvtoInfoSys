# telegram_notify.py
import os
import json
from aiogram import Bot
from aiogram.types import FSInputFile
from dotenv import load_dotenv

load_dotenv()

USERS_FILE = "users.json"  # файл, где хранятся chat_id пользователей

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

async def send_telegram_message(message: str):
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Telegram bot token not found.")
        return

    users = load_users()
    if not users:
        print("Нет зарегистрированных пользователей.")
        return

    bot = Bot(token=token)
    try:
        for chat_id in users:
            try:
                await bot.send_message(chat_id=chat_id, text=message)
                print(f"✅ Сообщение отправлено: {chat_id}")
            except Exception as e:
                print(f"⚠️ Ошибка при отправке {chat_id}: {e}")
    finally:
        await bot.session.close()

async def send_report_file(file_path: str):
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Telegram bot token not found.")
        return

    users = load_users()
    if not users:
        print("Нет зарегистрированных пользователей.")
        return

    bot = Bot(token=token)
    try:
        file = FSInputFile(file_path, filename=os.path.basename(file_path))
        for chat_id in users:
            try:
                await bot.send_document(chat_id=chat_id, document=file)
                print(f"✅ Отчёт отправлен пользователю: {chat_id}")
            except Exception as e:
                print(f"⚠️ Ошибка при отправке {chat_id}: {e}")
    finally:
        await bot.session.close()
