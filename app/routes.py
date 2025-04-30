#routes.py
import io


from flask import render_template, request, jsonify

from app.reporter import generate_html_report
from app.sync_core import start_sync

# Инклюд логирования в реальном времени
log_output = io.StringIO()  # Стрим для вывода логов в Flask


def register_routes(app):
    @app.route('/')
    def index():
        # Здесь выводим последние несколько строк логов
        logs = log_output.getvalue().splitlines()[-10:]  # Последние 10 строк
        return render_template('index.html', logs=logs)

    @app.route("/start_sync", methods=["POST"])
    def sync():
        dry_run = request.form.get("dry_run") == "on"
        skip_telegram = request.form.get("skip_telegram") == "on"
        report_html = request.form.get("report_html") == "on"
        report_path = request.form.get("report_path")  # Если указан путь для отчета

        # Перенаправление логов в StringIO (для записи в реальном времени)
        log_output.seek(0)
        log_output.truncate(0)

        try:
            # Запуск синхронизации
            start_sync(
                dry_run=dry_run,
                skip_telegram=skip_telegram,
                report_html=report_html,
                report_path=report_path,
                log_output=log_output  # Передаем для записи логов
            )
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    @app.route("/generate_report")
    def report():
        try:
            # Генерация отчета
            generate_html_report()
            return jsonify({"status": "ok"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
