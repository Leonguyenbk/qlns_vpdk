"""Test nhật ký thao tác tuân thủ phạm vi đơn vị."""
from __future__ import annotations

from app.models import AuditLog
from app.permissions.constants import ROLE_SYSTEM_ADMIN


def test_audit_logs_are_filtered_by_unit_scope(
    client, db, make_user, auth_header, make_unit
):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    unit_a = make_unit("A", parent=root)
    unit_b = make_unit("B", parent=root)
    make_user(
        "scoped_auditor",
        role_code=ROLE_SYSTEM_ADMIN,
        scopes=(("UNIT", unit_a),),
    )
    db.session.add_all(
        [
            AuditLog(action="employee.update", entity_type="employee", entity_id="1", unit_id=unit_a.id),
            AuditLog(action="employee.update", entity_type="employee", entity_id="2", unit_id=unit_b.id),
            AuditLog(action="role.update", entity_type="role", entity_id="1", unit_id=None),
        ]
    )
    db.session.commit()

    resp = client.get("/api/audit-logs", headers=auth_header("scoped_auditor"))

    assert resp.status_code == 200
    items = resp.get_json()["data"]["items"]
    assert [item["entity_id"] for item in items] == ["1"]
