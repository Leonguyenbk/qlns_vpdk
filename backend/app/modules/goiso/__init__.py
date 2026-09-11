"""Module Goiso (gọi số / kiosk).

- `legacy_db.py`   : truy cập CSDL (bảng `goiso_*`, MySQL từ Phase 6) qua một
  shim SQLAlchemy — giữ nguyên SQL/nghiệp vụ của bản gốc.
- `queue_logic.py` / `booking_logic.py` / `tts.py` : nghiệp vụ, không đổi.
- `legacy_app.py`  : blueprint `goiso` — CHỈ còn API JSON (cấp số, quầy, đặt
  lịch, quản trị...). Giao diện (bàn gọi số, màn hình, bảng chờ, đặt lịch,
  quản trị) do Portal React phục vụ — xem frontend/src/pages/goiso/ và
  frontend/src/pages/admin/. Không còn Jinja/template ở module này.

`configure_goiso(app)` gắn cấu hình cấp app mà goiso cần. Đăng ký blueprint
làm ở `app.modules`.
"""
from __future__ import annotations

from flask import Flask


def configure_goiso(app: Flask) -> None:
    """Cấu hình cấp app cho module goiso. An toàn với phần nhân sự (dùng JWT).

    Schema goiso_* do Alembic (0006_goiso_tables) quản lý — không cần init runtime.
    """
    return None
