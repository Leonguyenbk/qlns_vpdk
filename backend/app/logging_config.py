"""Cấu hình logging. Không ghi mật khẩu / token vào log."""
from __future__ import annotations

import logging
import sys

_SENSITIVE_KEYS = ("password", "token", "authorization", "secret", "refresh")


class RedactFilter(logging.Filter):
    """Che các từ khóa nhạy cảm xuất hiện trong message log."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage().lower()
            if any(k in msg for k in _SENSITIVE_KEYS):
                record.msg = "[đã ẩn nội dung nhạy cảm khỏi log]"
                record.args = ()
        except Exception:  # pragma: no cover - phòng hờ
            pass
        return True


def configure_logging(level: str = "INFO") -> None:
    # Bảo đảm console hiển thị được tiếng Việt (tránh lỗi trên Windows cp1252)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):  # pragma: no cover
            pass

    root = logging.getLogger()
    if root.handlers:
        for h in root.handlers:
            h.addFilter(RedactFilter())
        root.setLevel(level)
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    )
    handler.addFilter(RedactFilter())
    root.addHandler(handler)
    root.setLevel(level)
