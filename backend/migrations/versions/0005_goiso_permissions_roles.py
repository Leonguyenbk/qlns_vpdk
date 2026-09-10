"""Quyền + vai trò module Gọi số, và cột users.goiso_branch_code

Revision ID: 0005_goiso_permissions_roles
Revises: 0004_unit_sort_index
Create Date: 2026-09-10

Phase 5 của việc hợp nhất goiso + nhân sự:
- Thêm quyền goiso.view / goiso.counter / goiso.admin.
- Thêm vai trò GOISO_ADMIN, GOISO_BRANCH_ADMIN, GOISO_COUNTER (trực cửa).
- Gắn các quyền goiso mới cho SYSTEM_ADMIN.
- Thêm cột cầu nối tạm users.goiso_branch_code.

Idempotent: chỉ chèn bản ghi còn thiếu.
"""
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

from app.permissions.constants import (
    GOISO_ADMIN,
    GOISO_COUNTER,
    GOISO_VIEW,
    ROLE_DEFINITIONS,
    ROLE_GOISO_ADMIN,
    ROLE_GOISO_BRANCH_ADMIN,
    ROLE_GOISO_COUNTER,
    ROLE_SYSTEM_ADMIN,
)

revision = "0005_goiso_permissions_roles"
down_revision = "0004_unit_sort_index"
branch_labels = None
depends_on = None

_NEW_PERMS = [
    (GOISO_VIEW, "Gọi số: xem hàng đợi, màn hình, bảng chờ, thống kê"),
    (GOISO_COUNTER, "Gọi số: trực một cửa/quầy (gọi, gọi lại, bỏ qua, hoàn thành)"),
    (GOISO_ADMIN, "Gọi số: cấu hình dịch vụ/quầy/màn hình, chi nhánh, thiết bị, đặt lịch"),
]
_NEW_ROLES = [ROLE_GOISO_ADMIN, ROLE_GOISO_BRANCH_ADMIN, ROLE_GOISO_COUNTER]


def _now():
    return datetime.now(timezone.utc)


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # --- 1. Cột cầu nối + cột di trú mật khẩu goiso ---
    cols = {c["name"] for c in insp.get_columns("users")}
    if "goiso_branch_code" not in cols:
        op.add_column(
            "users", sa.Column("goiso_branch_code", sa.String(length=50), nullable=True)
        )
        existing_idx = {i["name"] for i in insp.get_indexes("users")}
        if "ix_users_goiso_branch_code" not in existing_idx:
            op.create_index(
                "ix_users_goiso_branch_code", "users", ["goiso_branch_code"]
            )
    if "legacy_password_sha256" not in cols:
        op.add_column(
            "users",
            sa.Column("legacy_password_sha256", sa.String(length=64), nullable=True),
        )

    meta = sa.MetaData()
    permissions = sa.Table("permissions", meta, autoload_with=bind)
    roles = sa.Table("roles", meta, autoload_with=bind)
    role_permissions = sa.Table("role_permissions", meta, autoload_with=bind)

    # --- 2. Quyền goiso mới ---
    have_perms = {r.code for r in bind.execute(sa.select(permissions.c.code))}
    to_add = [
        {"code": c, "description": d} for c, d in _NEW_PERMS if c not in have_perms
    ]
    if to_add:
        op.bulk_insert(permissions, to_add)

    perm_id = {
        r.code: r.id
        for r in bind.execute(sa.select(permissions.c.id, permissions.c.code))
    }

    # --- 3. Vai trò goiso mới ---
    have_roles = {r.code for r in bind.execute(sa.select(roles.c.code))}
    now = _now()
    role_rows = []
    for code in _NEW_ROLES:
        if code in have_roles:
            continue
        cfg = ROLE_DEFINITIONS[code]
        role_rows.append(
            {
                "code": code,
                "name": cfg["name"],
                "description": cfg["description"],
                "is_system": cfg["is_system"],
                "created_at": now,
                "updated_at": now,
            }
        )
    if role_rows:
        op.bulk_insert(roles, role_rows)

    role_id = {
        r.code: r.id for r in bind.execute(sa.select(roles.c.id, roles.c.code))
    }

    # --- 4. Liên kết role -> permission (goiso mới + bổ sung cho SYSTEM_ADMIN) ---
    have_links = {
        (r.role_id, r.permission_id)
        for r in bind.execute(
            sa.select(role_permissions.c.role_id, role_permissions.c.permission_id)
        )
    }
    link_rows = []
    targets = list(_NEW_ROLES) + [ROLE_SYSTEM_ADMIN]
    for rcode in targets:
        rid = role_id.get(rcode)
        if rid is None:
            continue
        for pcode in ROLE_DEFINITIONS[rcode]["permissions"]:
            pid = perm_id.get(pcode)
            if pid is None:
                continue
            if (rid, pid) not in have_links:
                link_rows.append({"role_id": rid, "permission_id": pid})
    if link_rows:
        op.bulk_insert(role_permissions, link_rows)


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    bind.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN "
            "(SELECT id FROM permissions WHERE code IN :codes)"
        ).bindparams(sa.bindparam("codes", expanding=True)),
        {"codes": [c for c, _ in _NEW_PERMS]},
    )
    bind.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE role_id IN "
            "(SELECT id FROM roles WHERE code IN :codes)"
        ).bindparams(sa.bindparam("codes", expanding=True)),
        {"codes": _NEW_ROLES},
    )
    bind.execute(
        sa.text("DELETE FROM roles WHERE code IN :codes").bindparams(
            sa.bindparam("codes", expanding=True)
        ),
        {"codes": _NEW_ROLES},
    )
    bind.execute(
        sa.text("DELETE FROM permissions WHERE code IN :codes").bindparams(
            sa.bindparam("codes", expanding=True)
        ),
        {"codes": [c for c, _ in _NEW_PERMS]},
    )

    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "legacy_password_sha256" in user_cols:
        op.drop_column("users", "legacy_password_sha256")
    if "goiso_branch_code" in user_cols:
        if "ix_users_goiso_branch_code" in {
            i["name"] for i in insp.get_indexes("users")
        }:
            op.drop_index("ix_users_goiso_branch_code", table_name="users")
        op.drop_column("users", "goiso_branch_code")
