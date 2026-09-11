"""Snapshot đơn vị/chức vụ hiện tại của một tài khoản — dùng chung cho Giao
việc và KPI khi tạo bản ghi mới (KHÔNG dùng để suy ra "hiện tại" sau này —
mỗi bản ghi giữ nguyên snapshot tại đúng thời điểm nó được tạo)."""
from __future__ import annotations

from ..models import User


def current_position_snapshot(user: User | None) -> dict:
    if user is None or user.employee_id is None or user.employee is None:
        return {"unit_id": None, "position_id": None, "position_name": None, "is_managerial": False}
    assignment = user.employee.primary_active_assignment()
    if assignment is None:
        return {"unit_id": None, "position_id": None, "position_name": None, "is_managerial": False}
    return {
        "unit_id": assignment.unit_id,
        "position_id": assignment.position_id,
        "position_name": assignment.position.name if assignment.position else None,
        "is_managerial": bool(assignment.position.is_managerial) if assignment.position else False,
    }
