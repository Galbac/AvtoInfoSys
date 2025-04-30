# cli.py

import argparse
from app.sync_core import start_sync

def main():
    parser = argparse.ArgumentParser(description="Синхронизация сетевых папок")
    parser.add_argument("--config", help="Путь к конфигурационному файлу YAML", default="config.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Запуск без копирования файлов")
    args = parser.parse_args()

    start_sync(config_path=args.config, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
