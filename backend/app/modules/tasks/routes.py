"""Route Giao việc – Theo dõi nhiệm vụ.

Toàn bộ kiểm tra quyền/quyền sở hữu/phạm vi đơn vị nằm ở tầng service
(``task_service``) — route chỉ đọc request và gọi service, đúng quy ước hiện
có (không chỉ ẩn nút trên giao diện).
"""
from __future__ import annotations

from flask import Blueprint, request, send_file

from ...common.responses import paginated, success
from ...common.auth_context import require_permission
from ...permissions import constants as perms
from ...services import task_service
from .._helpers import actor_and_scope, audit_meta, json_body

bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


@bp.get("")
def list_tasks():
    actor, scope = actor_and_scope()
    res = task_service.list_tasks(request.args, actor=actor, scope=scope)
    return paginated(res["items"], res["page"], res["page_size"], res["total"])


@bp.get("/dashboard")
@require_permission(perms.TASK_VIEW_ALL)
def dashboard():
    actor, scope = actor_and_scope()
    return success(task_service.executive_dashboard(actor=actor, scope=scope, args=request.args))


@bp.get("/workload/<int:user_id>")
@require_permission(perms.TASK_ASSIGN, perms.TASK_VIEW_ALL)
def workload(user_id: int):
    return success(task_service.workload_snapshot(user_id))


@bp.get("/assignable-people")
@require_permission(perms.TASK_CREATE, perms.TASK_ASSIGN)
def assignable_people():
    actor, scope = actor_and_scope()
    return success(task_service.list_assignable_people(request.args, actor=actor, scope=scope))


@bp.post("")
@require_permission(perms.TASK_CREATE)
def create_task():
    actor, scope = actor_and_scope()
    data = task_service.create_task(json_body(), actor=actor, scope=scope, meta=audit_meta())
    return success(data, "Tạo và giao nhiệm vụ thành công", status_code=201)


@bp.get("/<int:task_id>")
def get_task(task_id: int):
    actor, scope = actor_and_scope()
    return success(task_service.get_task(task_id, actor=actor, scope=scope))


@bp.put("/<int:task_id>/progress")
def update_progress(task_id: int):
    actor, scope = actor_and_scope()
    return success(task_service.update_progress(task_id, json_body(), actor=actor, scope=scope, meta=audit_meta()),
                   "Cập nhật tiến độ thành công")


@bp.post("/<int:task_id>/submit")
def submit_task(task_id: int):
    actor, _ = actor_and_scope()
    return success(task_service.submit_task(task_id, json_body(), actor=actor, meta=audit_meta()),
                   "Nộp kết quả thành công — đang chờ nghiệm thu")


@bp.post("/<int:task_id>/accept")
@require_permission(perms.TASK_ACCEPT)
def accept_task(task_id: int):
    actor, scope = actor_and_scope()
    return success(task_service.accept_task(task_id, json_body(), actor=actor, scope=scope, meta=audit_meta()),
                   "Nghiệm thu thành công")


@bp.post("/<int:task_id>/return")
@require_permission(perms.TASK_ACCEPT)
def return_for_revision(task_id: int):
    actor, scope = actor_and_scope()
    return success(task_service.return_for_revision(task_id, json_body(), actor=actor, scope=scope, meta=audit_meta()),
                   "Đã yêu cầu bổ sung/làm lại")


@bp.put("/<int:task_id>/deadline")
@require_permission(perms.TASK_MANAGE)
def extend_deadline(task_id: int):
    actor, scope = actor_and_scope()
    return success(task_service.extend_deadline(task_id, json_body(), actor=actor, scope=scope, meta=audit_meta()),
                   "Cập nhật hạn hoàn thành thành công")


@bp.put("/<int:task_id>/workload")
@require_permission(perms.TASK_MANAGE)
def adjust_workload(task_id: int):
    actor, scope = actor_and_scope()
    return success(task_service.adjust_workload(task_id, json_body(), actor=actor, scope=scope, meta=audit_meta()),
                   "Điều chỉnh khối lượng thành công")


@bp.post("/<int:task_id>/cancel")
@require_permission(perms.TASK_MANAGE)
def cancel_task(task_id: int):
    actor, scope = actor_and_scope()
    return success(task_service.cancel_task(task_id, json_body(), actor=actor, scope=scope, meta=audit_meta()),
                   "Đã hủy nhiệm vụ")


@bp.post("/<int:task_id>/comments")
def add_comment(task_id: int):
    actor, _ = actor_and_scope()
    return success(task_service.add_comment(task_id, json_body(), actor=actor, log_kind="COMMENT"),
                   "Đã thêm bình luận", status_code=201)


@bp.post("/<int:task_id>/work-logs")
def add_work_log(task_id: int):
    actor, _ = actor_and_scope()
    return success(task_service.add_comment(task_id, json_body(), actor=actor, log_kind="WORK_LOG"),
                   "Đã ghi nhật ký công việc", status_code=201)


@bp.post("/<int:task_id>/blockers")
def report_blocker(task_id: int):
    actor, _ = actor_and_scope()
    return success(task_service.report_blocker(task_id, json_body(), actor=actor),
                   "Đã báo cáo vướng mắc")


@bp.post("/<int:task_id>/pauses/<int:pause_id>/confirm")
@require_permission(perms.TASK_MANAGE)
def confirm_pause(task_id: int, pause_id: int):
    actor, scope = actor_and_scope()
    return success(task_service.confirm_pause(task_id, pause_id, actor=actor, scope=scope),
                   "Đã xác nhận thời gian tạm dừng")


@bp.post("/<int:task_id>/resume")
def resume_task(task_id: int):
    actor, scope = actor_and_scope()
    return success(task_service.resume_task(task_id, json_body(), actor=actor, scope=scope),
                   "Đã tiếp tục thực hiện nhiệm vụ")


@bp.post("/<int:task_id>/assignments")
@require_permission(perms.TASK_ASSIGN)
def add_assignment(task_id: int):
    actor, scope = actor_and_scope()
    return success(task_service.add_assignment(task_id, json_body(), actor=actor, scope=scope, meta=audit_meta()),
                   "Đã phân công thêm người thực hiện", status_code=201)


@bp.delete("/<int:task_id>/assignments/<int:assignment_id>")
@require_permission(perms.TASK_ASSIGN)
def remove_assignment(task_id: int, assignment_id: int):
    actor, scope = actor_and_scope()
    return success(
        task_service.remove_assignment(task_id, assignment_id, json_body(), actor=actor, scope=scope, meta=audit_meta()),
        "Đã gỡ người thực hiện khỏi nhiệm vụ",
    )


@bp.post("/<int:task_id>/attachments")
def upload_attachment(task_id: int):
    actor, _ = actor_and_scope()
    file_storage = request.files.get("file")
    kind = request.form.get("kind", "EVIDENCE")
    data = task_service.add_attachment(task_id, file_storage, kind=kind, actor=actor)
    return success(data, "Tải tệp lên thành công", status_code=201)


@bp.get("/<int:task_id>/attachments/<int:attachment_id>/download")
def download_attachment(task_id: int, attachment_id: int):
    actor, scope = actor_and_scope()
    attachment = task_service.get_attachment(task_id, attachment_id, actor=actor, scope=scope)
    return send_file(attachment.stored_path, as_attachment=True, download_name=attachment.file_name)
