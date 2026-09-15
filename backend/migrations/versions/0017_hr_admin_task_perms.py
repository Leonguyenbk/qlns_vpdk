"""Thêm quyền Giao việc cho Quản trị nhân sự (HR_ADMIN)

Revision ID: 0017_hr_admin_task_perms
Revises: 0016_survey_question_sections
Create Date: 2026-09-15

Quản trị nhân sự (HR_ADMIN) trước đây chỉ quản lý hồ sơ/đơn vị/chức vụ, không
giao việc được cho nhân sự do mình quản lý. Thêm task.view_all/create/assign/
manage/accept — vẫn KHÔNG có user.manage/role.manage (Quản trị hệ thống),
goiso.* hay kpi.criteria_manage/period_manage/approve (Lãnh đạo Văn phòng).

Chỉ thêm 5 role_permissions cho riêng HR_ADMIN, không đụng permission/vai trò
khác. Idempotent (kiểm tra tồn tại trước khi chèn, an toàn khi chạy lại).
"""
import sqlalchemy as sa
from alembic import op

from app.permissions.constants import ROLE_HR_ADMIN

revision = "0017_hr_admin_task_perms"
down_revision = "0016_survey_question_sections"
branch_labels = None
depends_on = None

_ADDED_CODES = [
    "task.view_all",
    "task.create",
    "task.assign",
    "task.manage",
    "task.accept",
]


def upgrade():
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
                permissions.c.code.in_(_ADDED_CODES)
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


def downgrade():
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
        for r in bind.execute(sa.select(permissions.c.id).where(permissions.c.code.in_(_ADDED_CODES)))
    ]
    if perm_ids:
        bind.execute(
            role_permissions.delete().where(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id.in_(perm_ids),
            )
        )
