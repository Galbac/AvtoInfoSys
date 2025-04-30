# app/reporter.py

from datetime import datetime
from pathlib import Path
from app.logger import get_logger

logger = get_logger()

def save_html_report(all_results: dict, all_stats: dict, dry_run: bool) -> str:
    """Создаёт HTML-отчёт и возвращает путь к файлу."""

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")
    desktop = Path.home() / "Desktop"
    report_dir = desktop / "отчет" / date_str
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / f"report_{date_str}_{time_str}.html"

    html = ["<html><head><meta charset='utf-8'><title>Отчет</title></head><body>"]
    html.append(f"<h2>📅 Отчет за {now.strftime('%d.%m.%Y %H:%M:%S')}</h2>")
    if dry_run:
        html.append("<p><strong>Режим:</strong> Тестовый (ничего не копировалось)</p>")

    total_copied = 0
    total_added = 0
    total_modified = 0

    for name, changes in all_results.items():
        stats = all_stats.get(name, {})
        html.append(f"<h3>📁 {name}</h3>")
        html.append("<ul>")
        for change in changes:
            html.append(f"<li>{change}</li>")
        html.append("</ul>")

        html.append("<ul>")
        html.append(f"<li>Добавлено: {stats.get('added', 0)}</li>")
        html.append(f"<li>Изменено: {stats.get('modified', 0)}</li>")
        html.append(f"<li>Скопировано: {stats.get('copied', 0)}</li>")
        html.append("</ul>")

        total_copied += stats.get("copied", 0)
        total_added += stats.get("added", 0)
        total_modified += stats.get("modified", 0)

    html.append("<hr>")
    html.append("<h3>📊 Общий итог</h3>")
    html.append("<ul>")
    html.append(f"<li>Всего добавлено: {total_added}</li>")
    html.append(f"<li>Всего изменено: {total_modified}</li>")
    html.append(f"<li>Всего скопировано: {total_copied}</li>")
    html.append("</ul>")

    html.append("</body></html>")

    report_path.write_text("\n".join(html), encoding="utf-8")
    logger.info(f"📝 HTML-отчет сохранён: {report_path}")
    return str(report_path)
