import argparse
from flask import Flask
from app.routes import register_routes  # Убедитесь, что этот файл существует
from app.sync_core import start_sync  # Убедитесь, что start_sync правильно реализована

app = Flask(__name__)
register_routes(app)  # Регистрация маршрутов


def main():
    # Ожидаем аргументы для веба и синхронизации
    parser = argparse.ArgumentParser(description="Запуск приложения для синхронизации файлов")

    # Добавляем флаг для запуска веб-интерфейса
    parser.add_argument(
        '--web',
        action='store_true',
        help='Запуск Web-интерфейса Flask'
    )

    # Добавляем дополнительные аргументы для синхронизации
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Покажет, что будет сделано, но не будет копировать файлы.'
    )
    parser.add_argument(
        '--skip-telegram',
        action='store_true',
        help='Пропустить отправку уведомлений в Telegram.'
    )
    parser.add_argument(
        '--report-html',
        action='store_true',
        help='Генерация HTML отчёта.'
    )
    parser.add_argument(
        '--report-path',
        type=str,
        help='Путь для сохранения HTML отчёта.'
    )

    # Парсим аргументы
    args = parser.parse_args()

    if args.web:
        # Если указан флаг --web, запускаем Flask
        print("Запуск Flask-сервера...")
        app.run(debug=True, host='127.0.0.1', port=5001)  # Локальный хост, другой порт для отладки
    else:
        # Если не указан флаг --web, запускаем синхронизацию
        print("Запуск синхронизации файлов...")
        start_sync(
            dry_run=args.dry_run,
            skip_telegram=args.skip_telegram,
            report_html=args.report_html,
            report_path=args.report_path
        )


if __name__ == '__main__':
    main()
