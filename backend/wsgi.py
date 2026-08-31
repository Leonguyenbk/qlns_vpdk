"""Điểm vào WSGI / Flask CLI.

Sử dụng:
    flask --app wsgi run
    gunicorn "wsgi:app"
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app(os.getenv("FLASK_ENV"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
