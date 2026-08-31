"""Test chuyển đơn vị và giới hạn chức vụ."""
from __future__ import annotations

from datetime import date

from app.extensions import db
from app.models import EmployeeAssignment
from app.services import employee_service


def _transfer_body(to_unit, to_pos, **over):
    body = {
        "to_unit_id": to_unit.id,
        "to_position_id": to_pos.id,
        "effective_date": "2023-01-01",
        "decision_number": "QD-01",
        "decision_date": "2022-12-20",
    }
    body.update(over)
    return body


def test_transfer_success_keeps_history(
    client, admin_user, auth_header, make_unit, make_position, make_employee
):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    a = make_unit("A", parent=root)
    b = make_unit("B", parent=root)
    pos = make_position("CV")
    emp = make_employee("T1", a, pos, start=date(2020, 1, 1))
    headers = auth_header("admin_test")

    resp = client.post(f"/api/employees/{emp.id}/transfer", headers=headers, json=_transfer_body(b, pos))
    assert resp.status_code == 200, resp.get_json()

    rows = (
        db.session.query(EmployeeAssignment)
        .filter(EmployeeAssignment.employee_id == emp.id)
        .order_by(EmployeeAssignment.start_date)
        .all()
    )
    assert len(rows) == 2  # lịch sử cũ được giữ lại
    old, new = rows
    assert old.unit_id == a.id and old.end_date == date(2022, 12, 31)
    assert new.unit_id == b.id and new.end_date is None and new.is_primary


def test_cannot_transfer_into_inactive_unit(
    client, admin_user, auth_header, make_unit, make_position, make_employee
):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    a = make_unit("A", parent=root)
    dead = make_unit("DEAD", parent=root, is_active=False)
    pos = make_position("CV")
    emp = make_employee("T2", a, pos)
    headers = auth_header("admin_test")

    resp = client.post(f"/api/employees/{emp.id}/transfer", headers=headers, json=_transfer_body(dead, pos))
    assert resp.status_code == 400
    assert "ngừng hoạt động" in resp.get_json()["message"].lower()


def test_position_limit_conflict_then_replace(
    client, admin_user, auth_header, make_unit, make_position, make_employee, set_limit
):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    a = make_unit("A", parent=root)
    b = make_unit("B", parent=root)
    boss = make_position("GDCN", managerial=True)
    staff = make_position("CV")

    set_limit(b, boss, 1)  # chỉ 1 giám đốc / chi nhánh B
    incumbent = make_employee("BOSS_OLD", b, boss, start=date(2019, 1, 1))
    mover = make_employee("MOVER", a, staff, start=date(2020, 1, 1))
    headers = auth_header("admin_test")

    # Lần 1: phát hiện xung đột -> 409 kèm thông tin người đang giữ
    resp = client.post(
        f"/api/employees/{mover.id}/transfer",
        headers=headers,
        json=_transfer_body(b, boss),
    )
    assert resp.status_code == 409
    payload = resp.get_json()["data"]
    assert payload["conflict"] == "POSITION_LIMIT_REACHED"
    assert payload["current_holders"][0]["employee_id"] == incumbent.id

    # Lần 2: xác nhận thay thế
    resp2 = client.post(
        f"/api/employees/{mover.id}/transfer",
        headers=headers,
        json=_transfer_body(b, boss, replace_existing=True),
    )
    assert resp2.status_code == 200

    # Người cũ đã kết thúc nhiệm kỳ, người mới đang giữ
    old_rows = (
        db.session.query(EmployeeAssignment)
        .filter(EmployeeAssignment.employee_id == incumbent.id)
        .all()
    )
    assert old_rows[0].end_date is not None
    new_rows = (
        db.session.query(EmployeeAssignment)
        .filter(
            EmployeeAssignment.employee_id == mover.id,
            EmployeeAssignment.end_date.is_(None),
        )
        .all()
    )
    assert len(new_rows) == 1 and new_rows[0].unit_id == b.id


def test_only_one_holder_for_single_capacity_position(
    app, make_unit, make_position, make_employee, set_limit
):
    """Không cho hai người đồng thời giữ chức vụ giới hạn 1 người."""
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    b = make_unit("B", parent=root)
    a = make_unit("A", parent=root)
    boss = make_position("GDCN", managerial=True)
    staff = make_position("CV")
    set_limit(b, boss, 1)

    make_employee("HOLD1", b, boss, start=date(2019, 1, 1))
    mover = make_employee("HOLD2", a, staff, start=date(2020, 1, 1))

    class _Actor:
        id = None

        def has_permission(self, _):
            return True

    from app.permissions.scope import UnitScopeResolver

    scope = UnitScopeResolver(is_global=True, unit_ids=set())
    import pytest
    from app.common.exceptions import ConflictError

    with pytest.raises(ConflictError):
        employee_service.transfer_employee(
            mover.id,
            {
                "to_unit_id": b.id,
                "to_position_id": boss.id,
                "effective_date": "2023-01-01",
            },
            actor=_Actor(),
            scope=scope,
            meta={"ip_address": None, "user_agent": None},
        )
    db.session.rollback()

    # Vẫn chỉ có đúng 1 người đang giữ chức vụ
    active = (
        db.session.query(EmployeeAssignment)
        .filter(
            EmployeeAssignment.unit_id == b.id,
            EmployeeAssignment.position_id == boss.id,
            EmployeeAssignment.end_date.is_(None),
        )
        .count()
    )
    assert active == 1


def test_transfer_rollback_on_error(
    client, admin_user, auth_header, make_unit, make_position, make_employee, monkeypatch
):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    a = make_unit("A", parent=root)
    b = make_unit("B", parent=root)
    pos = make_position("CV")
    emp = make_employee("RB1", a, pos, start=date(2020, 1, 1))
    headers = auth_header("admin_test")

    # Ép lỗi ở bước ghi audit "sau thay đổi"
    import app.services.employee_service as es

    real_audit = es.record_audit
    calls = {"n": 0}

    def boom(*args, **kwargs):
        calls["n"] += 1
        if kwargs.get("action") == "employee.transfer.after":
            raise RuntimeError("Lỗi giả lập")
        return real_audit(*args, **kwargs)

    monkeypatch.setattr(es, "record_audit", boom)

    resp = client.post(f"/api/employees/{emp.id}/transfer", headers=headers, json=_transfer_body(b, pos))
    assert resp.status_code == 500

    # Rollback: vẫn chỉ có 1 phân công ở đơn vị A, chưa tạo phân công mới
    rows = (
        db.session.query(EmployeeAssignment)
        .filter(EmployeeAssignment.employee_id == emp.id)
        .all()
    )
    assert len(rows) == 1
    assert rows[0].unit_id == a.id and rows[0].end_date is None
