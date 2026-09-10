"""Dịch vụ ghi nhật ký thao tác.

Lưu ý: KHÔNG ghi password_hash, token hay dữ liệu bí mật vào audit log.
"""
from __future__ import annotations

from typing import Any

from ..extensions import db
from ..models import AuditLog

_REDACT_FIELDS = {
    "password",
    "password_hash",
    "new_password",
    "old_password",
    "raw_password",
    "token",
    "refresh_token",
    "access_token",
    "secret",
}


def _sanitize(values: dict | None) -> dict | None:
    if not values:
        return values
    clean = {}
    for k, v in values.items():
        if k.lower() in _REDACT_FIELDS:
            continue
        clean[k] = v
    return clean or None


def record_audit(
    *,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: Any = None,
    unit_id: int | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    flush: bool = True,
) -> AuditLog:
    """Tạo bản ghi audit trong cùng session/transaction hiện tại.

    Không tự commit — để thao tác nghiệp vụ kiểm soát transaction.
    """
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        unit_id=unit_id,
        old_values=_sanitize(old_values),
        new_values=_sanitize(new_values),
        ip_address=ip_address,
        user_agent=(user_agent or "")[:255] or None,
    )
    db.session.add(log)
    if flush:
        db.session.flush()
    return log
