"""Nghiệp vụ hồ sơ nhân sự: CRUD, soft delete/restore, quá trình công tác, chuyển đơn vị."""
from __future__ import annotations

from datetime import timedelta

from ..common.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from ..common.utils import clean_str, parse_date, utcnow, validate_email, validate_phone
from ..extensions import db
from ..models import Employee, EmployeeAssignment, OrganizationUnit, Position
from ..models.enums import (
    ASSIGNMENT_TYPES,
    EMPLOYEE_STATUSES,
    EMPLOYMENT_TYPES,
    GENDERS,
)
from ..permissions import constants as perms
from ..repositories import employee_repository as repo
from .assignment_service import (
    assert_no_primary_overlap,
    assign_primary,
    check_position_capacity,
    end_assignment,
)
from .audit_service import record_audit

# ---- Các trường hồ sơ được phép cập nhật trực tiếp (KHÔNG gồm đơn vị/chức vụ) ----
_PROFILE_FIELDS = {
    "full_name",
    "date_of_birth",
    "gender",
    "identity_number",
    "phone",
    "email",
    "address",
    "professional_title",
    "employment_type",
    "recruitment_date",
    "status",
    "avatar_url",
    "notes",
}


def _validate_profile(data: dict, *, partial: bool) -> dict:
    out: dict = {}

    if not partial or "employee_code" in data:
        code = clean_str(data.get("employee_code"))
        if not code:
            raise ValidationError("Mã nhân sự là bắt buộc.")
        out["employee_code"] = code

    if not partial or "full_name" in data:
        name = clean_str(data.get("full_name"))
        if not name:
            raise ValidationError("Họ tên là bắt buộc.")
        out["full_name"] = name

    if "date_of_birth" in data:
        out["date_of_birth"] = parse_date(data.get("date_of_birth"), "date_of_birth")
    if "recruitment_date" in data:
        out["recruitment_date"] = parse_date(data.get("recruitment_date"), "recruitment_date")

    if "gender" in data and data.get("gender") is not None:
        g = clean_str(data.get("gender"))
        if g and g not in GENDERS:
            raise ValidationError(f"Giới tính phải thuộc: {', '.join(sorted(GENDERS))}.")
        out["gender"] = g

    if "employment_type" in data and data.get("employment_type") is not None:
        et = clean_str(data.get("employment_type"))
        if et and et not in EMPLOYMENT_TYPES:
            raise ValidationError(
                f"Loại nhân sự phải thuộc: {', '.join(sorted(EMPLOYMENT_TYPES))}."
            )
        out["employment_type"] = et

    if "status" in data and data.get("status") is not None:
        st = clean_str(data.get("status"))
        if st not in EMPLOYEE_STATUSES:
            raise ValidationError(
                f"Trạng thái phải thuộc: {', '.join(sorted(EMPLOYEE_STATUSES))}."
            )
        out["status"] = st

    if "email" in data:
        email = clean_str(data.get("email"))
        validate_email(email, "email")
        out["email"] = email
    if "phone" in data:
        phone = clean_str(data.get("phone"))
        validate_phone(phone, "phone")
        out["phone"] = phone

    for f in ("identity_number", "address", "professional_title", "avatar_url", "notes"):
        if f in data:
            out[f] = clean_str(data.get(f))

    return out


def _can_view_sensitive(actor) -> bool:
    return actor.has_permission(perms.EMPLOYEE_VIEW_SENSITIVE)


def _assert_scope(actor, scope, unit_id: int | None, *, action: str = "truy cập") -> None:
    if not scope.allows_unit(unit_id):
        raise PermissionDeniedError(
            f"Bạn không có quyền {action} nhân sự thuộc đơn vị này (ngoài phạm vi được phân công)."
        )


# ----------------------------- Đọc -----------------------------
def list_employees(args, *, actor, scope) -> dict:
    from ..common.utils import parse_pagination

    page, page_size = parse_pagination(args)
    rows, total = repo.search(
        scope=scope,
        keyword=args.get("keyword") or args.get("q"),
        unit_id=_to_int(args.get("unit_id")),
        position_id=_to_int(args.get("position_id")),
        status=clean_str(args.get("status")),
        employment_type=clean_str(args.get("employment_type")),
        include_deleted=str(args.get("include_deleted", "")).lower() in ("1", "true", "yes"),
        sort=args.get("sort", "updated_at"),
        order=args.get("order", "desc"),
        page=page,
        page_size=page_size,
    )
    include_sensitive = _can_view_sensitive(actor)
    items = [e.to_dict(include_sensitive=include_sensitive) for e in rows]
    return {"items": items, "page": page, "page_size": page_size, "total": total}


def get_employee(employee_id: int, *, actor, scope, include_deleted: bool = False) -> dict:
    emp = repo.get_by_id(employee_id, include_deleted=include_deleted)
    if emp is None:
        raise NotFoundError("Không tìm thấy nhân sự.")
    current = emp.primary_active_assignment()
    _assert_scope(actor, scope, current.unit_id if current else None, action="xem")
    data = emp.to_dict(include_sensitive=_can_view_sensitive(actor))
    data["assignments"] = [a.to_dict() for a in emp.assignments]
    return data


def list_assignments(employee_id: int, *, actor, scope) -> list[dict]:
    emp = repo.get_by_id(employee_id, include_deleted=True)
    if emp is None:
        raise NotFoundError("Không tìm thấy nhân sự.")
    current = emp.primary_active_assignment()
    _assert_scope(actor, scope, current.unit_id if current else None, action="xem lịch sử")
    return [a.to_dict() for a in emp.assignments]


# ----------------------------- Ghi -----------------------------
def create_employee(data: dict, *, actor, scope, meta: dict) -> dict:
    payload = _validate_profile(data, partial=False)

    if repo.get_by_code(payload["employee_code"]):
        raise ConflictError("Mã nhân sự đã tồn tại.")

    # Phân công ban đầu (bắt buộc để xác định đơn vị/chức vụ hiện tại)
    unit_id = _to_int(data.get("unit_id"))
    position_id = _to_int(data.get("position_id"))
    if not unit_id or not position_id:
        raise ValidationError("Cần chọn đơn vị và chức vụ khi tạo hồ sơ nhân sự.")

    unit = db.session.get(OrganizationUnit, unit_id)
    position = db.session.get(Position, position_id)
    if unit is None or not unit.is_active:
        raise ValidationError("Đơn vị không tồn tại hoặc đã ngừng hoạt động.")
    if position is None or not position.is_active:
        raise ValidationError("Chức vụ không tồn tại hoặc đã ngừng hoạt động.")

    _assert_scope(actor, scope, unit_id, action="thêm")

    start_date = parse_date(
        data.get("recruitment_date") or data.get("start_date"), "start_date"
    ) or utcnow().date()
    replace_existing = _as_bool(data.get("replace_existing"))

    try:
        emp = Employee(
            employee_code=payload["employee_code"],
            full_name=payload["full_name"],
            status=payload.get("status", "WORKING"),
        )
        for f in _PROFILE_FIELDS:
            if f in payload:
                setattr(emp, f, payload[f])
        db.session.add(emp)
        db.session.flush()

        assign_primary(
            employee=emp,
            unit_id=unit_id,
            position_id=position_id,
            assignment_type="RECRUITMENT",
            start_date=start_date,
            decision_number=clean_str(data.get("decision_number")),
            decision_date=parse_date(data.get("decision_date"), "decision_date"),
            note=clean_str(data.get("note")),
            actor_id=actor.id,
            replace_existing=replace_existing,
            audit_meta=meta,
        )

        record_audit(
            user_id=actor.id,
            action="employee.create",
            entity_type="employee",
            entity_id=emp.id,
            unit_id=unit_id,
            new_values=emp.to_dict(include_sensitive=True),
            **meta,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return emp.to_dict(include_sensitive=_can_view_sensitive(actor))


def update_employee(employee_id: int, data: dict, *, actor, scope, meta: dict) -> dict:
    emp = repo.get_by_id(employee_id)
    if emp is None:
        raise NotFoundError("Không tìm thấy nhân sự.")
    current = emp.primary_active_assignment()
    _assert_scope(actor, scope, current.unit_id if current else None, action="sửa")

    payload = _validate_profile(data, partial=True)
    old = emp.to_dict(include_sensitive=True)

    if "employee_code" in payload and payload["employee_code"] != emp.employee_code:
        if repo.get_by_code(payload["employee_code"]):
            raise ConflictError("Mã nhân sự đã tồn tại.")
        emp.employee_code = payload["employee_code"]

    for f in _PROFILE_FIELDS:
        if f in payload:
            setattr(emp, f, payload[f])

    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="employee.update",
        entity_type="employee",
        entity_id=emp.id,
        unit_id=current.unit_id if current else None,
        old_values=old,
        new_values=emp.to_dict(include_sensitive=True),
        **meta,
    )
    db.session.commit()
    return emp.to_dict(include_sensitive=_can_view_sensitive(actor))


def soft_delete_employee(employee_id: int, *, actor, scope, meta: dict) -> dict:
    emp = repo.get_by_id(employee_id)
    if emp is None:
        raise NotFoundError("Không tìm thấy nhân sự.")
    current = emp.primary_active_assignment()
    _assert_scope(actor, scope, current.unit_id if current else None, action="xóa")

    old = emp.to_dict(include_sensitive=True)
    emp.is_deleted = True
    emp.deleted_at = utcnow()
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="employee.delete",
        entity_type="employee",
        entity_id=emp.id,
        unit_id=current.unit_id if current else None,
        old_values=old,
        new_values={"is_deleted": True, "deleted_at": emp.deleted_at.isoformat()},
        **meta,
    )
    db.session.commit()
    return {"id": emp.id, "is_deleted": True}


def restore_employee(employee_id: int, *, actor, scope, meta: dict) -> dict:
    emp = repo.get_by_id(employee_id, include_deleted=True)
    if emp is None:
        raise NotFoundError("Không tìm thấy nhân sự.")
    if not emp.is_deleted:
        raise ConflictError("Nhân sự này chưa bị xóa.")
    current = emp.primary_active_assignment()
    _assert_scope(actor, scope, current.unit_id if current else None, action="khôi phục")

    emp.is_deleted = False
    emp.deleted_at = None
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="employee.restore",
        entity_type="employee",
        entity_id=emp.id,
        unit_id=current.unit_id if current else None,
        new_values={"is_deleted": False},
        **meta,
    )
    db.session.commit()
    return emp.to_dict(include_sensitive=_can_view_sensitive(actor))


# --------------------------- Chuyển đơn vị ---------------------------
def transfer_employee(employee_id: int, data: dict, *, actor, scope, meta: dict) -> dict:
    """Chuyển nhân sự sang đơn vị/chức vụ mới.

    Toàn bộ nằm trong một transaction: lỗi ở bất kỳ bước nào -> rollback.
    """
    emp = repo.get_by_id(employee_id)
    if emp is None:
        raise NotFoundError("Không tìm thấy nhân sự.")

    # 1. Nhân sự phải có phân công chính hợp lệ
    current = emp.primary_active_assignment()
    if current is None:
        raise BusinessRuleError(
            "Nhân sự chưa có phân công chính đang hiệu lực, không thể chuyển đơn vị."
        )

    to_unit_id = _to_int(data.get("to_unit_id"))
    to_position_id = _to_int(data.get("to_position_id"))
    if not to_unit_id or not to_position_id:
        raise ValidationError("Vui lòng chọn đơn vị mới và chức vụ mới.")

    to_unit = db.session.get(OrganizationUnit, to_unit_id)
    to_position = db.session.get(Position, to_position_id)
    if to_unit is None or not to_unit.is_active:
        raise BusinessRuleError("Không thể chuyển vào đơn vị đã ngừng hoạt động.")
    if to_position is None or not to_position.is_active:
        raise BusinessRuleError("Không thể chuyển vào chức vụ đã ngừng hoạt động.")

    # 2. Quyền trên cả đơn vị nguồn lẫn đơn vị đích
    _assert_scope(actor, scope, current.unit_id, action="chuyển (đơn vị nguồn)")
    _assert_scope(actor, scope, to_unit_id, action="chuyển (đơn vị đích)")

    if to_unit_id == current.unit_id and to_position_id == current.position_id:
        raise ConflictError("Đơn vị và chức vụ mới trùng với hiện tại.")

    # 3. Ngày hiệu lực
    effective_date = parse_date(data.get("effective_date"), "effective_date")
    if effective_date is None:
        raise ValidationError("Ngày hiệu lực là bắt buộc.")
    if effective_date < current.start_date:
        raise ValidationError(
            "Ngày hiệu lực không được trước ngày bắt đầu phân công hiện tại "
            f"({current.start_date.isoformat()})."
        )

    replace_existing = _as_bool(data.get("replace_existing"))
    assignment_type = clean_str(data.get("assignment_type")) or "TRANSFER"
    if assignment_type not in ASSIGNMENT_TYPES:
        assignment_type = "TRANSFER"

    before_snapshot = {
        "assignment_id": current.id,
        "unit_id": current.unit_id,
        "position_id": current.position_id,
        "start_date": current.start_date.isoformat(),
    }

    try:
        # 9a. Audit "trước thay đổi"
        record_audit(
            user_id=actor.id,
            action="employee.transfer.before",
            entity_type="employee",
            entity_id=emp.id,
            unit_id=current.unit_id,
            old_values=before_snapshot,
            new_values={
                "to_unit_id": to_unit_id,
                "to_position_id": to_position_id,
                "effective_date": effective_date.isoformat(),
            },
            **meta,
        )

        # 4-5. Kiểm tra giới hạn chức vụ tại đơn vị mới (có khóa bản ghi)
        result = assign_primary(
            employee=emp,
            unit_id=to_unit_id,
            position_id=to_position_id,
            assignment_type=assignment_type,
            start_date=effective_date,
            decision_number=clean_str(data.get("decision_number")),
            decision_date=parse_date(data.get("decision_date"), "decision_date"),
            note=clean_str(data.get("note")),
            actor_id=actor.id,
            replace_existing=replace_existing,
            audit_meta=meta,
        )
        new_assignment: EmployeeAssignment = result["assignment"]

        # 6. Kết thúc phân công cũ trước ngày hiệu lực (không xóa lịch sử)
        end_assignment(current, effective_date - timedelta(days=1))

        # Đồng bộ trạng thái hồ sơ
        if emp.status in ("WORKING", "TRANSFERRED"):
            emp.status = "WORKING"

        db.session.flush()

        # 9b. Audit "sau thay đổi"
        record_audit(
            user_id=actor.id,
            action="employee.transfer.after",
            entity_type="employee",
            entity_id=emp.id,
            unit_id=to_unit_id,
            old_values=before_snapshot,
            new_values={
                "assignment_id": new_assignment.id,
                "unit_id": to_unit_id,
                "position_id": to_position_id,
                "start_date": effective_date.isoformat(),
                "previous_assignment_ended_on": current.end_date.isoformat(),
            },
            **meta,
        )
        db.session.commit()
    except Exception:
        # 10. Rollback toàn bộ nếu bất kỳ bước nào lỗi
        db.session.rollback()
        raise

    db.session.refresh(emp)
    data_out = emp.to_dict(include_sensitive=_can_view_sensitive(actor))
    data_out["assignments"] = [a.to_dict() for a in emp.assignments]
    return data_out


def dashboard(*, actor, scope) -> dict:
    counts = repo.dashboard_counts(scope)
    unit_names = {
        u.id: u.name
        for u in db.session.query(OrganizationUnit).all()
    }
    recent = (
        db.session.query(EmployeeAssignment)
        .filter(EmployeeAssignment.assignment_type == "TRANSFER")
        .order_by(EmployeeAssignment.created_at.desc())
        .limit(10)
        .all()
    )
    recent_out = []
    for a in recent:
        if not scope.is_global and a.unit_id not in scope.unit_ids:
            continue
        recent_out.append(a.to_dict())
    return {
        "total_working": counts["total_working"],
        "by_status": counts["by_status"],
        "by_unit": [
            {"unit_id": uid, "unit_name": unit_names.get(uid, "Không rõ"), "count": c}
            for uid, c in counts["by_unit"].items()
        ],
        "recent_transfers": recent_out,
    }


# ----------------------------- Helpers -----------------------------
def _to_int(value):
    try:
        return int(value) if value not in (None, "", "null") else None
    except (TypeError, ValueError):
        return None


def _as_bool(value) -> bool:
    return str(value).lower() in ("1", "true", "yes", "on")
