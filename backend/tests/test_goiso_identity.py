"""P5: ánh xạ tài khoản platform -> danh tính goiso và cổng quyền trực quầy."""
from __future__ import annotations

import pytest

from app.modules.goiso import identity, legacy_app
from app.modules.goiso.identity import platform_user_to_goiso
from app.permissions.constants import (
    ROLE_GOISO_ADMIN,
    ROLE_GOISO_COUNTER,
    ROLE_SYSTEM_ADMIN,
    ROLE_VIEWER,
)


@pytest.fixture(autouse=True)
def _stub_branch(monkeypatch):
    """Không cần CSDL goiso thật: giả lập tra cứu chi nhánh."""
    branches = {"bmt": {"id": 15, "code": "bmt"}, "eakar": {"id": 1, "code": "eakar"}}
    monkeypatch.setattr(identity.legacy_db, "get_branch", lambda code: branches.get(code))


def test_counter_user_maps_to_staff_with_branch(db, make_user):
    u = make_user("nv1", role_code=ROLE_GOISO_COUNTER, scopes=())
    u.goiso_branch_code = "bmt"
    db.session.commit()

    shaped = platform_user_to_goiso(u)
    assert shaped["role"] == "staff"
    assert shaped["branch_id"] == 15
    assert shaped["branch_code"] == "bmt"
    assert "goiso.counter" in shaped["perms"]
    assert shaped["_platform"] is True
    assert legacy_app._can_work_counter(shaped) is True
    assert legacy_app._is_goiso_admin(shaped) is False


def test_goiso_admin_maps_to_admin(db, make_user):
    u = make_user("qtgs", role_code=ROLE_GOISO_ADMIN, scopes=())
    shaped = platform_user_to_goiso(u)
    assert shaped["role"] == "admin"
    assert legacy_app._is_goiso_admin(shaped) is True
    assert legacy_app._can_work_counter(shaped) is True


def test_system_admin_is_goiso_admin(db, make_user):
    u = make_user("root", role_code=ROLE_SYSTEM_ADMIN, scopes=())
    shaped = platform_user_to_goiso(u)
    assert shaped["role"] == "admin"
    assert legacy_app._is_goiso_admin(shaped) is True


def test_user_without_goiso_permission_cannot_work_counter(db, make_user):
    u = make_user("xem", role_code=ROLE_VIEWER, scopes=())
    shaped = platform_user_to_goiso(u)
    assert shaped["role"] == "staff"
    assert legacy_app._can_work_counter(shaped) is False


def test_legacy_session_user_keeps_old_behaviour(db):
    """User goiso cũ (SQLite, không có _platform) không bị chặn bởi cổng quyền mới."""
    legacy = {"role": "staff", "branch_id": 15, "active": True}  # không có 'perms'/'_platform'
    assert legacy_app._can_work_counter(legacy) is True
    assert legacy_app._is_goiso_admin(legacy) is False


def test_auth_login_sets_jwt_cookie(client, db, make_user):
    """Đăng nhập chung đặt cookie access_token để trang Jinja goiso dùng SSO."""
    make_user("ssouser", role_code=ROLE_GOISO_COUNTER, scopes=())
    resp = client.post("/api/auth/login", json={"username": "ssouser", "password": "Password@123"})
    assert resp.status_code == 200
    cookies = resp.headers.getlist("Set-Cookie")
    assert any(c.startswith("access_token_cookie=") for c in cookies)
