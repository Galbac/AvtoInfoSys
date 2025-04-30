import json
import os
import yaml
from aiogram import Bot, Dispatcher
from aiogram import F
from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.client.bot import DefaultBotProperties
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Использование DefaultBotProperties для указания параметров по умолчанию
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

RECIPIENTS_FILE = "users.json"


def load_config():
    """
    Загружает конфигурацию из YAML файла.
    Ищет сначала в корне проекта, потом в папке ./config.
    """
    base_dir = Path(__file__).resolve().parent.parent  # корень проекта
    possible_paths = [
        base_dir / "config.yaml",
        base_dir / "config" / "config.yaml"
    ]

    for config_path in possible_paths:
        if config_path.exists():
            try:
                with config_path.open("r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"Ошибка при разборе YAML: {e}")
                return {}

    print("❌ Ошибка: config.yaml не найден.")
    return {}


def load_recipients():
    """Загружает список получателей из файла."""
    if not os.path.exists(RECIPIENTS_FILE):
        return []
    try:
        with open(RECIPIENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Ошибка при чтении списка получателей: {e}")
        return []


def save_recipient(user_id: int):
    """Сохраняет нового получателя в файл, если его ещё нет в списке."""
    recipients = load_recipients()
    if user_id not in recipients:
        recipients.append(user_id)
        try:
            with open(RECIPIENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(recipients, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка при сохранении получателя: {e}")


@router.message(F.text == "/start")
async def handle_start(message: Message):
    """Обработчик для команды /start."""
    save_recipient(message.chat.id)
    await message.answer("✅ Вы добавлены в список получателей отчётов.")


@router.message()
async def handle_any(message: Message):
    """Обработчик для всех остальных сообщений."""
    save_recipient(message.chat.id)
    await message.answer("📥 Вы будете получать отчёты.")


async def main():
    """Запуск бота."""
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
