"""Test các luồng quản lý tài khoản, vai trò và phạm vi đơn vị."""
from __future__ import annotations

from app.models import Role


def test_create_user_assign_role_scope_and_reset_password(
    client, db, admin_user, auth_header, make_unit
):
    headers = auth_header("admin_test")
    unit = make_unit("USER-SCOPE", unit_type="DEPARTMENT")
    viewer = db.session.query(Role).filter(Role.code == "VIEWER").one()

    created = client.post(
        "/api/users",
        headers=headers,
        json={
            "username": "managed_user",
            "password": "Password@123",
            "full_name": "Tài khoản được quản lý",
            "email": "managed@example.com",
            "role_ids": [viewer.id],
        },
    )
    assert created.status_code == 201, created.get_json()
    user = created.get_json()["data"]
    assert [role["code"] for role in user["roles"]] == ["VIEWER"]

    scoped = client.post(
        f"/api/users/{user['id']}/unit-scopes",
        headers=headers,
        json={"scopes": [{"scope_type": "SUBTREE", "unit_id": unit.id}]},
    )
    assert scoped.status_code == 200
    assert scoped.get_json()["data"]["unit_scopes"][0]["unit_id"] == unit.id

    reset = client.post(
        f"/api/users/{user['id']}/reset-password", headers=headers, json={}
    )
    assert reset.status_code == 200
    generated_password = reset.get_json()["data"]["new_password"]
    assert generated_password and len(generated_password) >= 8
    assert client.post(
        "/api/auth/login",
        json={"username": "managed_user", "password": generated_password},
    ).status_code == 200


def test_custom_role_crud(client, admin_user, auth_header):
    headers = auth_header("admin_test")
    created = client.post(
        "/api/roles",
        headers=headers,
        json={
            "code": "CUSTOM_TEST_ROLE",
            "name": "Vai trò kiểm thử",
            "permissions": ["employee.view"],
        },
    )
    assert created.status_code == 201, created.get_json()
    role = created.get_json()["data"]

    updated = client.put(
        f"/api/roles/{role['id']}",
        headers=headers,
        json={
            "name": "Vai trò đã cập nhật",
            "permissions": ["employee.view", "unit.view"],
        },
    )
    assert updated.status_code == 200
    assert updated.get_json()["data"]["permissions"] == ["employee.view", "unit.view"]

    deleted = client.delete(f"/api/roles/{role['id']}", headers=headers)
    assert deleted.status_code == 200
