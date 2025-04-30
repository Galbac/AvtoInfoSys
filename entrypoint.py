#entrypoint.py
import argparse
import io
import sys

from flask import Flask

from app.routes import register_routes
from app.sync_core import start_sync
from app.logger import get_logger  # Импорт логгера

# Настраиваем stdout на UTF-8 (для совместимости с консолью)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Создаём Flask-приложение
app = Flask(__name__)
register_routes(app)

# Получаем логгер
logger = get_logger()


def main():
    parser = argparse.ArgumentParser(description="Запуск приложения для синхронизации файлов")

    parser.add_argument('--web', action='store_true', help='Запуск Web-интерфейса Flask')
    parser.add_argument('--dry-run', action='store_true', help='Показать, что будет сделано без копирования файлов')
    parser.add_argument('--skip-telegram', action='store_true', help='Не отправлять уведомления в Telegram')
    parser.add_argument('--report-html', action='store_true', help='Генерация HTML-отчёта')
    parser.add_argument('--report-path', type=str, help='Путь для сохранения HTML-отчёта')

    args = parser.parse_args()

    if args.web:
        logger.info("Запуск Flask-сервера на http://127.0.0.1:5001")
        app.run(debug=True, host='127.0.0.1', port=5001)
    else:
        logger.info("Запуск синхронизации файлов...")
        start_sync(
            dry_run=args.dry_run,
            skip_telegram=args.skip_telegram,
            report_html=args.report_html,
            report_path=args.report_path
        )


if __name__ == '__main__':
    main()
