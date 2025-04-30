import asyncio
import os
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
USERS_FILE = "users.json"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

def load_users():
    """Загружает список пользователей из файла JSON, если файл поврежден, возвращает пустой список."""
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_user(user_id):
    """Добавляет пользователя в файл, если его там нет."""
    users = load_users()

    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)  # Форматирование для удобства чтения.
        print(f"✅ Пользователь {user_id} добавлен.")
    else:
        print(f"ℹ️ Пользователь {user_id} уже есть.")

@dp.message(F.text == "/start")
async def start_handler(message: Message):
    save_user(message.chat.id)
    await message.answer("✅ Вы зарегистрированы для получения отчётов.")

async def send_report_to_all(file_path):
    users = load_users()
    if not users:
        print("❌ Нет зарегистрированных пользователей.")
        return

    file = FSInputFile(file_path, filename=os.path.basename(file_path))

    for user_id in users:
        try:
            await bot.send_document(chat_id=user_id, document=file)
            print(f"✅ Отчёт отправлен: {user_id}")
        except Exception as e:
            print(f"❌ Не удалось отправить отчет {user_id}: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
