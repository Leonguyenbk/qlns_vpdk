"""Seed quyền và vai trò mẫu

Revision ID: 0002_seed_roles_permissions
Revises: 0001_initial_schema
Create Date: 2026-08-31
"""
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

from app.permissions.constants import PERMISSION_DEFINITIONS, ROLE_DEFINITIONS

revision = "0002_seed_roles_permissions"
down_revision = "0001_initial_schema"
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

    # --- Permissions ---
    op.bulk_insert(
        permissions,
        [{"code": code, "description": desc} for code, desc in PERMISSION_DEFINITIONS],
    )
    perm_id = {
        row.code: row.id
        for row in bind.execute(sa.select(permissions.c.id, permissions.c.code))
    }

    # --- Roles ---
    now = _now()
    op.bulk_insert(
        roles,
        [
            {
                "code": code,
                "name": cfg["name"],
                "description": cfg["description"],
                "is_system": cfg["is_system"],
                "created_at": now,
                "updated_at": now,
            }
            for code, cfg in ROLE_DEFINITIONS.items()
        ],
    )
    role_id = {
        row.code: row.id for row in bind.execute(sa.select(roles.c.id, roles.c.code))
    }

    # --- Role -> Permission ---
    links = []
    for code, cfg in ROLE_DEFINITIONS.items():
        for pcode in cfg["permissions"]:
            links.append(
                {"role_id": role_id[code], "permission_id": perm_id[pcode]}
            )
    op.bulk_insert(role_permissions, links)


def downgrade():
    bind = op.get_bind()
    codes = list(ROLE_DEFINITIONS.keys())
    bind.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE role_id IN "
            "(SELECT id FROM roles WHERE code IN :codes)"
        ).bindparams(sa.bindparam("codes", expanding=True)),
        {"codes": codes},
    )
    bind.execute(
        sa.text("DELETE FROM roles WHERE code IN :codes").bindparams(
            sa.bindparam("codes", expanding=True)
        ),
        {"codes": codes},
    )
    bind.execute(sa.text("DELETE FROM permissions"))
