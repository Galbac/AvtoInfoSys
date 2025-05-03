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

                if added:
                    with tag("p"):
                        text("Добавлено:")
                    with tag("ul"):
                        for f in added:
                            with tag("li"):
                                text(f)
                else:
                    with tag("p"):
                        text("Нет добавленных файлов.")

                if modified:
                    with tag("p"):
                        text("Изменено:")
                    with tag("ul"):
                        for f in modified:
                            with tag("li"):
                                text(f)
                else:
                    with tag("p"):
                        text("Нет изменённых файлов.")

                with tag("p", klass="stats"):
                    text(f"Добавлено: {stats['added']} | Изменено: {stats['modified']} | Скопировано: {stats['copied']}")

            # ✅ Общий итог в конце с иконкой
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
    desktop = Path.home() / "Desktop"
    report_dir = desktop / "Отчет" / date_str
    report_dir.mkdir(parents=True, exist_ok=True)

    filename = f"Отчет_{date_str}_{time_str}.html"
    file_path = report_dir / filename

    file_path.write_text(html, encoding="utf-8")
    return file_path
