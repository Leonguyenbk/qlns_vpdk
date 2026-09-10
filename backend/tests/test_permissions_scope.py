"""Test phân quyền và lọc theo phạm vi đơn vị."""
from __future__ import annotations

from app.permissions.constants import ROLE_UNIT_MANAGER, ROLE_VIEWER


def test_missing_permission_is_forbidden(client, make_user, auth_header, make_unit, make_position):
    make_user("viewer1", role_code=ROLE_VIEWER)
    headers = auth_header("viewer1")
    # Người xem không có employee.create
    resp = client.post("/api/employees", headers=headers, json={"employee_code": "X", "full_name": "Y"})
    assert resp.status_code == 403
    assert resp.get_json()["success"] is False


def test_employee_list_filtered_by_unit_scope(
    client, make_user, auth_header, make_unit, make_position, make_employee
):
    parent = make_unit("ROOT", unit_type="HEAD_OFFICE")
    cn01 = make_unit("CN01", parent=parent)
    cn02 = make_unit("CN02", parent=parent)
    pos = make_position("CV")

    make_employee("E-CN01", cn01, pos)
    make_employee("E-CN02", cn02, pos)

    # Quản lý đơn vị chỉ có phạm vi CN01 (SUBTREE)
    make_user("mgr01", role_code=ROLE_UNIT_MANAGER, scopes=(("SUBTREE", cn01),))
    headers = auth_header("mgr01")

    resp = client.get("/api/employees", headers=headers)
    assert resp.status_code == 200
    items = resp.get_json()["data"]["items"]
    codes = {i["employee_code"] for i in items}
    assert codes == {"E-CN01"}


def test_out_of_scope_detail_is_forbidden(
    client, make_user, auth_header, make_unit, make_position, make_employee
):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    cn01 = make_unit("CN01", parent=root)
    cn02 = make_unit("CN02", parent=root)
    pos = make_position("CV")
    emp2 = make_employee("E2", cn02, pos)

    make_user("mgr_only01", role_code=ROLE_UNIT_MANAGER, scopes=(("UNIT", cn01),))
    headers = auth_header("mgr_only01")

    resp = client.get(f"/api/employees/{emp2.id}", headers=headers)
    assert resp.status_code == 403


def test_sensitive_field_hidden_without_permission(
    client, make_user, auth_header, make_unit, make_position, db
):
    from app.models import Employee, EmployeeAssignment
    from datetime import date

    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    pos = make_position("CV")
    emp = Employee(employee_code="SEC1", full_name="Nhân sự Nhạy cảm", identity_number="079123456789", status="WORKING")
    db.session.add(emp)
    db.session.flush()
    db.session.add(EmployeeAssignment(employee_id=emp.id, unit_id=root.id, position_id=pos.id, assignment_type="RECRUITMENT", start_date=date(2020, 1, 1), is_primary=True))
    db.session.commit()

    make_user("viewer_sec", role_code=ROLE_VIEWER)
    headers = auth_header("viewer_sec")
    resp = client.get(f"/api/employees/{emp.id}", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["identity_number"] is None
    assert data["has_sensitive_data"] is True
