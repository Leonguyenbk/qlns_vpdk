"""Route quản lý vai trò và quyền."""
from __future__ import annotations

from flask import Blueprint

from ...common.auth_context import require_permission
from ...common.responses import success
from ...permissions import constants as perms
from ...services import role_service
from ...schemas import role_create_schema, role_update_schema
from .._helpers import actor_and_scope, audit_meta, validated_json

bp = Blueprint("roles", __name__, url_prefix="/api")


@bp.get("/roles")
@require_permission(perms.ROLE_VIEW)
def list_roles():
    return success(role_service.list_roles())


@bp.post("/roles")
@require_permission(perms.ROLE_MANAGE)
def create_role():
    actor, _ = actor_and_scope()
    return success(
        role_service.create_role(
            validated_json(role_create_schema), actor=actor, meta=audit_meta()
        ),
        "Tạo vai trò thành công",
        status_code=201,
    )


@bp.put("/roles/<int:role_id>")
@require_permission(perms.ROLE_MANAGE)
def update_role(role_id: int):
    actor, _ = actor_and_scope()
    return success(
        role_service.update_role(
            role_id,
            validated_json(role_update_schema),
            actor=actor,
            meta=audit_meta(),
        ),
        "Cập nhật vai trò thành công",
    )


@bp.delete("/roles/<int:role_id>")
@require_permission(perms.ROLE_MANAGE)
def delete_role(role_id: int):
    actor, _ = actor_and_scope()
    return success(
        role_service.delete_role(role_id, actor=actor, meta=audit_meta()),
        "Xóa vai trò thành công",
    )


@bp.get("/permissions")
@require_permission(perms.ROLE_VIEW, perms.USER_MANAGE)
def list_permissions():
    return success(role_service.list_permissions())
