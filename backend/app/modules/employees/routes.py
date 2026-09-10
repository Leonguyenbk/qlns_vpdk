"""Route hồ sơ nhân sự, quá trình công tác và chuyển đơn vị."""
from __future__ import annotations

from datetime import date

from flask import Blueprint, request, send_file

from ...common.responses import paginated, success
from ...permissions import constants as perms
from ...common.auth_context import require_permission
from ...services import employee_service
from ...schemas import employee_create_schema, employee_update_schema, transfer_schema
from .._helpers import actor_and_scope, audit_meta, validated_json

bp = Blueprint("employees", __name__, url_prefix="/api/employees")


@bp.get("")
@require_permission(perms.EMPLOYEE_VIEW)
def list_employees():
    actor, scope = actor_and_scope()
    res = employee_service.list_employees(request.args, actor=actor, scope=scope)
    return paginated(res["items"], res["page"], res["page_size"], res["total"])


@bp.get("/dashboard")
@require_permission(perms.EMPLOYEE_VIEW)
def dashboard():
    actor, scope = actor_and_scope()
    return success(employee_service.dashboard(actor=actor, scope=scope))


@bp.get("/export")
@require_permission(perms.EMPLOYEE_VIEW)
def export_employees():
    actor, scope = actor_and_scope()
    buf = employee_service.export_employees(request.args, actor=actor, scope=scope)
    fname = f"Phu luc 4 - {date.today().strftime('%Y%m%d')}.xlsx"
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=fname,
    )


@bp.post("")
@require_permission(perms.EMPLOYEE_CREATE)
def create_employee():
    actor, scope = actor_and_scope()
    data = employee_service.create_employee(
        validated_json(employee_create_schema), actor=actor, scope=scope, meta=audit_meta()
    )
    return success(data, "Thêm nhân sự thành công", status_code=201)


@bp.get("/<int:employee_id>")
@require_permission(perms.EMPLOYEE_VIEW)
def get_employee(employee_id: int):
    actor, scope = actor_and_scope()
    include_deleted = str(request.args.get("include_deleted", "")).lower() in ("1", "true")
    return success(
        employee_service.get_employee(
            employee_id, actor=actor, scope=scope, include_deleted=include_deleted
        )
    )


@bp.put("/<int:employee_id>")
@require_permission(perms.EMPLOYEE_UPDATE)
def update_employee(employee_id: int):
    actor, scope = actor_and_scope()
    data = employee_service.update_employee(
        employee_id,
        validated_json(employee_update_schema),
        actor=actor,
        scope=scope,
        meta=audit_meta(),
    )
    return success(data, "Cập nhật nhân sự thành công")


@bp.delete("/<int:employee_id>")
@require_permission(perms.EMPLOYEE_DELETE)
def delete_employee(employee_id: int):
    actor, scope = actor_and_scope()
    data = employee_service.soft_delete_employee(
        employee_id, actor=actor, scope=scope, meta=audit_meta()
    )
    return success(data, "Đã xóa nhân sự (có thể khôi phục)")


@bp.post("/<int:employee_id>/restore")
@require_permission(perms.EMPLOYEE_RESTORE)
def restore_employee(employee_id: int):
    actor, scope = actor_and_scope()
    data = employee_service.restore_employee(
        employee_id, actor=actor, scope=scope, meta=audit_meta()
    )
    return success(data, "Khôi phục nhân sự thành công")


@bp.get("/<int:employee_id>/assignments")
@require_permission(perms.EMPLOYEE_VIEW)
def list_assignments(employee_id: int):
    actor, scope = actor_and_scope()
    return success(
        employee_service.list_assignments(employee_id, actor=actor, scope=scope)
    )


@bp.post("/<int:employee_id>/transfer")
@require_permission(perms.EMPLOYEE_TRANSFER)
def transfer_employee(employee_id: int):
    actor, scope = actor_and_scope()
    data = employee_service.transfer_employee(
        employee_id,
        validated_json(transfer_schema),
        actor=actor,
        scope=scope,
        meta=audit_meta(),
    )
    return success(data, "Chuyển đơn vị thành công")
