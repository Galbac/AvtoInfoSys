#cli.py
import argparse

from app.sync_core import start_sync


def run_cli():
    parser = argparse.ArgumentParser(description="Синхронизация файлов по сети.")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Показать, что будет сделано, но не копировать файлы."
    )
    parser.add_argument(
        "--skip-telegram",
        action="store_true",
        help="Не отправлять уведомления в Telegram"
    )
    parser.add_argument(
        "--report-html",
        action="store_true",
        help="Сгенерировать HTML-отчёт после синхронизации"
    )
    parser.add_argument(
        "--report-path",
        default="report.html",
        help="Путь для сохранения HTML-отчёта"
    )

    args = parser.parse_args()

    start_sync(
        dry_run=args.dry_run,
        skip_telegram=args.skip_telegram,
        generate_html=args.report_html,
        report_path=args.report_path
    )


if __name__ == "__main__":
    run_cli()
