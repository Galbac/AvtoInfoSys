from datetime import datetime
from pathlib import Path
from app.logger import get_logger

logger = get_logger()


def save_html_report(results_by_name: dict, stats_by_name: dict, dry_run: bool = False) -> str:
    """
    Сохраняет HTML-отчет о синхронизации.
    Возвращает путь к созданному файлу.
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")

    base_path = Path.home() / "Desktop" / "отчет" / date_str
    base_path.mkdir(parents=True, exist_ok=True)

    report_file = base_path / f"отчет_{time_str}.html"

    html_parts = [
        "<html><head><meta charset='utf-8'><title>Отчет</title></head><body>",
        f"<h2>Отчет синхронизации {'(пробный запуск)' if dry_run else ''}</h2>",
        f"<p><b>Дата:</b> {now.strftime('%Y-%m-%d %H:%M:%S')}</p><hr>"
    ]

    if not results_by_name:
        html_parts.append("<p>Изменений не обнаружено.</p>")
    else:
        for name, files in results_by_name.items():
            stats = stats_by_name.get(name, {})
            html_parts.append(f"<h3>{name}</h3>")
            html_parts.append("<ul>")
            for file in files:
                html_parts.append(f"<li>{file}</li>")
            html_parts.append("</ul>")

            summary = (
                f"Добавлено: {stats.get('added', 0)} | "
                f"Изменено: {stats.get('modified', 0)} | "
                f"Скопировано: {stats.get('copied', 0)}"
            )
            html_parts.append(f"<p><b>{summary}</b></p><hr>")

    html_parts.append("</body></html>")

    try:
        report_file.write_text("\n".join(html_parts), encoding="utf-8")
        logger.info(f"✅ HTML-отчет сохранен: {report_file}")
        return str(report_file)
    except Exception as e:
        logger.error(f"❌ Не удалось сохранить отчет: {e}")
        raise
