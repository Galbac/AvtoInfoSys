#sync_core.py
import asyncio
import concurrent.futures
import os
import shutil
from datetime import datetime
from pathlib import Path

from app.database import save_file_record
from app.hashing import calculate_file_hash
from app.logger import get_logger
from app.reporter import generate_html_report
from app.telegram_notify import send_telegram_message, send_report_file  # Импортируем нужные функции
from app.utils import load_config

logger = get_logger()


def sync_folder(ip, shared_path, destination_root, dry_run=False):
    source_dir = Path(shared_path)
    dest_dir = destination_root / ip
    new_files = []

    if not source_dir.exists():
        logger.warning(f"Источник не найден: {source_dir}")
        return ip, new_files

    logger.info(f"Файлы и папки в {source_dir.resolve()}:")
    for file in source_dir.rglob('*'):
        logger.info(f" - {file.name} (Тип: {file.suffix if file.is_file() else 'Папка'})")

    for file in source_dir.rglob('*'):
        dest_file = dest_dir / file.relative_to(source_dir)

        if file.is_dir():
            if not dry_run and not dest_file.exists():
                logger.info(f"Создание директории {dest_file}")
                dest_file.mkdir(parents=True, exist_ok=True)
        else:
            if not file.name.startswith('.'):
                src_hash = calculate_file_hash(file)
                logger.info(f"Хеш для {file.name}: {src_hash}")

                if dest_file.exists():
                    dest_hash = calculate_file_hash(dest_file)
                    if src_hash == dest_hash:
                        logger.info(f"Файл {file.name} уже синхронизирован. Пропускаем.")
                        continue

                logger.info(f"Новый или изменённый файл: {file.name}")
                if not dry_run:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file, dest_file)
                    save_file_record(ip, file.name, src_hash)

                created_time = datetime.fromtimestamp(file.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                new_files.append((file.name, created_time))

    return ip, new_files

def write_report(results):
    desktop_path = Path(os.path.join(os.environ["USERPROFILE"], "Desktop"))

    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

    report_dir = desktop_path / "Отчёты" / date_str
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / f"{time_str}.txt"
    report_lines = []

    for ip, files in results:
        if files:
            report_lines.append(f"{ip}:")
            for name, ctime in files:
                report_lines.append(f"  - {name} — {ctime}")
            report_lines.append("")

        else:
            report_lines.append(f"{ip}: Нет новых файлов для синхронизации.\n")

    with report_file.open("w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    logger.info(f"📝 Отчёт сохранён: {report_file.resolve()}")
    return report_file


def start_sync(dry_run=False, skip_telegram=False, report_html=False, report_path=None):
    try:
        config = load_config()
        destination_root = Path(config["destination_root"])
        shared_folders = config["shared_folders"]

        logger.info(f"Начинается синхронизация. dry_run={dry_run}, skip_telegram={skip_telegram}")

        report_entries = []  # [(ip, [files])]

        # Сканирование папок в потоках
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(sync_folder, ip, shared_path, destination_root, dry_run=dry_run)
                for ip, shared_path in shared_folders.items()
            ]
            for future in concurrent.futures.as_completed(futures):
                ip, new_files = future.result()
                report_entries.append((ip, new_files))

        msg = f"✅ Синхронизация завершена в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logger.info(msg)

        # Генерация и сохранение отчёта
        report_file_path = write_report(report_entries)

        # Генерация HTML-отчёта, если нужно
        if report_html:
            if report_path:
                generate_html_report(report_path)
            else:
                logger.warning("Путь для HTML отчёта не задан. Отчёт не будет сгенерирован.")

        # Отправка отчёта и уведомления в Telegram
        if not skip_telegram:
            async def notify():
                if all(len(files) == 0 for _, files in report_entries):
                    await send_telegram_message("ℹ️ Сканирование завершено. Новых файлов не обнаружено.")
                else:
                    await send_telegram_message(msg)
                await send_report_file(str(report_file_path))  # Отправка отчёта в Telegram

            asyncio.run(notify())

        logger.info(f"Полный путь к отчёту: {report_file_path.resolve()}")

    except Exception as e:
        error_msg = f"❌ Ошибка при синхронизации: {e}"
        logger.exception(error_msg)

        if not skip_telegram:
            async def send_error():
                await send_telegram_message(error_msg)

            asyncio.run(send_error())
