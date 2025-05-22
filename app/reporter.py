from pathlib import Path
from datetime import datetime
from yattag import Doc
from typing import Dict, List, Tuple


def save_html_report(results_by_bureau: Dict[str, Dict[str, List[Tuple[str, str]]]],
                     stats_by_bureau: Dict[str, Dict[str, Dict[str, int]]],
                     report_datetime: datetime) -> Path:
    doc, tag, text = Doc().tagtext()

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
                    details {
                        background-color: #f0f4f8;
                        border: 1px solid #ccc;
                        border-radius: 6px;
                        padding: 10px 15px;
                        margin-bottom: 20px;
                    }
                    summary {
                        cursor: pointer;
                        font-weight: bold;
                        font-size: 16px;
                        color: #2d3436;
                    }
                    summary:hover {
                        color: #0984e3;
                    }
                    ul {
                        list-style-type: disc;
                        margin-left: 20px;
                    }
                    li {
                        margin: 5px 0;
                    }
                    p {
                        margin: 10px 0;
                    }
                    .stats {
                        background-color: #ecf0f1;
                        padding: 10px;
                        border-radius: 5px;
                        margin-top: 10px;
                        font-weight: bold;
                    }
                """)

        with tag("body"):
            with tag("h2"):
                text(f"Отчет синхронизации — {report_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

            grand_total_added = 0
            grand_total_modified = 0

            for bureau, results_by_name in results_by_bureau.items():
                total_added = 0
                total_modified = 0

                # Считаем общее количество изменений в бюро
                for name, files in results_by_name.items():
                    stats = stats_by_bureau.get(bureau, {}).get(name, {"added": 0, "modified": 0, "copied": 0})
                    total_added += stats.get("added", 0)
                    total_modified += stats.get("modified", 0)

                grand_total_added += total_added
                grand_total_modified += total_modified

                change_count = total_added + total_modified

                with tag("details"):
                    with tag("summary"):
                        text(f"{bureau} - ({change_count})")

                    for name, files in results_by_name.items():
                        added = [f for f, status in files if status == "added"]
                        modified = [f for f, status in files if status == "modified"]
                        stats = stats_by_bureau.get(bureau, {}).get(name, {"added": 0, "modified": 0, "copied": 0})

                        with tag("details"):
                            with tag("summary"):
                                text(f"{name} — Добавлено: {stats['added']} | Изменено: {stats['modified']} | Скопировано: {stats['copied']}")

                            if added:
                                with tag("p"):
                                    text("Добавленные файлы:")
                                with tag("ul"):
                                    for f in added:
                                        with tag("li"):
                                            text(f)
                            else:
                                with tag("p"):
                                    text("Нет добавленных файлов.")

                            if modified:
                                with tag("p"):
                                    text("Изменённые файлы:")
                                with tag("ul"):
                                    for f in modified:
                                        with tag("li"):
                                            text(f)
                            else:
                                with tag("p"):
                                    text("Нет изменённых файлов.")

            with tag("div", klass="stats"):
                text(f"Общий итог по всем бюро — Добавлено: {grand_total_added}, Изменено: {grand_total_modified}")

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

    # Обновляем историю отчетов после создания нового отчёта
    update_index_html(base_dir, all_dates_dir, latest_report_path=report_path)

    return report_path


def update_index_html(base_dir: Path, all_dates_dir: Path, latest_report_path: Path = None):
    index_path = base_dir / "Отчет.html"
    links = []

    if all_dates_dir.exists():
        for date_dir in sorted(all_dates_dir.iterdir(), reverse=True):
            if date_dir.is_dir():
                for report_file in sorted(date_dir.glob("Отчет_*.html"), reverse=True):
                    rel_path = Path("Все даты") / date_dir.name / report_file.name
                    display_name = report_file.stem.replace("Отчет_", "").replace("_", " ")
                    is_latest = (latest_report_path is not None and report_file.resolve() == latest_report_path.resolve())
                    links.append((display_name, str(rel_path).replace("\\", "/"), is_latest))

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
