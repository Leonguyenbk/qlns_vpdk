"""Route cơ cấu đơn vị và giới hạn chức vụ theo đơn vị."""
from __future__ import annotations

from flask import Blueprint, request

from ...common.auth_context import require_permission
from ...common.responses import success
from ...permissions import constants as perms
from ...services import position_service, unit_service
from ...schemas import (
    position_limit_create_schema,
    position_limit_update_schema,
    unit_create_schema,
    unit_update_schema,
)
from .._helpers import actor_and_scope, audit_meta, validated_json

bp = Blueprint("units", __name__, url_prefix="/api/units")


@bp.get("")
@require_permission(perms.UNIT_VIEW)
def list_units():
    only_active = request.args.get("only_active")
    flag = None if only_active is None else str(only_active).lower() in ("1", "true")
    return success(unit_service.list_units(only_active=flag))


@bp.get("/tree")
@require_permission(perms.UNIT_VIEW)
def unit_tree():
    return success(unit_service.get_tree())


@bp.get("/<int:unit_id>")
@require_permission(perms.UNIT_VIEW)
def get_unit(unit_id: int):
    return success(unit_service.get_unit(unit_id))


@bp.post("")
@require_permission(perms.UNIT_MANAGE)
def create_unit():
    actor, _ = actor_and_scope()
    return success(
        unit_service.create_unit(
            validated_json(unit_create_schema), actor=actor, meta=audit_meta()
        ),
        "Tạo đơn vị thành công",
        status_code=201,
    )


@bp.put("/<int:unit_id>")
@require_permission(perms.UNIT_MANAGE)
def update_unit(unit_id: int):
    actor, _ = actor_and_scope()
    return success(
        unit_service.update_unit(
            unit_id,
            validated_json(unit_update_schema),
            actor=actor,
            meta=audit_meta(),
        ),
        "Cập nhật đơn vị thành công",
    )


@bp.delete("/<int:unit_id>")
@require_permission(perms.UNIT_MANAGE)
def delete_unit(unit_id: int):
    actor, _ = actor_and_scope()
    res = unit_service.deactivate_unit(unit_id, actor=actor, meta=audit_meta())
    return success(res, res["message"])


# --------- Giới hạn chức vụ theo đơn vị ---------
@bp.get("/<int:unit_id>/position-limits")
@require_permission(perms.POSITION_VIEW)
def list_limits(unit_id: int):
    return success(position_service.list_limits(unit_id))


@bp.post("/<int:unit_id>/position-limits")
@require_permission(perms.POSITION_MANAGE)
def create_limit(unit_id: int):
    actor, _ = actor_and_scope()
    return success(
        position_service.create_limit(
            unit_id,
            validated_json(position_limit_create_schema),
            actor=actor,
            meta=audit_meta(),
        ),
        "Tạo giới hạn chức vụ thành công",
        status_code=201,
    )


@bp.put("/<int:unit_id>/position-limits/<int:limit_id>")
@require_permission(perms.POSITION_MANAGE)
def update_limit(unit_id: int, limit_id: int):
    actor, _ = actor_and_scope()
    return success(
        position_service.update_limit(
            unit_id,
            limit_id,
            validated_json(position_limit_update_schema),
            actor=actor,
            meta=audit_meta(),
        ),
        "Cập nhật giới hạn chức vụ thành công",
    )
