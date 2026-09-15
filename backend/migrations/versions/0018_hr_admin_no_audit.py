"""Bỏ quyền Nhật ký hệ thống khỏi Quản trị nhân sự (HR_ADMIN)

Revision ID: 0018_hr_admin_no_audit
Revises: 0017_hr_admin_task_perms
Create Date: 2026-09-15

HR_ADMIN có audit.view khiến mục "Quản trị" (dùng chung với Quản trị hệ
thống) hiện ra trên sidebar và dẫn vào /admin — không đúng với vai trò "chỉ
quản lý nhân sự và giao việc" đã thống nhất. Bỏ audit.view; vẫn giữ nguyên
toàn bộ quyền nhân sự/đơn vị/chức vụ/giao việc/khảo sát.

Chỉ xoá 1 role_permissions của riêng HR_ADMIN. Không đụng permission/vai trò
khác. Idempotent.
"""
import sqlalchemy as sa
from alembic import op

from app.permissions.constants import ROLE_HR_ADMIN

revision = "0018_hr_admin_no_audit"
down_revision = "0017_hr_admin_task_perms"
branch_labels = None
depends_on = None

_REMOVED_CODES = ["audit.view"]


def upgrade():
    bind = op.get_bind()
    meta = sa.MetaData()
    permissions = sa.Table("permissions", meta, autoload_with=bind)
    roles = sa.Table("roles", meta, autoload_with=bind)
    role_permissions = sa.Table("role_permissions", meta, autoload_with=bind)

    role_id = bind.execute(sa.select(roles.c.id).where(roles.c.code == ROLE_HR_ADMIN)).scalar()
    if role_id is None:
        return
    perm_ids = [
        r.id
        for r in bind.execute(sa.select(permissions.c.id).where(permissions.c.code.in_(_REMOVED_CODES)))
    ]
    if perm_ids:
        bind.execute(
            role_permissions.delete().where(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id.in_(perm_ids),
            )
        )


def downgrade():
    bind = op.get_bind()
    meta = sa.MetaData()
    permissions = sa.Table("permissions", meta, autoload_with=bind)
    roles = sa.Table("roles", meta, autoload_with=bind)
    role_permissions = sa.Table("role_permissions", meta, autoload_with=bind)

    role_id = bind.execute(sa.select(roles.c.id).where(roles.c.code == ROLE_HR_ADMIN)).scalar()
    if role_id is None:
        return
    perm_id = {
        r.code: r.id
        for r in bind.execute(
            sa.select(permissions.c.id, permissions.c.code).where(
                permissions.c.code.in_(_REMOVED_CODES)
            )
        )
    }
    have_links = {
        r.permission_id
        for r in bind.execute(
            sa.select(role_permissions.c.permission_id).where(role_permissions.c.role_id == role_id)
        )
    }
    rows = [
        {"role_id": role_id, "permission_id": pid}
        for code, pid in perm_id.items()
        if pid not in have_links
    ]
    if rows:
        op.bulk_insert(role_permissions, rows)
