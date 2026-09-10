"""Route nhật ký hệ thống."""
from __future__ import annotations

from flask import Blueprint, request

from ...common.auth_context import require_permission
from ...common.responses import paginated
from ...common.utils import clean_str, parse_pagination
from ...extensions import db
from ...models import AuditLog
from ...permissions import constants as perms
from .._helpers import actor_and_scope

bp = Blueprint("audit", __name__, url_prefix="/api/audit-logs")


@bp.get("")
@require_permission(perms.AUDIT_VIEW)
def list_audit_logs():
    _actor, scope = actor_and_scope()
    page, page_size = parse_pagination(request.args)
    q = db.session.query(AuditLog)
    q = scope.filter_unit_column(q, AuditLog.unit_id)

    action = clean_str(request.args.get("action"))
    entity_type = clean_str(request.args.get("entity_type"))
    entity_id = clean_str(request.args.get("entity_id"))
    user_id = request.args.get("user_id")

    if action:
        q = q.filter(AuditLog.action == action)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    if user_id and str(user_id).isdigit():
        q = q.filter(AuditLog.user_id == int(user_id))

    total = q.count()
    rows = (
        q.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return paginated([r.to_dict() for r in rows], page, page_size, total)
