from datetime import datetime
from pathlib import Path
from app.logger import get_logger

logger = get_logger()


from datetime import datetime
from pathlib import Path
from collections import Counter
from app.logger import get_logger

logger = get_logger()


from datetime import datetime
from pathlib import Path
from collections import Counter
from app.logger import get_logger

logger = get_logger()


def save_html_report(results_by_name: dict, stats_by_name: dict, dry_run: bool = False) -> str:
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")

    report_dir = Path.home() / "Desktop" / "Отчет" / date_str
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"Отчет_{date_str}.html"

    title = f"Отчет синхронизации {'(пробный запуск)' if dry_run else ''}"
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')

    html = [
        "<!DOCTYPE html>",
        "<html lang='ru'>",
        "<head><meta charset='utf-8'>",
        f"<title>{title}</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; background: #f9f9f9; color: #333; padding: 20px; }",
        "h2 { color: #2c3e50; }",
        "h3 { color: #34495e; }",
        "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }",
        "th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }",
        "th { background-color: #f0f0f0; }",
        "tr:nth-child(even) { background-color: #fefefe; }",
        ".summary { font-weight: bold; color: #2d7c32; }",
        ".no-changes { font-style: italic; color: #888; }",
        ".total-summary { font-weight: bold; color: #1a5276; font-size: 16px; margin-top: 30px; }",
        "</style></head><body>",
        f"<h2>{title}</h2>",
        f"<p><b>Дата:</b> {timestamp}</p><hr>"
    ]

    total_counter = Counter()

    if not results_by_name:
        html.append("<p class='no-changes'>Изменений не обнаружено.</p>")
    else:
        for name, files in results_by_name.items():
            stats = stats_by_name.get(name, {})
            html.append(f"<h3>{name}</h3>")
            html.append("<table><thead><tr><th>Файл</th></tr></thead><tbody>")
            for file in files:
                if isinstance(file, dict):
                    path = file.get("path", "неизвестно")
                    status = file.get("status", "")
                    if status == "added":
                        status_text = "добавлено"
                    elif status == "modified":
                        status_text = "изменено"
                    else:
                        status_text = "неизвестно"
                    html.append(f"<tr><td>{path} - {status_text}</td></tr>")
                else:
                    html.append(f"<tr><td>{file}</td></tr>")
            html.append("</tbody></table>")

            added = stats.get('added', 0)
            modified = stats.get('modified', 0)
            copied = stats.get('copied', 0)
            total_counter.update({'added': added, 'modified': modified, 'copied': copied})

            summary = f"Добавлено: <b>{added}</b> | Изменено: <b>{modified}</b> | Скопировано: <b>{copied}</b>"
            html.append(f"<p class='summary'>{summary}</p><hr>")

        html.append(
            f"<div class='total-summary'>🧾 <b>Общий итог:</b> "
            f"Добавлено: <b>{total_counter['added']}</b> | "
            f"Изменено: <b>{total_counter['modified']}</b> | "
            f"Скопировано: <b>{total_counter['copied']}</b></div>"
        )

    html.append("</body></html>")

    try:
        report_file.write_text("\n".join(html), encoding="utf-8")
        logger.info(f"✅ HTML-отчет сохранен: {report_file}")
        return str(report_file)
    except Exception as e:
        logger.error(f"❌ Не удалось сохранить HTML-отчет: {e}")
        raise



