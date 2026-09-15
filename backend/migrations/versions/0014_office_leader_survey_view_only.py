"""Thu hẹp quyền khảo sát của Lãnh đạo Văn phòng (OFFICE_LEADER)

Revision ID: 0014_office_leader_survey_view_only
Revises: 0013_survey_respondent_contact
Create Date: 2026-09-15

Migration 0011 gán nhầm toàn bộ quyền survey.* (kể cả create/update/delete/
manage_questions/export) cho vai trò OFFICE_LEADER — thực tế Lãnh đạo Văn
phòng chỉ cần xem kết quả và thống kê khảo sát (toàn Văn phòng), việc soạn/
xuất bản/xoá khảo sát do Bộ phận tổ chức cán bộ (ORG_PERSONNEL) hoặc người
được giao vai trò SURVEY_EDITOR (thêm ở 0012) đảm nhiệm.

Chỉ xoá 5 role_permissions của riêng OFFICE_LEADER (survey.create/update/
delete/manage_questions/export) — giữ lại survey.view/view_statistics/
manage_all_branches. Không đụng permission/vai trò khác. Idempotent.
"""
import sqlalchemy as sa
from alembic import op

from app.permissions.constants import ROLE_OFFICE_LEADER

revision = "0014_office_leader_survey_view_only"
down_revision = "0013_survey_respondent_contact"
branch_labels = None
depends_on = None

_REMOVED_CODES = [
    "survey.create",
    "survey.update",
    "survey.delete",
    "survey.manage_questions",
    "survey.export",
]


def upgrade():
    bind = op.get_bind()
    meta = sa.MetaData()
    permissions = sa.Table("permissions", meta, autoload_with=bind)
    roles = sa.Table("roles", meta, autoload_with=bind)
    role_permissions = sa.Table("role_permissions", meta, autoload_with=bind)

    role_id = bind.execute(
        sa.select(roles.c.id).where(roles.c.code == ROLE_OFFICE_LEADER)
    ).scalar()
    if role_id is None:
        return
    perm_ids = [
        r.id
        for r in bind.execute(
            sa.select(permissions.c.id).where(permissions.c.code.in_(_REMOVED_CODES))
        )
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

    role_id = bind.execute(
        sa.select(roles.c.id).where(roles.c.code == ROLE_OFFICE_LEADER)
    ).scalar()
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
