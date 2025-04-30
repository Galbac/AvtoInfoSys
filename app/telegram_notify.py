#telegram_notify.py
import os
from aiogram import Bot
from aiogram.types import FSInputFile  # Используем FSInputFile вместо InputFile
from dotenv import load_dotenv

load_dotenv()


async def send_telegram_message(message: str):
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("ADMIN_CHAT_ID")

    if not token or not chat_id:
        print("Telegram bot token or chat ID not found.")
        return

    bot = Bot(token=token)
    try:
        await bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        print(f"Ошибка при отправке в Telegram: {e}")
    finally:
        await bot.session.close()  # Закрытие сессии обязательно


async def send_report_file(file_path: str):
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("ADMIN_CHAT_ID")

    if not token or not chat_id:
        print("Telegram bot token or chat ID not found.")
        return

    bot = Bot(token=token)
    try:
        file = FSInputFile(file_path, filename=os.path.basename(file_path))  # Правильно создаем объект файла
        await bot.send_document(chat_id=chat_id, document=file)
        print(f"✅ Отчёт отправлен в Telegram: {file_path}")
    except Exception as e:
        print(f"Ошибка при отправке файла: {e}")
    finally:
        await bot.session.close()  # Обязательно закрываем сессию
