# app/reporter.py

import os
from datetime import datetime
from pathlib import Path

def generate_html_report(results: dict, dry_run: bool = False) -> str:
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")
    filename = f"report_{date_str}_{time_str}.html"

    # Путь к рабочему столу и папке Отчет
    desktop_path = Path.home() / "Desktop"
    report_folder = desktop_path / "Отчет" / date_str
    report_folder.mkdir(parents=True, exist_ok=True)

    report_file = report_folder / filename

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'><title>Отчет</title></head><body>")
        f.write(f"<h1>Отчет синхронизации от {now.strftime('%Y-%m-%d %H:%M:%S')}</h1>")

        if dry_run:
            f.write("<p><strong>Режим: Dry-run (только проверка, без копирования)</strong></p>")

        total_changes = sum(len(files) for files in results.values())

        if total_changes == 0:
            f.write("<p><strong>Изменений не обнаружено.</strong></p>")
        else:
            for network_name, files in results.items():
                if not files:
                    continue
                f.write(f"<h2>Локальная сеть: {network_name}</h2>")
                f.write("<ul>")
                for file_path in files:
                    f.write(f"<li>{file_path}</li>")
                f.write("</ul>")

        f.write("</body></html>")

    return str(report_file)
