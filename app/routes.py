from flask import render_template, request, jsonify
from app.sync_core import start_sync
from app.reporter import generate_html_report

def register_routes(app):
    @app.route('/')
    def index():
        # Пример логов для отображения на веб-странице
        logs = [
            "Запуск синхронизации файлов...",
            "Начинается синхронизация. dry_run=False, skip_telegram=False",
            "Источники: /mnt/shared/101, /mnt/shared/102",
            "Синхронизация завершена успешно.",
        ]
        return render_template('index.html', logs=logs)

    @app.route("/start_sync", methods=["POST"])
    def sync():
        dry_run = request.form.get("dry_run") == "on"
        skip_telegram = request.form.get("skip_telegram") == "on"
        report_html = request.form.get("report_html") == "on"
        report_path = request.form.get("report_path")  # Если указан путь для отчета

        try:
            # Запуск синхронизации
            start_sync(
                dry_run=dry_run,
                skip_telegram=skip_telegram,
                report_html=report_html,
                report_path=report_path  # передаем путь к отчету
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
