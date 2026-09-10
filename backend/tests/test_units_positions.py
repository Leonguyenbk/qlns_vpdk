"""Test cơ cấu đơn vị và chức vụ."""
from __future__ import annotations

from datetime import date


def test_unit_cycle_is_rejected(client, admin_user, auth_header, make_unit):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    a = make_unit("A", parent=root)
    b = make_unit("B", parent=a)
    headers = auth_header("admin_test")

    # Đặt ROOT làm con của B -> tạo vòng lặp
    resp = client.put(f"/api/units/{root.id}", headers=headers, json={"parent_id": b.id})
    assert resp.status_code == 400
    assert "vòng lặp" in resp.get_json()["message"].lower()


def test_unit_self_parent_rejected(client, admin_user, auth_header, make_unit):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    headers = auth_header("admin_test")
    resp = client.put(f"/api/units/{root.id}", headers=headers, json={"parent_id": root.id})
    assert resp.status_code == 400


def test_unit_duplicate_code_conflict(client, admin_user, auth_header, make_unit):
    make_unit("DUP", unit_type="HEAD_OFFICE")
    headers = auth_header("admin_test")
    resp = client.post("/api/units", headers=headers, json={"code": "DUP", "name": "X", "unit_type": "BRANCH"})
    assert resp.status_code == 409


def test_delete_unit_with_data_only_deactivates(
    client, admin_user, auth_header, make_unit, make_position, make_employee
):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    a = make_unit("A", parent=root)
    pos = make_position("CV")
    make_employee("U1", a, pos)
    headers = auth_header("admin_test")

    resp = client.delete(f"/api/units/{a.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["hard_deleted"] is False

    # Đơn vị vẫn tồn tại nhưng is_active = False
    detail = client.get(f"/api/units/{a.id}", headers=headers).get_json()["data"]
    assert detail["is_active"] is False


def test_delete_empty_unit_hard_deletes(client, admin_user, auth_header, make_unit):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    tmp = make_unit("TMP", parent=root)
    headers = auth_header("admin_test")
    resp = client.delete(f"/api/units/{tmp.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["hard_deleted"] is True
    assert client.get(f"/api/units/{tmp.id}", headers=headers).status_code == 404


def test_unit_tree_structure(client, admin_user, auth_header, make_unit):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    a = make_unit("A", parent=root)
    make_unit("A1", parent=a)
    headers = auth_header("admin_test")

    tree = client.get("/api/units/tree", headers=headers).get_json()["data"]
    assert len(tree) == 1
    assert tree[0]["code"] == "ROOT"
    assert tree[0]["children"][0]["code"] == "A"
    assert tree[0]["children"][0]["children"][0]["code"] == "A1"


def test_position_limit_config(client, admin_user, auth_header, make_unit, make_position):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    pos = make_position("TP", managerial=True)
    headers = auth_header("admin_test")

    resp = client.post(
        f"/api/units/{root.id}/position-limits",
        headers=headers,
        json={"position_id": pos.id, "max_holders": 1},
    )
    assert resp.status_code == 201
    limit_id = resp.get_json()["data"]["id"]

    resp2 = client.put(
        f"/api/units/{root.id}/position-limits/{limit_id}",
        headers=headers,
        json={"max_holders": 3},
    )
    assert resp2.status_code == 200
    assert resp2.get_json()["data"]["max_holders"] == 3


def test_position_limit_cannot_be_lower_than_active_holders(
    client, admin_user, auth_header, make_unit, make_position, make_employee
):
    root = make_unit("ROOT", unit_type="HEAD_OFFICE")
    pos = make_position("CV")
    make_employee("HOLDER1", root, pos)
    make_employee("HOLDER2", root, pos)
    headers = auth_header("admin_test")

    resp = client.post(
        f"/api/units/{root.id}/position-limits",
        headers=headers,
        json={"position_id": pos.id, "max_holders": 1},
    )

    assert resp.status_code == 409
    data = resp.get_json()["data"]
    assert data["conflict"] == "POSITION_LIMIT_BELOW_ACTIVE_HOLDERS"
    assert data["active_holders"] == 2
