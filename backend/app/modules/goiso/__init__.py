"""Module Goiso (gọi số / kiosk) — Phase 3.

Ở phase này code goiso được bê gần như nguyên trạng:
- `legacy_db.py`   : truy cập SQLite (`hethong_v2.db`) — tạm giữ, Phase 6 chuyển sang MySQL.
- `queue_logic.py` / `booking_logic.py` / `tts.py` : nghiệp vụ, không đổi.
- `legacy_app.py`  : toàn bộ route cũ, chuyển Flask -> Blueprint `goiso`.

`configure_goiso(app)` gắn vài cấu hình cấp app mà goiso cần (session cookie cho
trang Jinja, tắt cache file tĩnh). Đăng ký blueprint làm ở `app.modules`.
"""
from __future__ import annotations

import os

from flask import Flask


def configure_goiso(app: Flask) -> None:
    """Cấu hình cấp app cho module goiso. An toàn với phần nhân sự (dùng JWT)."""
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    # Chỉ ép Secure khi không phải môi trường debug/local
    app.config.setdefault("SESSION_COOKIE_SECURE", not app.config.get("DEBUG", False))
    # Trang goiso nạp lại JS/CSS mỗi lần (tránh Cloudflare giữ bản cũ)
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    cookie_domain = os.getenv("COOKIE_DOMAIN", "").strip()
    if cookie_domain:
        app.config["SESSION_COOKIE_DOMAIN"] = cookie_domain

    # Schema goiso_* do Alembic (0006_goiso_tables) quản lý — không cần init runtime.
