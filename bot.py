#bot.py
import json
import os

import executor
from aiogram import Bot, Dispatcher, types


API_TOKEN = 'YOUR_API_TOKEN'  # замените на ваш токен

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

USER_DATA_FILE = 'data/users.json'

# ✅ Гарантируем, что файл существует и содержит корректный JSON
if not os.path.exists(USER_DATA_FILE):
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


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users:
        users.append(user_id)
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    await message.answer("Добро пожаловать!")


@dp.message_handler(commands=['users'])
async def list_users(message: types.Message):
    text = "Зарегистрированные пользователи:\n" + "\n".join(str(u) for u in users)
    await message.answer(text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
