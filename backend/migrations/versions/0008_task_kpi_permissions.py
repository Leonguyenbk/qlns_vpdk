"""Quyền + vai trò phân hệ Giao việc – Theo dõi nhiệm vụ – Đánh giá KPI

Revision ID: 0008_task_kpi_permissions
Revises: 0007_task_kpi_schema
Create Date: 2026-09-11

- Thêm 18 quyền task.*/kpi.* mới.
- Thêm 4 vai trò mới: OFFICE_LEADER, ORG_PERSONNEL, UNIT_HEAD, TASK_ASSIGNER.
- Gắn quyền tự phục vụ (task.view_own/kpi.view_own/kpi.self_assess) cho các
  vai trò hiện có (HR_ADMIN, UNIT_MANAGER, VIEWER, GOISO_*) để MỌI tài khoản
  đang có vẫn thấy được trang "Công việc của tôi" sau khi nâng cấp.
- Bổ sung toàn bộ quyền mới cho SYSTEM_ADMIN.

Idempotent: chỉ chèn bản ghi còn thiếu; KHÔNG xoá/sửa role hoặc user hiện có.
"""
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

from app.permissions.constants import (
    PERMISSION_DEFINITIONS,
    ROLE_DEFINITIONS,
    ROLE_GOISO_ADMIN,
    ROLE_GOISO_BRANCH_ADMIN,
    ROLE_GOISO_COUNTER,
    ROLE_HR_ADMIN,
    ROLE_OFFICE_LEADER,
    ROLE_ORG_PERSONNEL,
    ROLE_SYSTEM_ADMIN,
    ROLE_TASK_ASSIGNER,
    ROLE_UNIT_HEAD,
    ROLE_UNIT_MANAGER,
    ROLE_VIEWER,
)

revision = "0008_task_kpi_permissions"
down_revision = "0007_task_kpi_schema"
branch_labels = None
depends_on = None

_NEW_PERM_CODES = [c for c, _ in PERMISSION_DEFINITIONS if c.startswith(("task.", "kpi."))]
_NEW_ROLES = [ROLE_OFFICE_LEADER, ROLE_ORG_PERSONNEL, ROLE_UNIT_HEAD, ROLE_TASK_ASSIGNER]
# Vai trò hiện có cần bổ sung quyền tự phục vụ (không đổi is_system/tên/mô tả)
_UPDATE_EXISTING_ROLES = [
    ROLE_HR_ADMIN, ROLE_UNIT_MANAGER, ROLE_VIEWER,
    ROLE_GOISO_ADMIN, ROLE_GOISO_BRANCH_ADMIN, ROLE_GOISO_COUNTER,
]


def _now():
    return datetime.now(timezone.utc)


def upgrade():
    bind = op.get_bind()
    meta = sa.MetaData()
    permissions = sa.Table("permissions", meta, autoload_with=bind)
    roles = sa.Table("roles", meta, autoload_with=bind)
    role_permissions = sa.Table("role_permissions", meta, autoload_with=bind)

    # --- 1. Quyền mới ---
    perm_desc = dict(PERMISSION_DEFINITIONS)
    have_perms = {r.code for r in bind.execute(sa.select(permissions.c.code))}
    to_add = [
        {"code": c, "description": perm_desc[c]} for c in _NEW_PERM_CODES if c not in have_perms
    ]
    if to_add:
        op.bulk_insert(permissions, to_add)

    perm_id = {r.code: r.id for r in bind.execute(sa.select(permissions.c.id, permissions.c.code))}

    # --- 2. Vai trò mới ---
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

    role_id = {r.code: r.id for r in bind.execute(sa.select(roles.c.id, roles.c.code))}

    # --- 3. Gắn quyền cho vai trò mới + SYSTEM_ADMIN + bổ sung tự phục vụ cho vai trò cũ ---
    have_links = {
        (r.role_id, r.permission_id)
        for r in bind.execute(sa.select(role_permissions.c.role_id, role_permissions.c.permission_id))
    }
    link_rows = []
    targets = list(_NEW_ROLES) + [ROLE_SYSTEM_ADMIN] + _UPDATE_EXISTING_ROLES
    for rcode in targets:
        rid = role_id.get(rcode)
        if rid is None:
            continue
        wanted_codes = ROLE_DEFINITIONS[rcode]["permissions"]
        if rcode in _UPDATE_EXISTING_ROLES:
            # Chỉ bổ sung phần quyền task.*/kpi.* mới — không đụng cấu hình quyền cũ
            wanted_codes = [c for c in wanted_codes if c in _NEW_PERM_CODES]
        for pcode in wanted_codes:
            pid = perm_id.get(pcode)
            if pid is None:
                continue
            if (rid, pid) not in have_links:
                link_rows.append({"role_id": rid, "permission_id": pid})
    if link_rows:
        op.bulk_insert(role_permissions, link_rows)


def downgrade():
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN "
            "(SELECT id FROM permissions WHERE code IN :codes)"
        ).bindparams(sa.bindparam("codes", expanding=True)),
        {"codes": _NEW_PERM_CODES},
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
        {"codes": _NEW_PERM_CODES},
    )
