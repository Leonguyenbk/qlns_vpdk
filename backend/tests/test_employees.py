"""Test CRUD nhân sự, soft delete và khôi phục."""
from __future__ import annotations


def _payload(unit, pos, **over):
    base = {
        "employee_code": "NV100",
        "full_name": "Nguyễn Test",
        "unit_id": unit.id,
        "position_id": pos.id,
        "recruitment_date": "2021-01-01",
        "email": "nvtest@example.com",
        "phone": "0912345678",
    }
    base.update(over)
    return base


def test_create_employee(client, admin_user, auth_header, make_unit, make_position):
    unit = make_unit("ROOT", unit_type="HEAD_OFFICE")
    pos = make_position("CV")
    headers = auth_header("admin_test")

    resp = client.post("/api/employees", headers=headers, json=_payload(unit, pos))
    assert resp.status_code == 201, resp.get_json()
    data = resp.get_json()["data"]
    assert data["employee_code"] == "NV100"
    assert data["current_unit"]["id"] == unit.id
    assert data["current_position"]["id"] == pos.id


def test_create_duplicate_code_conflict(client, admin_user, auth_header, make_unit, make_position):
    unit = make_unit("ROOT", unit_type="HEAD_OFFICE")
    pos = make_position("CV")
    headers = auth_header("admin_test")
    client.post("/api/employees", headers=headers, json=_payload(unit, pos))
    resp = client.post("/api/employees", headers=headers, json=_payload(unit, pos))
    assert resp.status_code == 409


def test_create_invalid_email_422(client, admin_user, auth_header, make_unit, make_position):
    unit = make_unit("ROOT", unit_type="HEAD_OFFICE")
    pos = make_position("CV")
    headers = auth_header("admin_test")
    resp = client.post("/api/employees", headers=headers, json=_payload(unit, pos, email="khong-hop-le"))
    assert resp.status_code == 422


def test_update_employee(client, admin_user, auth_header, make_unit, make_position, make_employee):
    unit = make_unit("ROOT", unit_type="HEAD_OFFICE")
    pos = make_position("CV")
    emp = make_employee("NV200", unit, pos)
    headers = auth_header("admin_test")

    resp = client.put(f"/api/employees/{emp.id}", headers=headers, json={"full_name": "Tên Mới", "phone": "0987654321"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["full_name"] == "Tên Mới"


def test_soft_delete_and_restore(client, admin_user, auth_header, make_unit, make_position, make_employee):
    unit = make_unit("ROOT", unit_type="HEAD_OFFICE")
    pos = make_position("CV")
    emp = make_employee("NV300", unit, pos)
    headers = auth_header("admin_test")

    # Xóa mềm
    resp = client.delete(f"/api/employees/{emp.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["is_deleted"] is True

    # Không còn trong danh sách mặc định
    listed = client.get("/api/employees", headers=headers).get_json()["data"]["items"]
    assert all(i["id"] != emp.id for i in listed)

    # Vẫn xem được khi include_deleted, và bản ghi còn nguyên (không xóa cứng)
    detail = client.get(f"/api/employees/{emp.id}?include_deleted=true", headers=headers)
    assert detail.status_code == 200

    # Khôi phục
    restored = client.post(f"/api/employees/{emp.id}/restore", headers=headers)
    assert restored.status_code == 200
    assert restored.get_json()["data"]["is_deleted"] is False


def test_list_pagination_and_search(client, admin_user, auth_header, make_unit, make_position, make_employee):
    unit = make_unit("ROOT", unit_type="HEAD_OFFICE")
    pos = make_position("CV")
    for i in range(5):
        make_employee(f"SEARCH{i}", unit, pos, full_name=f"Người {i}")
    headers = auth_header("admin_test")

    resp = client.get("/api/employees?page=1&page_size=2", headers=headers)
    body = resp.get_json()["data"]
    assert body["pagination"]["page_size"] == 2
    assert body["pagination"]["total"] >= 5
    assert len(body["items"]) == 2

    resp2 = client.get("/api/employees?keyword=SEARCH3", headers=headers)
    items = resp2.get_json()["data"]["items"]
    assert len(items) == 1 and items[0]["employee_code"] == "SEARCH3"
