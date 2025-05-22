import argparse
import sys
from app.sync_core import start_sync

def main():
    parser = argparse.ArgumentParser(
        description="Синхронизация сетевых папок"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Путь к конфигурационному файлу YAML (по умолчанию: config.yaml)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Запуск без копирования файлов (только вывод действий)"
    )
    args = parser.parse_args()

    try:
        start_sync(config_path=args.config, dry_run=args.dry_run)
    except Exception as e:
        print(f"❌ Ошибка во время синхронизации: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
