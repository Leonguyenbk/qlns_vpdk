"""Route quản lý tài khoản và phân quyền."""
from __future__ import annotations

from flask import Blueprint, request

from ...common.auth_context import require_permission
from ...common.responses import paginated, success
from ...permissions import constants as perms
from ...services import user_service
from ...schemas import (
    reset_password_schema,
    user_create_schema,
    user_roles_schema,
    user_scopes_schema,
    user_update_schema,
)
from .._helpers import actor_and_scope, audit_meta, validated_json

bp = Blueprint("users", __name__, url_prefix="/api/users")


@bp.get("")
@require_permission(perms.USER_VIEW)
def list_users():
    res = user_service.list_users(request.args)
    return paginated(res["items"], res["page"], res["page_size"], res["total"])


@bp.post("")
@require_permission(perms.USER_MANAGE)
def create_user():
    actor, _ = actor_and_scope()
    return success(
        user_service.create_user(
            validated_json(user_create_schema), actor=actor, meta=audit_meta()
        ),
        "Tạo tài khoản thành công",
        status_code=201,
    )


@bp.get("/<int:user_id>")
@require_permission(perms.USER_VIEW)
def get_user(user_id: int):
    return success(user_service.get_user(user_id))


@bp.put("/<int:user_id>")
@require_permission(perms.USER_MANAGE)
def update_user(user_id: int):
    actor, _ = actor_and_scope()
    return success(
        user_service.update_user(
            user_id,
            validated_json(user_update_schema),
            actor=actor,
            meta=audit_meta(),
        ),
        "Cập nhật tài khoản thành công",
    )


@bp.post("/<int:user_id>/reset-password")
@require_permission(perms.USER_MANAGE)
def reset_password(user_id: int):
    actor, _ = actor_and_scope()
    return success(
        user_service.reset_password(
            user_id,
            validated_json(reset_password_schema),
            actor=actor,
            meta=audit_meta(),
        ),
        "Đặt lại mật khẩu thành công",
    )


@bp.post("/<int:user_id>/roles")
@require_permission(perms.USER_MANAGE)
def set_roles(user_id: int):
    actor, _ = actor_and_scope()
    return success(
        user_service.set_roles(
            user_id,
            validated_json(user_roles_schema),
            actor=actor,
            meta=audit_meta(),
        ),
        "Cập nhật vai trò thành công",
    )


@bp.post("/<int:user_id>/unit-scopes")
@require_permission(perms.USER_MANAGE)
def set_unit_scopes(user_id: int):
    actor, _ = actor_and_scope()
    return success(
        user_service.set_unit_scopes(
            user_id,
            validated_json(user_scopes_schema),
            actor=actor,
            meta=audit_meta(),
        ),
        "Cập nhật phạm vi đơn vị thành công",
    )
