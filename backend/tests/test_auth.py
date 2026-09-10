"""Test đăng nhập / xác thực."""
from __future__ import annotations


def test_login_success(client, make_user):
    make_user("u_login")
    resp = client.post("/api/auth/login", json={"username": "u_login", "password": "Password@123"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]
    assert "password" not in str(body["data"]["user"]).lower() or "password_hash" not in body["data"]["user"]


def test_login_wrong_password(client, make_user):
    make_user("u_wrong")
    resp = client.post("/api/auth/login", json={"username": "u_wrong", "password": "sai-mat-khau"})
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


def test_login_locked_after_max_failed_attempts(client, make_user):
    make_user("u_lock")
    for _ in range(3):  # LOGIN_MAX_FAILED_ATTEMPTS = 3 ở TestingConfig
        client.post("/api/auth/login", json={"username": "u_lock", "password": "x"})
    # Lần sau dù đúng mật khẩu vẫn bị khóa tạm
    resp = client.post("/api/auth/login", json={"username": "u_lock", "password": "Password@123"})
    assert resp.status_code == 401
    assert "khóa" in resp.get_json()["message"].lower()


def test_inactive_user_cannot_login(client, make_user):
    make_user("u_inactive", is_active=False)
    resp = client.post("/api/auth/login", json={"username": "u_inactive", "password": "Password@123"})
    assert resp.status_code == 401


def test_api_rejected_without_token(client):
    resp = client.get("/api/employees")
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


def test_me_and_refresh_and_logout(client, make_user):
    make_user("u_flow")
    login = client.post("/api/auth/login", json={"username": "u_flow", "password": "Password@123"}).get_json()["data"]
    access = {"Authorization": f"Bearer {login['access_token']}"}
    refresh = {"Authorization": f"Bearer {login['refresh_token']}"}

    me = client.get("/api/auth/me", headers=access)
    assert me.status_code == 200
    assert me.get_json()["data"]["username"] == "u_flow"

    r = client.post("/api/auth/refresh", headers=refresh)
    assert r.status_code == 200
    assert r.get_json()["data"]["access_token"]

    # refresh token cũ đã bị xoay vòng -> không dùng lại được
    r2 = client.post("/api/auth/refresh", headers=refresh)
    assert r2.status_code == 401


def test_change_password_revokes_refresh_tokens(client, make_user):
    make_user("u_cp")
    login = client.post("/api/auth/login", json={"username": "u_cp", "password": "Password@123"}).get_json()["data"]
    access = {"Authorization": f"Bearer {login['access_token']}"}
    refresh = {"Authorization": f"Bearer {login['refresh_token']}"}

    resp = client.put(
        "/api/auth/change-password",
        headers=access,
        json={"old_password": "Password@123", "new_password": "NewPass@456"},
    )
    assert resp.status_code == 200
    # Refresh token cũ bị thu hồi
    assert client.post("/api/auth/refresh", headers=refresh).status_code == 401
    # Đăng nhập lại bằng mật khẩu mới
    assert client.post("/api/auth/login", json={"username": "u_cp", "password": "NewPass@456"}).status_code == 200
