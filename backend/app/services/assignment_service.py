"""Nghiệp vụ phân công công tác dùng chung cho: tuyển dụng, bổ nhiệm, chuyển đơn vị.

Trọng tâm:
- Phát hiện xung đột giới hạn chức vụ tại đơn vị.
- Thay thế người đang giữ chức vụ trong một transaction, có khóa bản ghi.
- Không làm mất lịch sử phân công cũ.
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import and_

from ..common.exceptions import BusinessRuleError, ConflictError
from ..extensions import db
from ..models import EmployeeAssignment, Position, UnitPositionLimit
from .audit_service import record_audit


def _active_holders_query(unit_id: int, position_id: int, *, exclude_employee_id: int | None = None):
    q = db.session.query(EmployeeAssignment).filter(
        EmployeeAssignment.unit_id == unit_id,
        EmployeeAssignment.position_id == position_id,
        EmployeeAssignment.is_primary.is_(True),
        EmployeeAssignment.end_date.is_(None),
    )
    if exclude_employee_id is not None:
        q = q.filter(EmployeeAssignment.employee_id != exclude_employee_id)
    return q


def check_position_capacity(
    unit_id: int,
    position_id: int,
    *,
    exclude_employee_id: int | None = None,
    lock: bool = False,
) -> dict:
    """Kiểm tra sức chứa của chức vụ tại đơn vị.

    Trả về dict:
      - limit: số tối đa (None = không giới hạn)
      - current_count: số người đang giữ (không tính exclude_employee_id)
      - is_full: đã đạt giới hạn hay chưa
      - holders: danh sách phân công đang giữ (để hiển thị xác nhận thay thế)

    Khi lock=True, dùng SELECT ... FOR UPDATE trên các bản ghi liên quan để
    tránh hai người được gán đồng thời vào chức vụ chỉ cho phép một người.
    """
    limit_row: UnitPositionLimit | None = (
        db.session.query(UnitPositionLimit)
        .filter(
            UnitPositionLimit.unit_id == unit_id,
            UnitPositionLimit.position_id == position_id,
        )
        .first()
    )
    max_holders = limit_row.max_holders if limit_row else None

    holders_q = _active_holders_query(
        unit_id, position_id, exclude_employee_id=exclude_employee_id
    )
    if lock:
        # with_for_update: MySQL/PostgreSQL sẽ khóa dòng; SQLite bỏ qua (test).
        holders_q = holders_q.with_for_update()
        if limit_row is not None:
            db.session.query(UnitPositionLimit).filter(
                UnitPositionLimit.id == limit_row.id
            ).with_for_update().all()

    holders = holders_q.all()
    current_count = len(holders)
    is_full = max_holders is not None and current_count >= max_holders
    return {
        "limit": max_holders,
        "current_count": current_count,
        "is_full": is_full,
        "holders": holders,
    }


def _conflict_payload(position: Position | None, unit_id: int, holders) -> dict:
    return {
        "conflict": "POSITION_LIMIT_REACHED",
        "unit_id": unit_id,
        "position": position.to_dict() if position else None,
        "current_holders": [
            {
                "assignment_id": h.id,
                "employee_id": h.employee_id,
                "employee_code": h.employee.employee_code if h.employee else None,
                "full_name": h.employee.full_name if h.employee else None,
                "start_date": h.start_date.isoformat() if h.start_date else None,
            }
            for h in holders
        ],
    }


def end_assignment(assignment: EmployeeAssignment, end_date: date) -> None:
    """Kết thúc một phân công. end_date là ngày cuối cùng còn hiệu lực."""
    if assignment.end_date is not None:
        return
    if end_date < assignment.start_date:
        # Không cho end_date trước start_date -> đặt bằng start_date
        end_date = assignment.start_date
    assignment.end_date = end_date


def assign_primary(
    *,
    employee,
    unit_id: int,
    position_id: int,
    assignment_type: str,
    start_date: date,
    decision_number: str | None,
    decision_date: date | None,
    note: str | None,
    actor_id: int | None,
    replace_existing: bool = False,
    audit_meta: dict | None = None,
) -> dict:
    """Tạo phân công chính mới cho nhân sự.

    - Nếu chức vụ đã đủ chỗ và replace_existing=False -> ném ConflictError kèm
      payload để frontend hiển thị hộp xác nhận.
    - Nếu replace_existing=True -> kết thúc nhiệm kỳ người cũ (trước ngày hiệu lực)
      rồi tạo phân công mới. Toàn bộ nằm trong transaction do caller kiểm soát.
    - Ghi audit người cũ, người mới, đơn vị, chức vụ, thời điểm.

    Hàm KHÔNG tự commit; caller bao transaction.
    """
    audit_meta = audit_meta or {}
    position = db.session.get(Position, position_id)

    capacity = check_position_capacity(
        unit_id, position_id, exclude_employee_id=employee.id, lock=True
    )

    if capacity["is_full"]:
        if not replace_existing:
            raise ConflictError(
                "Chức vụ tại đơn vị đã đạt số lượng tối đa. "
                "Xác nhận thay thế người đang giữ chức vụ để tiếp tục.",
                payload=_conflict_payload(position, unit_id, capacity["holders"]),
            )
        # --- Thực hiện thay thế ---
        replaced = []
        end_prev = start_date - timedelta(days=1)
        for holder in capacity["holders"]:
            end_assignment(holder, end_prev)
            replaced.append(
                {
                    "assignment_id": holder.id,
                    "employee_id": holder.employee_id,
                    "employee_code": holder.employee.employee_code
                    if holder.employee
                    else None,
                    "ended_on": holder.end_date.isoformat() if holder.end_date else None,
                }
            )
        db.session.flush()
        record_audit(
            user_id=actor_id,
            action="position.replace_holder",
            entity_type="position",
            entity_id=position_id,
            unit_id=unit_id,
            old_values={"replaced_holders": replaced},
            new_values={
                "new_employee_id": employee.id,
                "new_employee_code": employee.employee_code,
                "unit_id": unit_id,
                "position_id": position_id,
                "effective_date": start_date.isoformat(),
            },
            **audit_meta,
        )

    new_assignment = EmployeeAssignment(
        employee_id=employee.id,
        unit_id=unit_id,
        position_id=position_id,
        assignment_type=assignment_type,
        start_date=start_date,
        end_date=None,
        is_primary=True,
        decision_number=decision_number,
        decision_date=decision_date,
        note=note,
        created_by=actor_id,
    )
    db.session.add(new_assignment)
    db.session.flush()
    return {"assignment": new_assignment}


def assert_no_primary_overlap(employee_id: int, start_date: date, *, ignore_id: int | None = None) -> None:
    """Không cho phép các khoảng công tác chính bị chồng lấn.

    Một phân công cũ chồng lấn nếu end_date NULL hoặc end_date >= start_date mới.
    """
    q = db.session.query(EmployeeAssignment).filter(
        EmployeeAssignment.employee_id == employee_id,
        EmployeeAssignment.is_primary.is_(True),
        and_(
            (EmployeeAssignment.end_date.is_(None))
            | (EmployeeAssignment.end_date >= start_date)
        ),
    )
    if ignore_id is not None:
        q = q.filter(EmployeeAssignment.id != ignore_id)
    if q.first() is not None:
        raise BusinessRuleError(
            "Đã tồn tại phân công chính chồng lấn khoảng thời gian. "
            "Cần kết thúc phân công hiện tại trước ngày hiệu lực."
        )
