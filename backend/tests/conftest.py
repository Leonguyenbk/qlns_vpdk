"""Fixtures dùng chung cho test backend.

Test chạy trên SQLite in-memory và áp dụng chính các file migration Alembic
để đồng thời kiểm tra tính đúng đắn của migration.
"""
from __future__ import annotations

import os
from datetime import date

os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-0123456789-abcdefghij")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789-abcdefghijklmno")
os.environ.setdefault("LOG_LEVEL", "CRITICAL")

import pytest
from flask_migrate import upgrade as migrate_upgrade

from app import create_app
from app.extensions import db as _db
from app.models import (
    Employee,
    EmployeeAssignment,
    OrganizationUnit,
    Position,
    Role,
    UnitPositionLimit,
    User,
    UserUnitScope,
)
from app.permissions.constants import (
    ROLE_HR_ADMIN,
    ROLE_SYSTEM_ADMIN,
    ROLE_UNIT_MANAGER,
    ROLE_VIEWER,
)


@pytest.fixture(scope="session")
def _app_session():
    """Tạo app 1 lần và chạy migration (bao gồm seed roles/permissions)."""
    application = create_app("testing")
    with application.app_context():
        migrate_upgrade(
            directory=os.path.join(os.path.dirname(__file__), "..", "migrations")
        )
    yield application


@pytest.fixture
def app(_app_session):
    """Mỗi test chạy trong một application context mới -> g và session sạch."""
    with _app_session.app_context():
        yield _app_session
        _db.session.remove()


@pytest.fixture(autouse=True)
def _clean_db(app):
    """Xóa dữ liệu nghiệp vụ giữa các test, giữ lại roles/permissions từ migration."""
    yield
    _db.session.rollback()
    # Xóa theo thứ tự phụ thuộc; gồm cả bảng liên kết (SQLite không ép FK).
    for table in (
        "audit_logs",
        "refresh_tokens",
        "employee_assignments",
        "unit_position_limits",
        "user_roles",
        "user_unit_scopes",
        "employees",
        "users",
        "organization_units",
        "positions",
    ):
        _db.session.execute(_db.text(f"DELETE FROM {table}"))
    _db.session.commit()
    _db.session.remove()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def client(app):
    return app.test_client()


# ----------------------- Factories -----------------------
@pytest.fixture
def make_unit(db):
    def _make(code, name=None, unit_type="BRANCH", parent=None, is_active=True):
        u = OrganizationUnit(
            code=code,
            name=name or code,
            unit_type=unit_type,
            parent_id=parent.id if parent else None,
            is_active=is_active,
        )
        db.session.add(u)
        db.session.commit()
        return u

    return _make


@pytest.fixture
def make_position(db):
    def _make(code, name=None, level=10, is_active=True, managerial=False):
        p = Position(
            code=code, name=name or code, level=level, is_active=is_active,
            is_managerial=managerial,
        )
        db.session.add(p)
        db.session.commit()
        return p

    return _make


@pytest.fixture
def set_limit(db):
    def _make(unit, position, max_holders):
        lim = UnitPositionLimit(
            unit_id=unit.id, position_id=position.id, max_holders=max_holders
        )
        db.session.add(lim)
        db.session.commit()
        return lim

    return _make


@pytest.fixture
def make_employee(db):
    def _make(code, unit, position, full_name=None, start=date(2020, 1, 1), atype="RECRUITMENT"):
        emp = Employee(employee_code=code, full_name=full_name or code, status="WORKING")
        db.session.add(emp)
        db.session.flush()
        db.session.add(
            EmployeeAssignment(
                employee_id=emp.id,
                unit_id=unit.id,
                position_id=position.id,
                assignment_type=atype,
                start_date=start,
                is_primary=True,
            )
        )
        db.session.commit()
        return emp

    return _make


@pytest.fixture
def make_user(db):
    def _make(username, role_code=ROLE_HR_ADMIN, password="Password@123", scopes=(("GLOBAL", None),), is_active=True):
        role = db.session.query(Role).filter_by(code=role_code).first()
        u = User(username=username, full_name=username, email=f"{username}@ex.com", is_active=is_active)
        u.set_password(password)
        if role:
            u.roles.append(role)
        for stype, unit in scopes:
            u.unit_scopes.append(
                UserUnitScope(scope_type=stype, unit_id=unit.id if unit else None)
            )
        db.session.add(u)
        db.session.commit()
        return u

    return _make


@pytest.fixture
def auth_header(client):
    def _login(username, password="Password@123"):
        resp = client.post(
            "/api/auth/login", json={"username": username, "password": password}
        )
        assert resp.status_code == 200, resp.get_json()
        token = resp.get_json()["data"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _login


@pytest.fixture
def admin_user(make_user):
    return make_user("admin_test", role_code=ROLE_SYSTEM_ADMIN)


# Export role codes để test dùng
ROLE_CODES = {
    "SYSTEM_ADMIN": ROLE_SYSTEM_ADMIN,
    "HR_ADMIN": ROLE_HR_ADMIN,
    "UNIT_MANAGER": ROLE_UNIT_MANAGER,
    "VIEWER": ROLE_VIEWER,
}
