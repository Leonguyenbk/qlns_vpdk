"""Vai trò STAFF (tự phục vụ) — mặc định cho viên chức không giữ chức vụ quản
lý khi tạo tài khoản hàng loạt (scripts/create_employee_accounts.py).

Revision ID: 0010_staff_role
Revises: 0009_unit_username_prefix
Create Date: 2026-09-11

Không thêm permission mới (dùng lại task.view_own/kpi.view_own/kpi.self_assess
đã có từ 0008) — chỉ thêm 1 vai trò mới. Idempotent, không xoá/sửa vai trò cũ.
"""
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

from app.permissions.constants import ROLE_DEFINITIONS, ROLE_STAFF

revision = "0010_staff_role"
down_revision = "0009_unit_username_prefix"
branch_labels = None
depends_on = None


def _now():
    return datetime.now(timezone.utc)


def upgrade():
    bind = op.get_bind()
    meta = sa.MetaData()
    permissions = sa.Table("permissions", meta, autoload_with=bind)
    roles = sa.Table("roles", meta, autoload_with=bind)
    role_permissions = sa.Table("role_permissions", meta, autoload_with=bind)

    have_roles = {r.code for r in bind.execute(sa.select(roles.c.code))}
    if ROLE_STAFF not in have_roles:
        cfg = ROLE_DEFINITIONS[ROLE_STAFF]
        now = _now()
        op.bulk_insert(roles, [{
            "code": ROLE_STAFF, "name": cfg["name"], "description": cfg["description"],
            "is_system": cfg["is_system"], "created_at": now, "updated_at": now,
        }])

    role_id = bind.execute(sa.select(roles.c.id).where(roles.c.code == ROLE_STAFF)).scalar()
    perm_id = {r.code: r.id for r in bind.execute(sa.select(permissions.c.id, permissions.c.code))}
    have_links = {
        (r.role_id, r.permission_id)
        for r in bind.execute(sa.select(role_permissions.c.role_id, role_permissions.c.permission_id))
    }
    link_rows = []
    for pcode in ROLE_DEFINITIONS[ROLE_STAFF]["permissions"]:
        pid = perm_id.get(pcode)
        if pid and (role_id, pid) not in have_links:
            link_rows.append({"role_id": role_id, "permission_id": pid})
    if link_rows:
        op.bulk_insert(role_permissions, link_rows)


def downgrade():
    bind = op.get_bind()
    bind.execute(
        sa.text("DELETE FROM role_permissions WHERE role_id IN (SELECT id FROM roles WHERE code=:c)"),
        {"c": ROLE_STAFF},
    )
    bind.execute(sa.text("DELETE FROM roles WHERE code=:c"), {"c": ROLE_STAFF})
