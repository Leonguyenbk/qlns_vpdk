"""Bảng tin nội bộ, đối tượng nhận và quyền quản lý thông báo.

Revision ID: 0020_announcements
Revises: 0019_task_assigner_scope
Create Date: 2026-09-17
"""
import sqlalchemy as sa
from alembic import op

from app.permissions.constants import PERMISSION_DEFINITIONS


revision = "0020_announcements"
down_revision = "0019_task_assigner_scope"
branch_labels = None
depends_on = None

MYSQL_ARGS = {"mysql_charset": "utf8mb4", "mysql_engine": "InnoDB"}
PERMISSION_CODES = [
    "announcement.view",
    "announcement.create",
    "announcement.publish",
    "announcement.manage",
]


def upgrade():
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())

    if "announcements" not in existing:
        op.create_table(
            "announcements",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("category", sa.String(length=50), nullable=False, server_default="Thông báo"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("audience_type", sa.String(length=10), nullable=False, server_default="ALL"),
            sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_announcements_status_published", "announcements", ["status", "published_at"])
        op.create_index("ix_announcements_pinned", "announcements", ["is_pinned", "published_at"])
        op.create_index("ix_announcements_published_at", "announcements", ["published_at"])
        op.create_index("ix_announcements_expires_at", "announcements", ["expires_at"])

    if "announcement_units" not in existing:
        op.create_table(
            "announcement_units",
            sa.Column("announcement_id", sa.Integer(), nullable=False),
            sa.Column("unit_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["announcement_id"], ["announcements.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["unit_id"], ["organization_units.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("announcement_id", "unit_id"),
            **MYSQL_ARGS,
        )

    if "announcement_roles" not in existing:
        op.create_table(
            "announcement_roles",
            sa.Column("announcement_id", sa.Integer(), nullable=False),
            sa.Column("role_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["announcement_id"], ["announcements.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("announcement_id", "role_id"),
            **MYSQL_ARGS,
        )

    if "announcement_users" not in existing:
        op.create_table(
            "announcement_users",
            sa.Column("announcement_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["announcement_id"], ["announcements.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("announcement_id", "user_id"),
            **MYSQL_ARGS,
        )

    if "announcement_reads" not in existing:
        op.create_table(
            "announcement_reads",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("announcement_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["announcement_id"], ["announcements.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("announcement_id", "user_id", name="uq_announcement_read"),
            **MYSQL_ARGS,
        )
        op.create_index("ix_announcement_reads_announcement_id", "announcement_reads", ["announcement_id"])
        op.create_index("ix_announcement_reads_user_id", "announcement_reads", ["user_id"])
        op.create_index("ix_announcement_reads_user", "announcement_reads", ["user_id", "read_at"])

    meta = sa.MetaData()
    permissions = sa.Table("permissions", meta, autoload_with=bind)
    roles = sa.Table("roles", meta, autoload_with=bind)
    role_permissions = sa.Table("role_permissions", meta, autoload_with=bind)

    descriptions = dict(PERMISSION_DEFINITIONS)
    existing_codes = {
        row.code
        for row in bind.execute(sa.select(permissions.c.code).where(permissions.c.code.in_(PERMISSION_CODES)))
    }
    rows = [
        {"code": code, "description": descriptions[code]}
        for code in PERMISSION_CODES
        if code not in existing_codes
    ]
    if rows:
        op.bulk_insert(permissions, rows)

    permission_ids = {
        row.code: row.id
        for row in bind.execute(
            sa.select(permissions.c.id, permissions.c.code).where(permissions.c.code.in_(PERMISSION_CODES))
        )
    }
    role_ids = {row.code: row.id for row in bind.execute(sa.select(roles.c.id, roles.c.code))}
    existing_links = {
        (row.role_id, row.permission_id)
        for row in bind.execute(
            sa.select(role_permissions.c.role_id, role_permissions.c.permission_id).where(
                role_permissions.c.permission_id.in_(permission_ids.values())
            )
        )
    }

    grants: dict[int, set[str]] = {
        role_id: {"announcement.view"} for role_id in role_ids.values()
    }
    for role_code, codes in {
        "SYSTEM_ADMIN": set(PERMISSION_CODES),
        "OFFICE_LEADER": set(PERMISSION_CODES),
        "HR_ADMIN": {"announcement.view", "announcement.create"},
        "ORG_PERSONNEL": {"announcement.view", "announcement.create"},
    }.items():
        role_id = role_ids.get(role_code)
        if role_id:
            grants.setdefault(role_id, set()).update(codes)

    links = []
    for role_id, codes in grants.items():
        for code in codes:
            pair = (role_id, permission_ids[code])
            if pair not in existing_links:
                links.append({"role_id": pair[0], "permission_id": pair[1]})
    if links:
        op.bulk_insert(role_permissions, links)


def downgrade():
    bind = op.get_bind()
    meta = sa.MetaData()
    permissions = sa.Table("permissions", meta, autoload_with=bind)
    role_permissions = sa.Table("role_permissions", meta, autoload_with=bind)
    permission_ids = [
        row.id
        for row in bind.execute(sa.select(permissions.c.id).where(permissions.c.code.in_(PERMISSION_CODES)))
    ]
    if permission_ids:
        bind.execute(role_permissions.delete().where(role_permissions.c.permission_id.in_(permission_ids)))
        bind.execute(permissions.delete().where(permissions.c.id.in_(permission_ids)))

    existing = set(sa.inspect(bind).get_table_names())
    for table in (
        "announcement_reads",
        "announcement_users",
        "announcement_roles",
        "announcement_units",
        "announcements",
    ):
        if table in existing:
            op.drop_table(table)
