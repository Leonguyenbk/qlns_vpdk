"""Route danh mục chức vụ."""
from __future__ import annotations

from flask import Blueprint, request

from ...common.auth_context import require_permission
from ...common.responses import success
from ...permissions import constants as perms
from ...services import position_service
from ...schemas import position_create_schema, position_update_schema
from .._helpers import actor_and_scope, audit_meta, validated_json

bp = Blueprint("positions", __name__, url_prefix="/api/positions")


@bp.get("")
@require_permission(perms.POSITION_VIEW)
def list_positions():
    only_active = request.args.get("only_active")
    flag = None if only_active is None else str(only_active).lower() in ("1", "true")
    return success(position_service.list_positions(only_active=flag))


@bp.post("")
@require_permission(perms.POSITION_MANAGE)
def create_position():
    actor, _ = actor_and_scope()
    return success(
        position_service.create_position(
            validated_json(position_create_schema), actor=actor, meta=audit_meta()
        ),
        "Tạo chức vụ thành công",
        status_code=201,
    )


@bp.put("/<int:position_id>")
@require_permission(perms.POSITION_MANAGE)
def update_position(position_id: int):
    actor, _ = actor_and_scope()
    return success(
        position_service.update_position(
            position_id,
            validated_json(position_update_schema),
            actor=actor,
            meta=audit_meta(),
        ),
        "Cập nhật chức vụ thành công",
    )


@bp.delete("/<int:position_id>")
@require_permission(perms.POSITION_MANAGE)
def delete_position(position_id: int):
    actor, _ = actor_and_scope()
    res = position_service.delete_position(position_id, actor=actor, meta=audit_meta())
    msg = "Đã xóa chức vụ" if res["hard_deleted"] else "Chức vụ có dữ liệu nên chỉ được ngừng hoạt động"
    return success(res, msg)
