"""Điểm vào cho phát triển:  python app.py   (http://0.0.0.0:$PORT, mặc định 5050)

Triển khai thật dùng:  waitress-serve --host=0.0.0.0 --port=5050 wsgi:app
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app(os.getenv("FLASK_ENV"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5050")), debug=True)
