import logging
import shutil
from pathlib import Path
import concurrent.futures
from datetime import datetime  # Добавлен импорт datetime

from app.logger import get_logger
from app.reporter import generate_html_report
from app.utils import load_config, calculate_file_hash, send_telegram_message
from app.database import save_file_record, is_file_already_synced

logger = get_logger()

# Функция для синхронизации одного каталога
def sync_folder(ip, shared_path, destination_root, dry_run=False):
    source_dir = Path(shared_path)
    dest_dir = destination_root / ip

    if not source_dir.exists():
        logger.warning(f"Источник не найден: {source_dir}")
        return

    # Создание папки назначения для каждого IP, если её нет
    if not dest_dir.exists():
        logger.info(f"Создание директории {dest_dir}")
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)

    # Проверка файлов в папке
    if dry_run:
        logger.info(f"[dry_run] Проверка папки {source_dir} → {dest_dir}")
    else:
        for file in source_dir.iterdir():
            if file.is_file():
                dest_file = dest_dir / file.name
                src_hash = calculate_file_hash(file)

                # Проверка, был ли уже синхронизирован файл
                if is_file_already_synced(ip, file.name, src_hash):
                    logger.info(f"Файл уже синхронизирован: {file.name}")
                    continue  # Пропустить файл, если он уже был синхронизирован

                logger.info(f"Новый или изменённый файл: {file.name}")
                if not dry_run:
                    shutil.copy2(file, dest_file)  # Копируем файл в папку назначения
                    save_file_record(ip, file.name, src_hash)  # Сохраняем запись в БД

# Функция для параллельной синхронизации
def start_sync(dry_run=False, skip_telegram=False, report_html=False, report_path=None):
    try:
        config = load_config()
        destination_root = Path(config["destination_root"])
        shared_folders = config["shared_folders"]

        logger.info(f"Начинается синхронизация. dry_run={dry_run}, skip_telegram={skip_telegram}")

        # Используем ThreadPoolExecutor для параллельной синхронизации
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for ip, shared_path in shared_folders.items():
                futures.append(executor.submit(sync_folder, ip, shared_path, destination_root, dry_run))

            # Дождаться завершения всех задач
            for future in concurrent.futures.as_completed(futures):
                future.result()  # Если ошибка произошла, она будет поднята здесь

        # Сообщение о завершении
        msg = f"✅ Синхронизация завершена в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logger.info(msg)

        if report_html:
            if report_path:
                generate_html_report(report_path)
            else:
                logger.warning("Путь для HTML отчёта не задан. Отчёт не будет сгенерирован.")

        if not skip_telegram:
            send_telegram_message(msg)

    except Exception as e:
        error_msg = f"❌ Ошибка при синхронизации: {e}"
        logger.exception(error_msg)

        if not skip_telegram:
            send_telegram_message(error_msg)
