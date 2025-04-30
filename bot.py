#bot.py
import json
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message
import asyncio

# Загрузка переменных окружения
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')

if not API_TOKEN:
    raise ValueError("❌ API_TOKEN не задан в .env файле")

# Создание бота и диспетчера
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

USER_DATA_FILE = 'data/users.json'

# Гарантируем наличие JSON-файла
if not os.path.exists(USER_DATA_FILE):
    os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

try:
    with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
        if not isinstance(users, list):
            raise ValueError("JSON должен быть списком пользователей")
except (json.JSONDecodeError, ValueError):
    users = []
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f)


@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id not in users:
        users.append(user_id)
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    await message.answer("Добро пожаловать!")


@dp.message(F.text == "/users")
async def list_users(message: Message):
    text = "<b>Зарегистрированные пользователи:</b>\n" + "\n".join(str(u) for u in users)
    await message.answer(text)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
