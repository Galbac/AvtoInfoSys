from pathlib import Path
from datetime import datetime
from yattag import Doc
from typing import Dict, List, Tuple


def save_html_report(results_by_name: Dict[str, List[Tuple[str, str]]],
                     stats_by_name: Dict[str, Dict[str, int]],
                     report_datetime: datetime) -> Path:
    doc, tag, text = Doc().tagtext()

    total_added = total_modified = total_copied = 0

    doc.asis("<!DOCTYPE html>")
    with tag("html"):
        with tag("head"):
            doc.stag("meta", charset="utf-8")
            with tag("title"):
                text("Отчет синхронизации")
            with tag("style"):
                text("""
                    body {
                        font-family: Arial, sans-serif;
                        margin: 40px;
                        background-color: #f9f9f9;
                        color: #333;
                    }
                    h2 {
                        color: #2c3e50;
                        border-bottom: 2px solid #ccc;
                        padding-bottom: 5px;
                    }
                    h3 {
                        color: #34495e;
                        margin-top: 30px;
                    }
                    p {
                        margin: 10px 0;
                    }
                    ul {
                        list-style-type: disc;
                        margin-left: 20px;
                    }
                    li {
                        margin: 5px 0;
                    }
                    .stats {
                        background-color: #ecf0f1;
                        padding: 10px;
                        border-radius: 5px;
                        margin-top: 10px;
                        font-weight: bold;
                    }
                    .summary {
                        background-color: #dfe6e9;
                        padding: 15px;
                        margin-top: 40px;
                        border: 2px solid #b2bec3;
                        border-radius: 8px;
                        text-align: center;
                        font-size: 16px;
                    }
                    .icon {
                        font-size: 40px;
                        margin-bottom: 10px;
                    }
                """)

        with tag("body"):
            with tag("h2"):
                text(f"Отчет синхронизации — {report_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

            for name, files in results_by_name.items():
                added = [f for f, status in files if status == "added"]
                modified = [f for f, status in files if status == "modified"]
                stats = stats_by_name.get(name, {"added": 0, "modified": 0, "copied": 0})

                total_added += stats["added"]
                total_modified += stats["modified"]
                total_copied += stats["copied"]

                with tag("h3"):
                    text(name)

                with tag("p"):
                    text("Добавлено:" if added else "Нет добавленных файлов.")
                if added:
                    with tag("ul"):
                        for f in added:
                            with tag("li"):
                                text(f)

                with tag("p"):
                    text("Изменено:" if modified else "Нет изменённых файлов.")
                if modified:
                    with tag("ul"):
                        for f in modified:
                            with tag("li"):
                                text(f)

                with tag("p", klass="stats"):
                    text(f"Добавлено: {stats['added']} | Изменено: {stats['modified']} | Скопировано: {stats['copied']}")

            with tag("div", klass="summary"):
                with tag("div", klass="icon"):
                    text("📊")
                with tag("strong"):
                    text("Общий итог")
                with tag("p"):
                    text(f"Всего добавлено: {total_added}")
                with tag("p"):
                    text(f"Всего изменено: {total_modified}")
                with tag("p"):
                    text(f"Всего скопировано: {total_copied}")

    html = doc.getvalue()
    date_str = report_datetime.strftime("%Y-%m-%d")
    time_str = report_datetime.strftime("%H-%M-%S")

    base_dir = Path.home() / "Desktop" / "Отчет"
    all_dates_dir = base_dir / "Все даты"
    report_dir = all_dates_dir / date_str
    report_dir.mkdir(parents=True, exist_ok=True)

    report_filename = f"Отчет_{date_str}_{time_str}.html"
    report_path = report_dir / report_filename
    report_path.write_text(html, encoding="utf-8")

    # Обновить index.html
    update_index_html(base_dir, all_dates_dir)

    return report_path


def update_index_html(base_dir: Path, all_dates_dir: Path, latest_report_path: Path = None):
    index_path = base_dir / "Отчет.html"
    links = []

    # Собираем все отчеты, начиная с самых новых
    for date_dir in sorted(all_dates_dir.iterdir(), reverse=True):
        if date_dir.is_dir():
            for report_file in sorted(date_dir.glob("Отчет_*.html"), reverse=True):
                rel_path = Path("Все даты") / date_dir.name / report_file.name
                display_name = report_file.stem.replace("Отчет_", "").replace("_", " ")
                is_latest = (latest_report_path is not None and report_file.resolve() == latest_report_path.resolve())
                links.append((display_name, str(rel_path).replace("\\", "/"), is_latest))

    # Генерация HTML
    doc, tag, text = Doc().tagtext()
    doc.asis("<!DOCTYPE html>")
    with tag("html"):
        with tag("head"):
            doc.stag("meta", charset="utf-8")
            with tag("title"):
                text("История отчетов")
            with tag("style"):
                text("""
                    body {
                        font-family: Arial, sans-serif;
                        padding: 40px;
                        background-color: #f4f6f7;
                    }
                    h1 {
                        color: #2d3436;
                        margin-bottom: 20px;
                    }
                    ul {
                        list-style-type: none;
                        padding: 0;
                    }
                    li {
                        margin: 10px 0;
                    }
                    a {
                        text-decoration: none;
                        color: #0984e3;
                        font-size: 18px;
                    }
                    a:hover {
                        text-decoration: underline;
                    }
                    .new-label {
                        color: #d63031;
                        font-weight: bold;
                        margin-left: 10px;
                    }
                """)

        with tag("body"):
            with tag("h1"):
                text("История отчетов")
            with tag("ul"):
                for name, href, is_latest in links:
                    with tag("li"):
                        with tag("a", href=href):
                            text(name)
                        if is_latest:
                            with tag("span", klass="new-label"):
                                text("🆕")

    index_html = doc.getvalue()
    index_path.write_text(index_html, encoding="utf-8")




# 🔽 Пример запуска
if __name__ == "__main__":
    # Пример данных
    example_results = {
        "Проект А": [("file1.txt", "added"), ("file2.txt", "modified")],
        "Проект Б": [("doc1.docx", "added")]
    }
    example_stats = {
        "Проект А": {"added": 1, "modified": 1, "copied": 0},
        "Проект Б": {"added": 1, "modified": 0, "copied": 0}
    }
    now = datetime.now()

    save_html_report(example_results, example_stats, now)
