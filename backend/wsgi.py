"""Điểm vào WSGI / Flask CLI.

Sử dụng:
    flask --app wsgi run
    gunicorn "wsgi:app"
"""
from __future__ import annotations
from apscheduler.schedulers.background import BackgroundScheduler
from cronjob import my_task
from datetime import datetime

import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app(os.getenv("FLASK_ENV"))

scheduler = BackgroundScheduler()
scheduler.add_job(my_task, 'interval', hours=3, next_run_time=datetime.now())
scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), use_reloader=False)
