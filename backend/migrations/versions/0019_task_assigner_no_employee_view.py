"""Bỏ quyền xem Nhân sự/Cơ cấu đơn vị khỏi Người được giao quyền giao việc (TASK_ASSIGNER)

Revision ID: 0019_task_assigner_scope
Revises: 0018_hr_admin_no_audit
Create Date: 2026-09-15

TASK_ASSIGNER là người được uỷ quyền giao việc/nghiệm thu trong phạm vi cụ thể,
"không nhất thiết là lãnh đạo đơn vị" (không có chức vụ quản lý) — nhưng trước
đây vẫn có employee.view/unit.view nên nhìn thấy mục Quản lý (Nhân sự, Cơ cấu
đơn vị) trên sidebar. Việc chọn người nhận việc đã dùng API riêng
(assignable-people, chỉ cần task.create/task.assign), không phụ thuộc
employee.view — nên bỏ 2 quyền này không ảnh hưởng chức năng giao việc.

Chỉ xoá 2 role_permissions của riêng TASK_ASSIGNER. Không đụng permission/vai
trò khác (UNIT_HEAD, OFFICE_LEADER... vẫn giữ nguyên vì là lãnh đạo có chức
vụ). Idempotent.
"""
import sqlalchemy as sa
from alembic import op

from app.permissions.constants import ROLE_TASK_ASSIGNER

revision = "0019_task_assigner_scope"
down_revision = "0018_hr_admin_no_audit"
branch_labels = None
depends_on = None

_REMOVED_CODES = ["employee.view", "unit.view"]


def upgrade():
    bind = op.get_bind()
    meta = sa.MetaData()
    permissions = sa.Table("permissions", meta, autoload_with=bind)
    roles = sa.Table("roles", meta, autoload_with=bind)
    role_permissions = sa.Table("role_permissions", meta, autoload_with=bind)

    role_id = bind.execute(sa.select(roles.c.id).where(roles.c.code == ROLE_TASK_ASSIGNER)).scalar()
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

    role_id = bind.execute(sa.select(roles.c.id).where(roles.c.code == ROLE_TASK_ASSIGNER)).scalar()
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
