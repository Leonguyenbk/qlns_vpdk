"""Nghiệp vụ quản lý tài khoản, gán vai trò và phạm vi đơn vị."""
from __future__ import annotations

import secrets

from ..common.exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from ..common.utils import clean_str, parse_pagination, validate_email
from ..extensions import db
from ..models import Employee, OrganizationUnit, Role, User, UserUnitScope
from ..permissions.constants import ROLE_SYSTEM_ADMIN
from .audit_service import record_audit
from .auth_service import revoke_all_for_user


def _actor_is_system_admin(actor: User) -> bool:
    return ROLE_SYSTEM_ADMIN in actor.role_codes()


def _protect_system_admin_target(actor: User, target: User) -> None:
    """Không cho tài khoản không phải Quản trị hệ thống chỉnh sửa tài khoản Quản trị hệ thống."""
    if ROLE_SYSTEM_ADMIN in target.role_codes() and not _actor_is_system_admin(actor):
        raise PermissionDeniedError(
            "Chỉ Quản trị hệ thống mới được thao tác trên tài khoản Quản trị hệ thống."
        )


def list_users(args) -> dict:
    page, page_size = parse_pagination(args)
    q = db.session.query(User)
    keyword = clean_str(args.get("keyword") or args.get("q"))
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(db.or_(User.username.ilike(like), User.full_name.ilike(like), User.email.ilike(like)))
    if args.get("is_active") in ("0", "1", "true", "false"):
        q = q.filter(User.is_active.is_(str(args.get("is_active")).lower() in ("1", "true")))
    total = q.count()
    rows = q.order_by(User.username).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [u.to_dict(include_permissions=True) for u in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def get_user(user_id: int) -> dict:
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản.")
    return user.to_dict(include_permissions=True)


def create_user(data: dict, *, actor, meta: dict) -> dict:
    username = clean_str(data.get("username"))
    password = data.get("password")
    full_name = clean_str(data.get("full_name"))
    email = clean_str(data.get("email"))

    if not username or not password or not full_name:
        raise ValidationError("Tên đăng nhập, mật khẩu và họ tên là bắt buộc.")
    if len(password) < 8:
        raise ValidationError("Mật khẩu phải có ít nhất 8 ký tự.")
    validate_email(email, "email")
    if db.session.query(User).filter(User.username == username).first():
        raise ConflictError("Tên đăng nhập đã tồn tại.")
    if email and db.session.query(User).filter(User.email == email).first():
        raise ConflictError("Email đã được sử dụng.")

    user = User(username=username, full_name=full_name, email=email, is_active=bool(data.get("is_active", True)))
    user.set_password(password)
    if data.get("employee_id"):
        employee_id = int(data["employee_id"])
        if db.session.get(Employee, employee_id) is None:
            raise ValidationError("Nhân sự liên kết không tồn tại.")
        user.employee_id = employee_id

    db.session.add(user)
    db.session.flush()

    role_ids = data.get("role_ids") or []
    if role_ids:
        _set_roles(actor, user, role_ids)

    record_audit(
        user_id=actor.id,
        action="user.create",
        entity_type="user",
        entity_id=user.id,
        new_values={"username": username, "full_name": full_name, "email": email},
        **meta,
    )
    db.session.commit()
    return user.to_dict(include_permissions=True)


def update_user(user_id: int, data: dict, *, actor, meta: dict) -> dict:
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản.")
    _protect_system_admin_target(actor, user)

    old = {"full_name": user.full_name, "email": user.email, "is_active": user.is_active}
    if "full_name" in data:
        fn = clean_str(data.get("full_name"))
        if not fn:
            raise ValidationError("Họ tên không được để trống.")
        user.full_name = fn
    if "email" in data:
        email = clean_str(data.get("email"))
        validate_email(email, "email")
        if email and db.session.query(User).filter(User.email == email, User.id != user.id).first():
            raise ConflictError("Email đã được sử dụng.")
        user.email = email
    if "is_active" in data:
        new_active = bool(data.get("is_active"))
        if not new_active and user.id == actor.id:
            raise ConflictError("Không thể tự khóa tài khoản của chính mình.")
        user.is_active = new_active
        if not new_active:
            revoke_all_for_user(user.id)
    if "employee_id" in data:
        employee_id = int(data["employee_id"]) if data.get("employee_id") else None
        if employee_id and db.session.get(Employee, employee_id) is None:
            raise ValidationError("Nhân sự liên kết không tồn tại.")
        user.employee_id = employee_id

    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="user.update",
        entity_type="user",
        entity_id=user.id,
        old_values=old,
        new_values={"full_name": user.full_name, "email": user.email, "is_active": user.is_active},
        **meta,
    )
    db.session.commit()
    return user.to_dict(include_permissions=True)


def reset_password(user_id: int, data: dict, *, actor, meta: dict) -> dict:
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản.")
    _protect_system_admin_target(actor, user)

    new_password = data.get("new_password") or _random_password()
    if len(new_password) < 8:
        raise ValidationError("Mật khẩu phải có ít nhất 8 ký tự.")
    user.set_password(new_password)
    revoke_all_for_user(user.id)
    record_audit(
        user_id=actor.id,
        action="user.reset_password",
        entity_type="user",
        entity_id=user.id,
        **meta,
    )
    db.session.commit()
    # Trả mật khẩu tạm nếu do hệ thống sinh (không ghi vào audit/log)
    return {"generated": not bool(data.get("new_password")), "new_password": new_password if not data.get("new_password") else None}


def _set_roles(actor, user: User, role_ids: list[int]) -> list[int]:
    roles = db.session.query(Role).filter(Role.id.in_([int(r) for r in role_ids])).all()
    found_ids = {r.id for r in roles}
    missing = set(int(r) for r in role_ids) - found_ids
    if missing:
        raise ValidationError(f"Vai trò không tồn tại: {sorted(missing)}.")
    # Chỉ Quản trị hệ thống mới được gán vai trò SYSTEM_ADMIN
    if any(r.code == ROLE_SYSTEM_ADMIN for r in roles) and not _actor_is_system_admin(actor):
        raise PermissionDeniedError("Chỉ Quản trị hệ thống mới được gán vai trò Quản trị hệ thống.")
    user.roles = roles
    return sorted(found_ids)


def set_roles(user_id: int, data: dict, *, actor, meta: dict) -> dict:
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản.")
    _protect_system_admin_target(actor, user)
    old = sorted(r.id for r in user.roles)
    role_ids = data.get("role_ids", [])
    _set_roles(actor, user, role_ids)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="user.set_roles",
        entity_type="user",
        entity_id=user.id,
        old_values={"role_ids": old},
        new_values={"role_ids": sorted(r.id for r in user.roles)},
        **meta,
    )
    db.session.commit()
    return user.to_dict(include_permissions=True)


def set_unit_scopes(user_id: int, data: dict, *, actor, meta: dict) -> dict:
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản.")
    _protect_system_admin_target(actor, user)

    scopes_in = data.get("scopes", [])
    if not isinstance(scopes_in, list):
        raise ValidationError("Danh sách phạm vi không hợp lệ.")

    old = [s.to_dict() for s in user.unit_scopes]
    new_scopes: list[UserUnitScope] = []
    for item in scopes_in:
        stype = clean_str((item or {}).get("scope_type"))
        if stype not in ("GLOBAL", "UNIT", "SUBTREE"):
            raise ValidationError("scope_type phải là GLOBAL, UNIT hoặc SUBTREE.")
        unit_id = item.get("unit_id")
        if stype == "GLOBAL":
            unit_id = None
        else:
            if not unit_id or db.session.get(OrganizationUnit, int(unit_id)) is None:
                raise ValidationError("Đơn vị của phạm vi không tồn tại.")
            unit_id = int(unit_id)
        new_scopes.append(UserUnitScope(user_id=user.id, scope_type=stype, unit_id=unit_id))

    user.unit_scopes = new_scopes
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="user.set_unit_scopes",
        entity_type="user",
        entity_id=user.id,
        old_values={"scopes": old},
        new_values={"scopes": [s.to_dict() for s in user.unit_scopes]},
        **meta,
    )
    db.session.commit()
    return user.to_dict(include_permissions=True)


def _random_password(length: int = 12) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))
