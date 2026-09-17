"""API bảng tin nội bộ."""
from __future__ import annotations

from flask import Blueprint, request

from ...common.auth_context import require_permission
from ...common.responses import paginated, success
from ...permissions import constants as perms
from ...schemas import (
    announcement_create_schema,
    announcement_status_schema,
    announcement_update_schema,
)
from ...services import announcement_service
from .._helpers import actor_and_scope, audit_meta, validated_json


bp = Blueprint("announcements", __name__, url_prefix="/api/announcements")


@bp.get("")
@require_permission(perms.ANNOUNCEMENT_VIEW)
def list_announcements():
    actor, _ = actor_and_scope()
    result = announcement_service.list_announcements(request.args, actor=actor)
    response, status = paginated(
        result["items"], result["page"], result["page_size"], result["total"]
    )
    body = response.get_json()
    body["data"]["unread"] = result["unread"]
    return body, status


@bp.get("/audience-options")
@require_permission(perms.ANNOUNCEMENT_CREATE, perms.ANNOUNCEMENT_MANAGE)
def get_audience_options():
    return success(announcement_service.audience_options())


@bp.post("")
@require_permission(perms.ANNOUNCEMENT_CREATE, perms.ANNOUNCEMENT_MANAGE)
def create_announcement():
    actor, _ = actor_and_scope()
    data = announcement_service.create_announcement(
        validated_json(announcement_create_schema), actor=actor, meta=audit_meta()
    )
    return success(data, "Đã tạo bản nháp thông báo", status_code=201)


@bp.get("/<int:announcement_id>")
@require_permission(perms.ANNOUNCEMENT_VIEW)
def get_announcement(announcement_id: int):
    actor, _ = actor_and_scope()
    return success(announcement_service.get_announcement(announcement_id, actor=actor))


@bp.put("/<int:announcement_id>")
@require_permission(perms.ANNOUNCEMENT_CREATE, perms.ANNOUNCEMENT_MANAGE)
def update_announcement(announcement_id: int):
    actor, _ = actor_and_scope()
    data = announcement_service.update_announcement(
        announcement_id,
        validated_json(announcement_update_schema),
        actor=actor,
        meta=audit_meta(),
    )
    return success(data, "Đã cập nhật thông báo")


@bp.delete("/<int:announcement_id>")
@require_permission(perms.ANNOUNCEMENT_CREATE, perms.ANNOUNCEMENT_MANAGE)
def delete_announcement(announcement_id: int):
    actor, _ = actor_and_scope()
    announcement_service.delete_announcement(
        announcement_id, actor=actor, meta=audit_meta()
    )
    return success(None, "Đã xóa thông báo")


@bp.post("/<int:announcement_id>/status")
@require_permission(perms.ANNOUNCEMENT_PUBLISH, perms.ANNOUNCEMENT_MANAGE)
def set_status(announcement_id: int):
    actor, _ = actor_and_scope()
    payload = validated_json(announcement_status_schema)
    data = announcement_service.set_status(
        announcement_id, payload["status"], actor=actor, meta=audit_meta()
    )
    message = "Đã phát hành thông báo" if payload["status"] == "published" else "Đã thu hồi thông báo"
    return success(data, message)


@bp.post("/<int:announcement_id>/read")
@require_permission(perms.ANNOUNCEMENT_VIEW)
def mark_read(announcement_id: int):
    actor, _ = actor_and_scope()
    return success(announcement_service.mark_read(announcement_id, actor=actor))
