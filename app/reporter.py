#reporter.py
import json
from pathlib import Path

from app.database import DB_FILE


def generate_html_report(output_path="report.html"):
    # Проверяем, существует ли база данных
    if not DB_FILE.exists():
        raise FileNotFoundError("Нет базы данных")

    # Загружаем данные из базы
    with open(DB_FILE) as f:
        db = json.load(f)

    # Строим HTML-отчёт
    html = "<html><body><h1>Синхронизированные файлы</h1><ul>"
    for ip, files in db.items():
        for fname in files:
            html += f"<li>{ip}: {fname}</li>"
    html += "</ul></body></html>"

    # Сохраняем в файл по заданному пути
    output_path = Path(output_path)
    with open(output_path, "w") as rep:
        rep.write(html)

    return str(output_path)  # Возвращаем путь к сохранённому отчёту
