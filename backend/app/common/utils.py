"""Tiện ích dùng chung: thời gian UTC, phân trang, ép kiểu."""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any

from .exceptions import ValidationError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+()\-\s]{8,20}$")


def utcnow() -> datetime:
    """Thời điểm hiện tại theo UTC, luôn timezone-aware."""
    return datetime.now(timezone.utc)


def ensure_aware(value: datetime | None) -> datetime | None:
    """Chuẩn hóa datetime về timezone-aware (UTC).

    MySQL trả về datetime có tz, SQLite trả về naive; hàm này giúp so sánh an toàn
    trên cả hai backend.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def parse_pagination(args, default_size: int = 20, max_size: int = 100) -> tuple[int, int]:
    try:
        page = int(args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(args.get("page_size", default_size))
    except (TypeError, ValueError):
        page_size = default_size
    page = max(page, 1)
    page_size = min(max(page_size, 1), max_size)
    return page, page_size


def parse_date(value: Any, field: str) -> date | None:
    if value in (None, "", "null"):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValidationError(f"Trường '{field}' phải theo định dạng YYYY-MM-DD.") from exc


def validate_email(value: str | None, field: str = "email") -> None:
    if value and not EMAIL_RE.match(value):
        raise ValidationError(f"Trường '{field}' không đúng định dạng email.")


def validate_phone(value: str | None, field: str = "phone") -> None:
    if value and not PHONE_RE.match(value):
        raise ValidationError(f"Trường '{field}' không đúng định dạng số điện thoại.")


def clean_str(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None
