"""Cầu nối danh tính: tài khoản platform (JWT) -> "user" theo hình dạng goiso.

Các decorator/API cũ của goiso (admin_required, counter_guard...) mong đợi
dict user dạng:
    {id, username, full_name, role in {"admin","staff"}, branch_id, branch_code,
     active, perms: [..], _platform: True}

goiso đọc JWT platform (header hoặc cookie) — không còn phiên riêng (session/SQLite
users) từ khi tài khoản goiso được di trú vào bảng `users` chung.
"""
from __future__ import annotations

from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from ...extensions import db
from ...models import User
from . import legacy_db

_GOISO_ADMIN_ROLES = {"SYSTEM_ADMIN", "GOISO_ADMIN"}


def platform_user_to_goiso(user: User) -> dict:
    role_codes = user.role_codes()
    perms = sorted(user.permission_codes())
    is_admin = bool(_GOISO_ADMIN_ROLES & role_codes) or "goiso.admin" in perms

    branch_id = None
    if user.goiso_branch_code:
        b = legacy_db.get_branch(user.goiso_branch_code)
        branch_id = b["id"] if b else None

    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": "admin" if is_admin else "staff",
        "branch_id": branch_id,
        "branch_code": user.goiso_branch_code,
        "active": user.is_active,
        "perms": perms,
        "_platform": True,
    }


def current_platform_user_as_goiso() -> dict | None:
    """Trả về user goiso-shaped nếu request mang JWT access hợp lệ, ngược lại None."""
    try:
        verify_jwt_in_request(optional=True)
    except Exception:  # noqa: BLE001 — token hỏng/hết hạn: coi như chưa đăng nhập
        return None

    identity = get_jwt_identity()
    if not identity:
        return None
    try:
        if get_jwt().get("type") not in (None, "access"):
            return None
    except Exception:  # noqa: BLE001
        return None

    user = db.session.get(User, int(identity))
    if user is None or not user.is_active:
        return None
    return platform_user_to_goiso(user)
