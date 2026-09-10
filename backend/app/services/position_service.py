"""Nghiệp vụ quản lý chức vụ và giới hạn chức vụ theo đơn vị."""
from __future__ import annotations

from ..common.exceptions import ConflictError, NotFoundError, ValidationError
from ..common.utils import clean_str
from ..extensions import db
from ..models import EmployeeAssignment, OrganizationUnit, Position, UnitPositionLimit
from .audit_service import record_audit


def _active_holder_count(unit_id: int, position_id: int) -> int:
    return (
        db.session.query(EmployeeAssignment.id)
        .filter(
            EmployeeAssignment.unit_id == unit_id,
            EmployeeAssignment.position_id == position_id,
            EmployeeAssignment.is_primary.is_(True),
            EmployeeAssignment.end_date.is_(None),
        )
        .count()
    )


def _assert_limit_not_below_active_holders(
    unit_id: int, position_id: int, max_holders: int | None
) -> None:
    if max_holders is None:
        return
    active_count = _active_holder_count(unit_id, position_id)
    if active_count > max_holders:
        raise ConflictError(
            "Không thể đặt giới hạn thấp hơn số người đang giữ chức vụ.",
            payload={
                "conflict": "POSITION_LIMIT_BELOW_ACTIVE_HOLDERS",
                "unit_id": unit_id,
                "position_id": position_id,
                "active_holders": active_count,
                "requested_limit": max_holders,
            },
        )


def list_positions(only_active: bool | None = None) -> list[dict]:
    q = db.session.query(Position)
    if only_active is True:
        q = q.filter(Position.is_active.is_(True))
    return [p.to_dict() for p in q.order_by(Position.level.desc(), Position.code).all()]


def _validate(data: dict, partial: bool = False) -> dict:
    out: dict = {}
    if not partial or "code" in data:
        code = clean_str(data.get("code"))
        if not code:
            raise ValidationError("Mã chức vụ là bắt buộc.")
        out["code"] = code
    if not partial or "name" in data:
        name = clean_str(data.get("name"))
        if not name:
            raise ValidationError("Tên chức vụ là bắt buộc.")
        out["name"] = name
    if "level" in data:
        try:
            out["level"] = int(data.get("level") or 0)
        except (TypeError, ValueError):
            raise ValidationError("Cấp bậc (level) phải là số nguyên.")
    if "description" in data:
        out["description"] = clean_str(data.get("description"))
    if "is_managerial" in data:
        out["is_managerial"] = bool(data.get("is_managerial"))
    if "is_active" in data:
        out["is_active"] = bool(data.get("is_active"))
    return out


def create_position(data: dict, *, actor, meta: dict) -> dict:
    payload = _validate(data)
    if db.session.query(Position).filter(Position.code == payload["code"]).first():
        raise ConflictError("Mã chức vụ đã tồn tại.")
    pos = Position(
        code=payload["code"],
        name=payload["name"],
        level=payload.get("level", 0),
        description=payload.get("description"),
        is_managerial=payload.get("is_managerial", False),
        is_active=payload.get("is_active", True),
    )
    db.session.add(pos)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="position.create",
        entity_type="position",
        entity_id=pos.id,
        new_values=pos.to_dict(),
        **meta,
    )
    db.session.commit()
    return pos.to_dict()


def update_position(position_id: int, data: dict, *, actor, meta: dict) -> dict:
    pos = db.session.get(Position, position_id)
    if pos is None:
        raise NotFoundError("Không tìm thấy chức vụ.")
    payload = _validate(data, partial=True)
    old = pos.to_dict()
    if "code" in payload and payload["code"] != pos.code:
        if db.session.query(Position).filter(Position.code == payload["code"]).first():
            raise ConflictError("Mã chức vụ đã tồn tại.")
    for k, v in payload.items():
        setattr(pos, k, v)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="position.update",
        entity_type="position",
        entity_id=pos.id,
        old_values=old,
        new_values=pos.to_dict(),
        **meta,
    )
    db.session.commit()
    return pos.to_dict()


def delete_position(position_id: int, *, actor, meta: dict) -> dict:
    pos = db.session.get(Position, position_id)
    if pos is None:
        raise NotFoundError("Không tìm thấy chức vụ.")
    in_use = (
        db.session.query(EmployeeAssignment.id)
        .filter(EmployeeAssignment.position_id == position_id)
        .first()
        is not None
    )
    old = pos.to_dict()
    if in_use:
        # Có dữ liệu lịch sử -> chỉ ngừng hoạt động
        pos.is_active = False
        action = "position.deactivate"
        hard = False
    else:
        db.session.query(UnitPositionLimit).filter(
            UnitPositionLimit.position_id == position_id
        ).delete()
        db.session.delete(pos)
        action = "position.delete"
        hard = True
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action=action,
        entity_type="position",
        entity_id=position_id,
        old_values=old,
        new_values=None if hard else pos.to_dict(),
        **meta,
    )
    db.session.commit()
    return {"hard_deleted": hard}


# ----------------- Giới hạn chức vụ theo đơn vị -----------------
def list_limits(unit_id: int) -> list[dict]:
    if db.session.get(OrganizationUnit, unit_id) is None:
        raise NotFoundError("Không tìm thấy đơn vị.")
    rows = (
        db.session.query(UnitPositionLimit)
        .filter(UnitPositionLimit.unit_id == unit_id)
        .all()
    )
    return [r.to_dict() for r in rows]


def create_limit(unit_id: int, data: dict, *, actor, meta: dict) -> dict:
    if db.session.get(OrganizationUnit, unit_id) is None:
        raise NotFoundError("Không tìm thấy đơn vị.")
    position_id = data.get("position_id")
    if not position_id or db.session.get(Position, int(position_id)) is None:
        raise ValidationError("Chức vụ không hợp lệ.")
    max_holders = data.get("max_holders")
    if max_holders is not None:
        try:
            max_holders = int(max_holders)
            if max_holders < 1:
                raise ValueError
        except (TypeError, ValueError):
            raise ValidationError("Số lượng tối đa phải là số nguyên dương hoặc bỏ trống (không giới hạn).")

    exists = (
        db.session.query(UnitPositionLimit)
        .filter(
            UnitPositionLimit.unit_id == unit_id,
            UnitPositionLimit.position_id == int(position_id),
        )
        .first()
    )
    if exists:
        raise ConflictError("Đã tồn tại cấu hình giới hạn cho chức vụ này tại đơn vị.")

    _assert_limit_not_below_active_holders(unit_id, int(position_id), max_holders)

    limit = UnitPositionLimit(
        unit_id=unit_id, position_id=int(position_id), max_holders=max_holders
    )
    db.session.add(limit)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="position_limit.create",
        entity_type="unit_position_limit",
        entity_id=limit.id,
        unit_id=unit_id,
        new_values=limit.to_dict(),
        **meta,
    )
    db.session.commit()
    return limit.to_dict()


def update_limit(unit_id: int, limit_id: int, data: dict, *, actor, meta: dict) -> dict:
    limit = db.session.get(UnitPositionLimit, limit_id)
    if limit is None or limit.unit_id != unit_id:
        raise NotFoundError("Không tìm thấy cấu hình giới hạn chức vụ.")
    old = limit.to_dict()
    max_holders = data.get("max_holders")
    if max_holders is not None:
        try:
            max_holders = int(max_holders)
            if max_holders < 1:
                raise ValueError
        except (TypeError, ValueError):
            raise ValidationError("Số lượng tối đa phải là số nguyên dương hoặc bỏ trống.")
    _assert_limit_not_below_active_holders(
        unit_id, limit.position_id, max_holders
    )
    limit.max_holders = max_holders
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="position_limit.update",
        entity_type="unit_position_limit",
        entity_id=limit.id,
        unit_id=unit_id,
        old_values=old,
        new_values=limit.to_dict(),
        **meta,
    )
    db.session.commit()
    return limit.to_dict()
