import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message

from app.utils import save_recipient, load_recipients

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ Переменная окружения BOT_TOKEN не найдена.")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if save_recipient(user_id):
        await message.answer("✅ Вы добавлены в список получателей уведомлений.")
    else:
        await message.answer("ℹ️ Вы уже есть в списке получателей уведомлений.")


@dp.message(F.text == "/users")
async def cmd_users(message: Message):
    users = load_recipients()
    if users:
        lines = "\n".join(f"• <code>{uid}</code>" for uid in users)
        text = f"<b>Зарегистрированные пользователи:</b>\n{lines}"
    else:
        text = "Список получателей пуст."
    await message.answer(text)


async def main():
    print("🤖 Бот запущен и ожидает команды...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("⛔ Бот остановлен.")
