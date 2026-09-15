"""Vai trò SURVEY_EDITOR (Biên tập khảo sát)

Revision ID: 0012_survey_editor_role
Revises: 0011_survey_module
Create Date: 2026-09-15

Vai trò gán thêm cho viên chức không giữ chức vụ quản lý nhưng được giao
biên tập một/một số khảo sát cụ thể — trước đây chỉ ORG_PERSONNEL/
OFFICE_LEADER/UNIT_HEAD... (đều gắn với chức vụ quản lý) mới có quyền
survey.*, nên viên chức thường (vai trò STAFF) được giao việc này không
đăng nhập vào biên tập được.

Không thêm permission mới (dùng lại survey.* đã có từ 0011) — chỉ thêm 1
vai trò mới. Idempotent, không xoá/sửa vai trò cũ.
"""
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

from app.permissions.constants import ROLE_DEFINITIONS, ROLE_SURVEY_EDITOR

revision = "0012_survey_editor_role"
down_revision = "0011_survey_module"
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
    if ROLE_SURVEY_EDITOR not in have_roles:
        cfg = ROLE_DEFINITIONS[ROLE_SURVEY_EDITOR]
        now = _now()
        op.bulk_insert(roles, [{
            "code": ROLE_SURVEY_EDITOR, "name": cfg["name"], "description": cfg["description"],
            "is_system": cfg["is_system"], "created_at": now, "updated_at": now,
        }])

    role_id = bind.execute(sa.select(roles.c.id).where(roles.c.code == ROLE_SURVEY_EDITOR)).scalar()
    perm_id = {r.code: r.id for r in bind.execute(sa.select(permissions.c.id, permissions.c.code))}
    have_links = {
        (r.role_id, r.permission_id)
        for r in bind.execute(sa.select(role_permissions.c.role_id, role_permissions.c.permission_id))
    }
    link_rows = []
    for pcode in ROLE_DEFINITIONS[ROLE_SURVEY_EDITOR]["permissions"]:
        pid = perm_id.get(pcode)
        if pid and (role_id, pid) not in have_links:
            link_rows.append({"role_id": role_id, "permission_id": pid})
    if link_rows:
        op.bulk_insert(role_permissions, link_rows)


def downgrade():
    bind = op.get_bind()
    bind.execute(
        sa.text("DELETE FROM role_permissions WHERE role_id IN (SELECT id FROM roles WHERE code=:c)"),
        {"c": ROLE_SURVEY_EDITOR},
    )
    bind.execute(sa.text("DELETE FROM roles WHERE code=:c"), {"c": ROLE_SURVEY_EDITOR})
