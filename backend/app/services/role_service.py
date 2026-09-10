"""Nghiệp vụ quản lý vai trò và quyền."""
from __future__ import annotations

from ..common.exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from ..common.utils import clean_str
from ..extensions import db
from ..models import Permission, Role, User
from ..permissions.constants import ROLE_SYSTEM_ADMIN
from .audit_service import record_audit


def list_roles() -> list[dict]:
    return [r.to_dict() for r in db.session.query(Role).order_by(Role.code).all()]


def list_permissions() -> list[dict]:
    return [p.to_dict() for p in db.session.query(Permission).order_by(Permission.code).all()]


def _resolve_permissions(codes: list[str]) -> list[Permission]:
    codes = [clean_str(c) for c in (codes or []) if clean_str(c)]
    perms = db.session.query(Permission).filter(Permission.code.in_(codes)).all()
    found = {p.code for p in perms}
    missing = set(codes) - found
    if missing:
        raise ValidationError(f"Quyền không tồn tại: {sorted(missing)}.")
    return perms


def create_role(data: dict, *, actor, meta: dict) -> dict:
    code = clean_str(data.get("code"))
    name = clean_str(data.get("name"))
    if not code or not name:
        raise ValidationError("Mã và tên vai trò là bắt buộc.")
    if db.session.query(Role).filter(Role.code == code).first():
        raise ConflictError("Mã vai trò đã tồn tại.")
    role = Role(
        code=code,
        name=name,
        description=clean_str(data.get("description")),
        is_system=False,
    )
    role.permissions = _resolve_permissions(data.get("permissions", []))
    db.session.add(role)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="role.create",
        entity_type="role",
        entity_id=role.id,
        new_values=role.to_dict(),
        **meta,
    )
    db.session.commit()
    return role.to_dict()


def update_role(role_id: int, data: dict, *, actor, meta: dict) -> dict:
    role = db.session.get(Role, role_id)
    if role is None:
        raise NotFoundError("Không tìm thấy vai trò.")
    # Không cho chỉnh sửa quyền của vai trò Quản trị hệ thống trừ khi chính là Quản trị hệ thống
    if role.code == ROLE_SYSTEM_ADMIN and ROLE_SYSTEM_ADMIN not in actor.role_codes():
        raise PermissionDeniedError("Không được chỉnh sửa vai trò Quản trị hệ thống.")

    old = role.to_dict()
    if "name" in data:
        name = clean_str(data.get("name"))
        if not name:
            raise ValidationError("Tên vai trò không được để trống.")
        role.name = name
    if "description" in data:
        role.description = clean_str(data.get("description"))
    if "permissions" in data:
        if role.code == ROLE_SYSTEM_ADMIN:
            raise ConflictError("Không thể thay đổi quyền của vai trò Quản trị hệ thống.")
        role.permissions = _resolve_permissions(data.get("permissions", []))

    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="role.update",
        entity_type="role",
        entity_id=role.id,
        old_values=old,
        new_values=role.to_dict(),
        **meta,
    )
    db.session.commit()
    return role.to_dict()


def delete_role(role_id: int, *, actor, meta: dict) -> dict:
    role = db.session.get(Role, role_id)
    if role is None:
        raise NotFoundError("Không tìm thấy vai trò.")
    if role.is_system:
        raise ConflictError("Không thể xóa vai trò hệ thống.")
    in_use = db.session.query(User).filter(User.roles.any(Role.id == role_id)).first()
    if in_use:
        raise ConflictError("Vai trò đang được gán cho tài khoản, không thể xóa.")
    old = role.to_dict()
    db.session.delete(role)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="role.delete",
        entity_type="role",
        entity_id=role_id,
        old_values=old,
        **meta,
    )
    db.session.commit()
    return {"id": role_id, "deleted": True}
