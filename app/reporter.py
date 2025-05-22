from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from jinja2 import Template

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Отчет синхронизации</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f9f9f9; color: #333; }
        h2 { color: #2c3e50; border-bottom: 2px solid #ccc; }
        details { background: #f0f4f8; border: 1px solid #ccc; border-radius: 6px; padding: 10px; margin-bottom: 20px; }
        summary { font-weight: bold; font-size: 16px; color: #2d3436; cursor: pointer; }
        summary:hover { color: #0984e3; }
        ul { margin-left: 20px; }
        .stats { background: #ecf0f1; padding: 10px; border-radius: 5px; font-weight: bold; margin-top: 20px; }
    </style>
</head>
<body>
<h2>Отчет синхронизации — {{ report_datetime.strftime('%Y-%m-%d %H:%M:%S') }}</h2>

{% for bureau, users in results_by_bureau.items() %}
    <details>
        <summary>{{ bureau }} - ({{ bureau_totals[bureau].added + bureau_totals[bureau].modified }})</summary>

        {% for name, files in users.items() %}
            {% set added = files | selectattr("1", "equalto", "added") | list %}
            {% set modified = files | selectattr("1", "equalto", "modified") | list %}
            {% set stat = stats_by_bureau[bureau][name] %}
            <details>
                <summary>{{ name }} — Добавлено: {{ stat.added }} | Изменено: {{ stat.modified }} | Скопировано: {{ stat.copied }}</summary>

                {% if added %}
                    <p>Добавленные файлы:</p>
                    <ul>{% for f in added %}<li>{{ f[0] }}</li>{% endfor %}</ul>
                {% else %}
                    <p>Нет добавленных файлов.</p>
                {% endif %}

                {% if modified %}
                    <p>Изменённые файлы:</p>
                    <ul>{% for f in modified %}<li>{{ f[0] }}</li>{% endfor %}</ul>
                {% else %}
                    <p>Нет изменённых файлов.</p>
                {% endif %}
            </details>
        {% endfor %}
    </details>
{% endfor %}

<div class="stats">
    Общий итог по всем бюро — Добавлено: {{ grand_total.added }}, Изменено: {{ grand_total.modified }}, Всего: {{ grand_total.added + grand_total.modified }}
</div>

</body>
</html>
"""

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Список отчетов</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f9f9f9; color: #333; }
        h1 { color: #2c3e50; }
        ul { list-style-type: none; padding-left: 0; }
        li { margin: 8px 0; }
        a { text-decoration: none; color: #0984e3; font-weight: bold; }
        a:hover { text-decoration: underline; }
        .new-label {
            background-color: #e74c3c;
            color: white;
            font-size: 0.8em;
            font-weight: normal;
            padding: 2px 6px;
            border-radius: 4px;
            margin-left: 10px;
        }
    </style>
</head>
<body>
<h1>Список отчетов</h1>
<ul>
{% for report in reports %}
    <li>
        <a href="{{ report.rel_path }}">{{ report.name }}</a>
        {% if loop.first %}
            <span class="new-label">NEW</span>
        {% endif %}
    </li>
{% endfor %}
</ul>
</body>
</html>

"""

class AttrDict(dict):
    def __getattr__(self, item):
        return self[item]

def save_html_report(
    results_by_bureau: Dict[str, Dict[str, List[Tuple[str, str]]]],
    stats_by_bureau: Dict[str, Dict[str, Dict[str, int]]],
    report_datetime: datetime
) -> Path:
    template = Template(REPORT_TEMPLATE)

    # Преобразуем словари в AttrDict
    stats_converted = {
        bureau: {
            name: AttrDict(stat) for name, stat in names.items()
        } for bureau, names in stats_by_bureau.items()
    }

    # Считаем итоги по каждому бюро и общие
    bureau_totals = {}
    grand_total = {"added": 0, "modified": 0}
    for bureau, users in stats_by_bureau.items():
        total_added = sum(user["added"] for user in users.values())
        total_modified = sum(user["modified"] for user in users.values())
        bureau_totals[bureau] = AttrDict({"added": total_added, "modified": total_modified})
        grand_total["added"] += total_added
        grand_total["modified"] += total_modified

    html = template.render(
        report_datetime=report_datetime,
        results_by_bureau=results_by_bureau,
        stats_by_bureau=stats_converted,
        bureau_totals=bureau_totals,
        grand_total=AttrDict(grand_total)
    )

    # Сохраняем в файл
    date_str = report_datetime.strftime("%Y-%m-%d")
    time_str = report_datetime.strftime("%H-%M-%S")

    base_dir = Path.home() / "Desktop" / "Отчет"
    report_dir = base_dir / "Все даты" / date_str
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / f"Отчет_{date_str}_{time_str}.html"
    report_path.write_text(html, encoding="utf-8")

    update_reports_index()

    return report_path

def update_reports_index():
    base_dir = Path.home() / "Desktop" / "Отчет"
    all_dates_dir = base_dir / "Все даты"

    # Ищем все html-файлы с отчетами во всех подкаталогах
    report_files = list(all_dates_dir.rglob("Отчет_*.html"))

    reports = []
    for file_path in report_files:
        # Парсим дату и время из имени файла Отчет_YYYY-MM-DD_HH-MM-SS.html
        try:
            parts = file_path.stem.split("_")  # ['Отчет', 'YYYY-MM-DD', 'HH-MM-SS']
            date_str, time_str = parts[1], parts[2]
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H-%M-%S")
        except Exception:
            dt = datetime.fromtimestamp(file_path.stat().st_mtime)

        reports.append({
            "name": file_path.name,
            "path": file_path,
            "rel_path": file_path.relative_to(base_dir).as_posix(),
            "date_time": dt
        })

    # Сортируем по дате — свежий сверху
    reports.sort(key=lambda x: x["date_time"], reverse=True)

    template = Template(INDEX_TEMPLATE)
    html = template.render(reports=reports)

    # Сохраняем индексный файл в корень base_dir
    index_path = base_dir / "отчет.html"
    index_path.write_text(html, encoding="utf-8")

    print(f"Обновлен файл отчетов: {index_path}")
