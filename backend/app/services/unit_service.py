"""Nghiệp vụ quản lý cơ cấu đơn vị."""
from __future__ import annotations

from ..common.exceptions import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from ..common.utils import clean_str, validate_email
from ..extensions import db
from ..models import OrganizationUnit
from ..models.enums import UNIT_TYPES
from ..repositories import unit_repository as repo
from .audit_service import record_audit


def _check_no_cycle(unit_id: int, new_parent_id: int | None) -> None:
    """Không cho tạo quan hệ cha–con gây vòng lặp.

    Đi ngược theo parent_id từ new_parent_id; nếu gặp lại unit_id -> có chu trình.
    """
    if new_parent_id is None:
        return
    if new_parent_id == unit_id:
        raise BusinessRuleError("Đơn vị không thể là cấp trên của chính nó.")
    seen: set[int] = set()
    cursor = repo.get_by_id(new_parent_id)
    if cursor is None:
        raise ValidationError("Đơn vị cấp trên không tồn tại.")
    while cursor is not None:
        if cursor.id == unit_id:
            raise BusinessRuleError(
                "Không thể đặt cấp trên là một đơn vị cấp dưới (gây vòng lặp)."
            )
        if cursor.id in seen:
            break
        seen.add(cursor.id)
        cursor = cursor.parent


def _validate_payload(data: dict, *, partial: bool = False) -> dict:
    out: dict = {}
    if not partial or "code" in data:
        code = clean_str(data.get("code"))
        if not code:
            raise ValidationError("Mã đơn vị là bắt buộc.")
        out["code"] = code
    if not partial or "name" in data:
        name = clean_str(data.get("name"))
        if not name:
            raise ValidationError("Tên đơn vị là bắt buộc.")
        out["name"] = name
    if not partial or "unit_type" in data:
        unit_type = clean_str(data.get("unit_type"))
        if unit_type not in UNIT_TYPES:
            raise ValidationError(
                f"Loại đơn vị phải thuộc: {', '.join(sorted(UNIT_TYPES))}."
            )
        out["unit_type"] = unit_type
    if "address" in data:
        out["address"] = clean_str(data.get("address"))
    if "phone" in data:
        out["phone"] = clean_str(data.get("phone"))
    if "email" in data:
        email = clean_str(data.get("email"))
        validate_email(email, "email")
        out["email"] = email
    if "is_active" in data:
        out["is_active"] = bool(data.get("is_active"))
    if "parent_id" in data:
        out["parent_id"] = data.get("parent_id")
    return out


def list_units(only_active: bool | None = None) -> list[dict]:
    return [u.to_dict(include_relations=True) for u in repo.list_all(only_active=only_active)]


def get_tree() -> list[dict]:
    return repo.build_tree(repo.list_all())


def get_unit(unit_id: int) -> dict:
    unit = repo.get_by_id(unit_id)
    if unit is None:
        raise NotFoundError("Không tìm thấy đơn vị.")
    data = unit.to_dict(include_relations=True)
    data["children"] = [
        c.to_dict() for c in sorted(unit.children, key=lambda x: x.code)
    ]
    return data


def create_unit(data: dict, *, actor, meta: dict) -> dict:
    payload = _validate_payload(data)
    if repo.get_by_code(payload["code"]):
        raise ConflictError("Mã đơn vị đã tồn tại.")

    parent_id = payload.get("parent_id")
    if parent_id:
        if repo.get_by_id(parent_id) is None:
            raise ValidationError("Đơn vị cấp trên không tồn tại.")

    unit = OrganizationUnit(
        code=payload["code"],
        name=payload["name"],
        unit_type=payload["unit_type"],
        parent_id=parent_id,
        address=payload.get("address"),
        phone=payload.get("phone"),
        email=payload.get("email"),
        is_active=payload.get("is_active", True),
    )
    db.session.add(unit)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="unit.create",
        entity_type="organization_unit",
        entity_id=unit.id,
        unit_id=unit.id,
        new_values=unit.to_dict(),
        **meta,
    )
    db.session.commit()
    return unit.to_dict(include_relations=True)


def update_unit(unit_id: int, data: dict, *, actor, meta: dict) -> dict:
    unit = repo.get_by_id(unit_id)
    if unit is None:
        raise NotFoundError("Không tìm thấy đơn vị.")

    payload = _validate_payload(data, partial=True)
    old = unit.to_dict()

    if "code" in payload and payload["code"] != unit.code:
        if repo.get_by_code(payload["code"]):
            raise ConflictError("Mã đơn vị đã tồn tại.")

    if "parent_id" in payload:
        _check_no_cycle(unit.id, payload["parent_id"])

    for key, value in payload.items():
        setattr(unit, key, value)

    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="unit.update",
        entity_type="organization_unit",
        entity_id=unit.id,
        unit_id=unit.id,
        old_values=old,
        new_values=unit.to_dict(),
        **meta,
    )
    db.session.commit()
    return unit.to_dict(include_relations=True)


def deactivate_unit(unit_id: int, *, actor, meta: dict) -> dict:
    """DELETE /units/{id}: chỉ ngừng hoạt động nếu đơn vị đã phát sinh dữ liệu.

    Không xóa cứng đơn vị đang có nhân sự hoặc dữ liệu lịch sử.
    """
    unit = repo.get_by_id(unit_id)
    if unit is None:
        raise NotFoundError("Không tìm thấy đơn vị.")

    old = unit.to_dict()
    if repo.has_dependent_data(unit.id):
        if not unit.is_active:
            raise ConflictError("Đơn vị đã ở trạng thái ngừng hoạt động.")
        unit.is_active = False
        action = "unit.deactivate"
        message = "Đơn vị có dữ liệu liên quan nên chỉ được ngừng hoạt động."
        hard_deleted = False
    else:
        db.session.delete(unit)
        action = "unit.delete"
        message = "Đã xóa đơn vị."
        hard_deleted = True

    db.session.flush()
    record_audit(
        user_id=actor.id,
        action=action,
        entity_type="organization_unit",
        entity_id=unit_id,
        unit_id=unit_id,
        old_values=old,
        new_values=None if hard_deleted else unit.to_dict(),
        **meta,
    )
    db.session.commit()
    return {"hard_deleted": hard_deleted, "message": message}
