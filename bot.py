
# bot.py (улучшенная версия)
import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ Переменная окружения BOT_TOKEN не найдена")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

DATA_DIR.mkdir(exist_ok=True)
if not USERS_FILE.exists():
    USERS_FILE.write_text("[]", encoding="utf-8")

try:
    users = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    if not isinstance(users, list):
        raise ValueError("Файл users.json должен содержать список")
except Exception:
    users = []
    USERS_FILE.write_text("[]", encoding="utf-8")


def save_users():
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id not in users:
        users.append(user_id)
        save_users()
    await message.answer("Добро пожаловать! Вы добавлены в список получателей уведомлений.")


@dp.message(F.text == "/users")
async def list_users(message: Message):
    text = "<b>Зарегистрированные пользователи:</b>\n" + "\n".join(str(uid) for uid in users)
    await message.answer(text)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
