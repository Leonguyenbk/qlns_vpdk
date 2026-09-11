"""Nghiệp vụ Giao việc – Theo dõi nhiệm vụ.

Quy tắc quan trọng được thực thi ở đây (không chỉ ở giao diện):
- Người thực hiện cập nhật tiến độ 100% chỉ có thể chuyển sang "Chờ nghiệm
  thu" — CHỈ người có quyền ``task.accept`` mới đặt được "Hoàn thành".
- "Quá hạn" không lưu — luôn tính lại từ ``Task.is_overdue()``.
- Mọi thao tác ghi log/audit trước khi thay đổi trạng thái, trong cùng
  transaction (không tự commit — route/service gọi ngoài cùng chịu trách
  nhiệm transaction theo đúng quy ước hiện có của codebase).
- Snapshot đơn vị/chức vụ tại thời điểm giao việc — không suy ra từ hồ sơ
  nhân sự hiện tại.
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta

from flask import current_app
from sqlalchemy import func, or_
from werkzeug.utils import secure_filename

from ..common.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from ..common.utils import clean_str, parse_date, parse_pagination, utcnow
from ..extensions import db
from ..models import (
    OrganizationUnit,
    Task,
    TaskAssignment,
    TaskAttachment,
    TaskLog,
    TaskPause,
    User,
)
from ..models.enums import (
    TASK_ASSIGNMENT_ROLES,
    TASK_ATTACHMENT_KINDS,
    TASK_DEADLINE_TYPES,
    TASK_PAUSE_REASONS,
    TASK_PRIORITIES,
    TASK_SOURCES,
    TASK_STATUSES,
    TASK_TERMINAL_STATUSES,
)
from ..permissions import constants as perms
from .audit_service import record_audit
from .snapshot_utils import current_position_snapshot as _current_snapshot

_ACTIVE_STATUSES = tuple(s for s in TASK_STATUSES if s not in TASK_TERMINAL_STATUSES)


# ------------------------------- helpers -------------------------------


def _is_participant(task: Task, user_id: int) -> bool:
    return any(a.user_id == user_id for a in task.active_assignments())


def _is_lead(task: Task, user_id: int) -> bool:
    return any(a.user_id == user_id and a.role_in_task == "LEAD" for a in task.active_assignments())


def _check_version(task: Task, expected_version: int | None) -> None:
    if expected_version is not None and expected_version != task.version:
        raise ConflictError(
            "Nhiệm vụ đã bị thay đổi bởi người khác — vui lòng tải lại trước khi tiếp tục.",
            payload={"conflict": "TASK_VERSION_MISMATCH", "current_version": task.version},
        )


def _bump(task: Task) -> None:
    task.version += 1


def _scope_filter(query, scope, *, unit_col):
    if scope.is_global:
        return query
    if not scope.unit_ids:
        return query.filter(db.false())
    return query.filter(unit_col.in_(scope.unit_ids))


def _get_task(task_id: int) -> Task:
    task = db.session.get(Task, task_id)
    if task is None:
        raise NotFoundError("Không tìm thấy nhiệm vụ.")
    return task


def _in_scope(task: Task, scope) -> bool:
    if scope.is_global:
        return True
    return scope.allows_unit(task.assigning_unit_id) or scope.allows_unit(task.executing_unit_id)


def _assert_visible(task: Task, *, actor: User, scope) -> None:
    codes = actor.permission_codes()
    if perms.TASK_VIEW_ALL in codes:
        if not _in_scope(task, scope):
            raise PermissionDeniedError("Nhiệm vụ nằm ngoài phạm vi đơn vị được phân quyền.")
        return
    if perms.TASK_VIEW_OWN in codes and (
        _is_participant(task, actor.id) or task.creator_id == actor.id or task.assigner_id == actor.id
    ):
        return
    raise PermissionDeniedError("Bạn không có quyền xem nhiệm vụ này.")


def _assert_managed(task: Task, *, actor: User, scope, required: tuple[str, ...]) -> None:
    """Kiểm tra quyền quản lý nhiệm vụ (nghiệm thu/gia hạn/hủy/phân công...) —
    bắt buộc có MỘT trong các quyền yêu cầu VÀ nhiệm vụ nằm trong phạm vi đơn
    vị được phân quyền (không chỉ kiểm tra permission code một cách tách rời
    khỏi phạm vi tổ chức)."""
    codes = actor.permission_codes()
    if not any(p in codes for p in required):
        raise PermissionDeniedError("Bạn không có quyền thực hiện thao tác này trên nhiệm vụ.")
    if not _in_scope(task, scope):
        raise PermissionDeniedError("Nhiệm vụ nằm ngoài phạm vi đơn vị được phân quyền.")


def generate_task_code() -> str:
    year = date.today().year
    prefix = f"NV-{year}-"
    count = db.session.query(func.count(Task.id)).filter(Task.code.like(f"{prefix}%")).scalar() or 0
    return f"{prefix}{count + 1:06d}"


# ------------------------------- CRUD -------------------------------

def create_task(data: dict, *, actor: User, scope, meta: dict) -> dict:
    name = clean_str(data.get("name"))
    if not name:
        raise ValidationError("Tên nhiệm vụ là bắt buộc.")
    assigning_unit_id = data.get("assigning_unit_id")
    if not assigning_unit_id:
        raise ValidationError("Đơn vị giao việc là bắt buộc.")
    unit = db.session.get(OrganizationUnit, assigning_unit_id)
    if unit is None:
        raise ValidationError("Đơn vị giao việc không tồn tại.")
    if not scope.allows_unit(assigning_unit_id):
        raise PermissionDeniedError("Bạn không có quyền giao việc từ đơn vị này.")

    source = clean_str(data.get("source")) or "AD_HOC"
    if source not in TASK_SOURCES:
        raise ValidationError(f"Nguồn nhiệm vụ phải thuộc: {', '.join(sorted(TASK_SOURCES))}.")
    priority = clean_str(data.get("priority")) or "NORMAL"
    if priority not in TASK_PRIORITIES:
        raise ValidationError(f"Mức ưu tiên phải thuộc: {', '.join(sorted(TASK_PRIORITIES))}.")
    deadline_type = clean_str(data.get("deadline_type")) or "INTERNAL"
    if deadline_type not in TASK_DEADLINE_TYPES:
        raise ValidationError(f"Loại hạn phải thuộc: {', '.join(sorted(TASK_DEADLINE_TYPES))}.")

    parent_id = data.get("parent_task_id")
    if parent_id:
        parent = db.session.get(Task, parent_id)
        if parent is None:
            raise ValidationError("Nhiệm vụ cha không tồn tại.")

    assignees = data.get("assignees") or []
    if not assignees:
        raise ValidationError("Phải chọn ít nhất một người thực hiện (chủ trì).")
    if not any(a.get("role_in_task", "LEAD") == "LEAD" for a in assignees):
        assignees[0]["role_in_task"] = "LEAD"

    contribs = [a.get("contribution_percent") for a in assignees if a.get("role_in_task") in ("LEAD", "COLLABORATOR")]
    contribs = [c for c in contribs if c is not None]
    if contribs and abs(sum(contribs) - 100) > 0.01:
        raise BusinessRuleError(
            "Tổng % đóng góp của những người cùng làm một sản phẩm phải bằng 100%."
        )

    task = Task(
        code=data.get("code") or generate_task_code(),
        name=name,
        description=clean_str(data.get("description")),
        business_group_code=clean_str(data.get("business_group_code")),
        product_id=data.get("product_id"),
        source=source,
        creator_id=actor.id,
        assigner_id=data.get("assigner_id") or actor.id,
        assigning_unit_id=assigning_unit_id,
        executing_unit_id=data.get("executing_unit_id"),
        parent_task_id=parent_id,
        has_own_product=data.get("has_own_product", True),
        priority=priority,
        status="ASSIGNED" if assignees else "DRAFT",
        assigned_date=parse_date(data.get("assigned_date"), "assigned_date") or date.today(),
        start_date=parse_date(data.get("start_date"), "start_date"),
        original_deadline=parse_date(data.get("original_deadline"), "original_deadline"),
        deadline_type=deadline_type,
        assigned_workload=data.get("assigned_workload"),
        workload_unit=clean_str(data.get("workload_unit")),
        output_description=clean_str(data.get("output_description")),
        quality_standard=clean_str(data.get("quality_standard")),
        acceptance_conditions=clean_str(data.get("acceptance_conditions")),
        complexity_level=clean_str(data.get("complexity_level")),
        created_by=actor.id,
    )
    db.session.add(task)
    db.session.flush()

    for a in assignees:
        _add_assignment(task, user_id=a["user_id"], role_in_task=a.get("role_in_task", "COLLABORATOR"),
                         contribution_percent=a.get("contribution_percent"), actor=actor)

    db.session.add(TaskLog(
        task_id=task.id, user_id=actor.id, log_kind="STATUS_CHANGE",
        content="Tạo và giao nhiệm vụ",
        meta={"to_status": task.status},
    ))
    record_audit(
        user_id=actor.id, action="task.create", entity_type="task", entity_id=task.id,
        unit_id=assigning_unit_id, new_values={"code": task.code, "name": task.name}, **meta,
    )
    db.session.commit()
    return get_task(task.id, actor=actor, scope=scope)


def _add_assignment(task: Task, *, user_id: int, role_in_task: str, contribution_percent, actor: User) -> TaskAssignment:
    if role_in_task not in TASK_ASSIGNMENT_ROLES:
        raise ValidationError(f"Vai trò trong nhiệm vụ phải thuộc: {', '.join(sorted(TASK_ASSIGNMENT_ROLES))}.")
    user = db.session.get(User, user_id)
    if user is None:
        raise ValidationError("Người được giao việc không tồn tại.")
    snap = _current_snapshot(user)
    assignment = TaskAssignment(
        task_id=task.id, user_id=user_id, role_in_task=role_in_task,
        contribution_percent=contribution_percent,
        unit_id_snapshot=snap["unit_id"], position_id_snapshot=snap["position_id"],
        position_name_snapshot=snap["position_name"], is_managerial_snapshot=snap["is_managerial"],
        assigned_at=utcnow(), assigned_by=actor.id,
    )
    db.session.add(assignment)
    db.session.flush()
    return assignment


def list_tasks(args, *, actor: User, scope) -> dict:
    page, page_size = parse_pagination(args, default_size=20, max_size=200)
    q = db.session.query(Task)

    codes = actor.permission_codes()
    if perms.TASK_VIEW_ALL not in codes:
        if perms.TASK_VIEW_OWN not in codes:
            raise PermissionDeniedError("Bạn không có quyền xem danh sách nhiệm vụ.")
        # Chỉ thấy nhiệm vụ mình tham gia/tạo/giao — dùng cho "Công việc của tôi"
        q = q.outerjoin(TaskAssignment, TaskAssignment.task_id == Task.id).filter(
            or_(
                TaskAssignment.user_id == actor.id,
                Task.creator_id == actor.id,
                Task.assigner_id == actor.id,
            )
        )
    elif not scope.is_global:
        if not scope.unit_ids:
            q = q.filter(db.false())
        else:
            q = q.filter(
                or_(Task.assigning_unit_id.in_(scope.unit_ids), Task.executing_unit_id.in_(scope.unit_ids))
            )

    unit_id = args.get("unit_id")
    if unit_id:
        q = q.filter(or_(Task.assigning_unit_id == unit_id, Task.executing_unit_id == unit_id))
    person_id = args.get("person_id")
    if person_id:
        q = q.join(TaskAssignment, TaskAssignment.task_id == Task.id).filter(TaskAssignment.user_id == person_id)
    assigner_id = args.get("assigner_id")
    if assigner_id:
        q = q.filter(Task.assigner_id == assigner_id)
    business_group = args.get("business_group_code")
    if business_group:
        q = q.filter(Task.business_group_code == business_group)
    status = args.get("status")
    if status:
        q = q.filter(Task.status == status)
    priority = args.get("priority")
    if priority:
        q = q.filter(Task.priority == priority)
    date_from = parse_date(args.get("date_from"), "date_from")
    if date_from:
        q = q.filter(Task.assigned_date >= date_from)
    date_to = parse_date(args.get("date_to"), "date_to")
    if date_to:
        q = q.filter(Task.assigned_date <= date_to)
    search = clean_str(args.get("search"))
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Task.name.ilike(like), Task.code.ilike(like)))

    overdue_only = str(args.get("overdue", "")).lower() in ("1", "true")
    due_soon_only = str(args.get("due_soon", "")).lower() in ("1", "true")
    today = date.today()
    if overdue_only:
        q = q.filter(
            Task.status.notin_(TASK_TERMINAL_STATUSES),
            func.coalesce(Task.extended_deadline, Task.original_deadline) < today,
        )
    if due_soon_only:
        soon = today + timedelta(days=3)
        q = q.filter(
            Task.status.notin_(TASK_TERMINAL_STATUSES),
            func.coalesce(Task.extended_deadline, Task.original_deadline).between(today, soon),
        )

    total = q.distinct().count()
    items = (
        q.distinct().order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    )
    return {
        "items": [t.to_dict(include_relations=False) for t in items],
        "page": page, "page_size": page_size, "total": total,
    }


def get_task(task_id: int, *, actor: User, scope) -> dict:
    task = _get_task(task_id)
    _assert_visible(task, actor=actor, scope=scope)
    data = task.to_dict(include_relations=True)
    data["logs"] = [l.to_dict() for l in task.logs]
    data["pauses"] = [p.to_dict() for p in task.pauses]
    data["attachments"] = [a.to_dict() for a in task.attachments]
    data["children"] = [c.to_dict(include_relations=False) for c in task.children]
    return data


# ------------------------------- workflow -------------------------------

def update_progress(task_id: int, data: dict, *, actor: User, scope, meta: dict) -> dict:
    task = _get_task(task_id)
    if not _is_participant(task, actor.id):
        _assert_managed(task, actor=actor, scope=scope, required=(perms.TASK_MANAGE,))
    if task.status in TASK_TERMINAL_STATUSES:
        raise BusinessRuleError("Nhiệm vụ đã kết thúc, không thể cập nhật tiến độ.")
    _check_version(task, data.get("expected_version"))

    percent = data.get("progress_percent")
    if percent is not None:
        percent = int(percent)
        if not (0 <= percent <= 100):
            raise ValidationError("Tiến độ phải trong khoảng 0-100.")
        task.progress_percent = percent
    if "result_summary" in data:
        task.result_summary = clean_str(data.get("result_summary"))

    old_status = task.status
    # Chỉ được chuyển sang "Chờ nghiệm thu" — KHÔNG được tự đặt "Hoàn thành".
    if task.progress_percent >= 100 and task.status not in ("PENDING_ACCEPTANCE", "COMPLETED"):
        task.status = "PENDING_ACCEPTANCE"
        task.submitted_at = utcnow()
    elif task.progress_percent > 0 and task.status == "ASSIGNED":
        task.status = "IN_PROGRESS"
        task.start_date = task.start_date or date.today()

    _bump(task)
    db.session.add(TaskLog(
        task_id=task.id, user_id=actor.id, log_kind="WORK_LOG",
        content=data.get("note") or f"Cập nhật tiến độ {task.progress_percent}%",
        meta={"progress_percent": task.progress_percent, "from_status": old_status, "to_status": task.status},
    ))
    if old_status != task.status:
        record_audit(
            user_id=actor.id, action="task.status_change", entity_type="task", entity_id=task.id,
            old_values={"status": old_status}, new_values={"status": task.status}, **meta,
        )
    db.session.commit()
    return get_task(task.id, actor=actor, scope=_AllScope())


def submit_task(task_id: int, data: dict, *, actor: User, meta: dict) -> dict:
    """Nộp kết quả — luôn chuyển sang "Chờ nghiệm thu", KHÔNG BAO GIỜ tự đặt
    "Hoàn thành" (chỉ người có quyền ``task.accept`` mới nghiệm thu được)."""
    task = _get_task(task_id)
    if not _is_participant(task, actor.id):
        raise PermissionDeniedError("Chỉ người thực hiện nhiệm vụ mới được nộp kết quả.")
    if task.status in TASK_TERMINAL_STATUSES:
        raise BusinessRuleError("Nhiệm vụ đã kết thúc.")
    _check_version(task, data.get("expected_version"))
    result_summary = clean_str(data.get("result_summary"))
    if not result_summary:
        raise ValidationError("Phải nhập tóm tắt kết quả khi nộp.")
    old_status = task.status
    task.result_summary = result_summary
    task.progress_percent = 100
    task.status = "PENDING_ACCEPTANCE"
    task.submitted_at = utcnow()
    _bump(task)
    db.session.add(TaskLog(
        task_id=task.id, user_id=actor.id, log_kind="SUBMISSION", content=result_summary,
        meta={"from_status": old_status, "to_status": "PENDING_ACCEPTANCE"},
    ))
    record_audit(
        user_id=actor.id, action="task.submit", entity_type="task", entity_id=task.id,
        old_values={"status": old_status}, new_values={"status": "PENDING_ACCEPTANCE"}, **meta,
    )
    db.session.commit()
    return get_task(task.id, actor=actor, scope=_AllScope())


def _upload_dir(task_id: int) -> str:
    base = os.path.join(current_app.instance_path, "task_attachments", str(task_id))
    os.makedirs(base, exist_ok=True)
    return base


def add_attachment(task_id: int, file_storage, *, kind: str, actor: User) -> dict:
    task = _get_task(task_id)
    codes = actor.permission_codes()
    if not _is_participant(task, actor.id) and perms.TASK_MANAGE not in codes and perms.TASK_ACCEPT not in codes:
        raise PermissionDeniedError("Bạn không có quyền đính kèm minh chứng cho nhiệm vụ này.")
    kind = kind or "EVIDENCE"
    if kind not in TASK_ATTACHMENT_KINDS:
        raise ValidationError(f"Loại tệp đính kèm phải thuộc: {', '.join(sorted(TASK_ATTACHMENT_KINDS))}.")
    if not file_storage or not file_storage.filename:
        raise ValidationError("Chưa chọn tệp để tải lên.")
    filename = secure_filename(file_storage.filename) or "tep"
    stored_name = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(_upload_dir(task_id), stored_name)
    file_storage.save(path)
    size = os.path.getsize(path)
    attachment = TaskAttachment(
        task_id=task_id, uploaded_by=actor.id, kind=kind, file_name=filename,
        stored_path=path, file_size=size, content_type=file_storage.content_type,
    )
    db.session.add(attachment)
    db.session.add(TaskLog(
        task_id=task_id, user_id=actor.id, log_kind="COMMENT",
        content=f"Đính kèm tệp: {filename}", meta={"attachment_kind": kind},
    ))
    db.session.commit()
    return attachment.to_dict()


def get_attachment(task_id: int, attachment_id: int, *, actor: User, scope) -> TaskAttachment:
    task = _get_task(task_id)
    _assert_visible(task, actor=actor, scope=scope)
    attachment = db.session.get(TaskAttachment, attachment_id)
    if attachment is None or attachment.task_id != task_id:
        raise NotFoundError("Không tìm thấy tệp đính kèm.")
    return attachment


class _AllScope:
    """Scope giả dùng nội bộ khi service tự đọc lại dữ liệu vừa ghi (đã kiểm
    tra quyền ở đầu hàm public), tránh phải truyền scope qua nhiều lớp gọi."""
    is_global = True
    unit_ids: set[int] = set()

    def allows_unit(self, unit_id):
        return True


def accept_task(task_id: int, data: dict, *, actor: User, scope, meta: dict) -> dict:
    task = _get_task(task_id)
    _assert_managed(task, actor=actor, scope=scope, required=(perms.TASK_ACCEPT,))
    if task.status not in ("PENDING_ACCEPTANCE",):
        raise BusinessRuleError("Chỉ nghiệm thu được nhiệm vụ đang ở trạng thái Chờ nghiệm thu.")
    _check_version(task, data.get("expected_version"))
    if _is_lead(task, actor.id):
        raise BusinessRuleError("Người chủ trì thực hiện không được tự nghiệm thu nhiệm vụ của mình.")

    quality_level = data.get("quality_level")
    if quality_level is not None:
        quality_level = int(quality_level)
        if not (1 <= quality_level <= 5):
            raise ValidationError("Đánh giá chất lượng phải theo thang 1-5.")
        task.quality_level = quality_level
    task.error_severity = clean_str(data.get("error_severity"))
    task.status = "COMPLETED"
    task.progress_percent = 100
    task.accepted_at = utcnow()
    task.accepted_by = actor.id
    if data.get("result_summary"):
        task.result_summary = clean_str(data.get("result_summary"))
    _bump(task)

    db.session.add(TaskLog(
        task_id=task.id, user_id=actor.id, log_kind="STATUS_CHANGE",
        content=data.get("note") or "Nghiệm thu — Hoàn thành",
        meta={"quality_level": task.quality_level, "to_status": "COMPLETED"},
    ))
    record_audit(
        user_id=actor.id, action="task.accept", entity_type="task", entity_id=task.id,
        new_values={"status": "COMPLETED", "quality_level": task.quality_level}, **meta,
    )
    db.session.commit()
    return get_task(task.id, actor=actor, scope=_AllScope())


def return_for_revision(task_id: int, data: dict, *, actor: User, scope, meta: dict) -> dict:
    task = _get_task(task_id)
    _assert_managed(task, actor=actor, scope=scope, required=(perms.TASK_ACCEPT,))
    if task.status not in ("PENDING_ACCEPTANCE",):
        raise BusinessRuleError("Chỉ trả lại được nhiệm vụ đang Chờ nghiệm thu.")
    reason = clean_str(data.get("reason"))
    if not reason:
        raise ValidationError("Phải nêu lý do yêu cầu bổ sung/làm lại.")
    task.status = "NEEDS_REVISION"
    task.rework_count += 1
    task.progress_percent = min(task.progress_percent, 90)
    _bump(task)
    db.session.add(TaskLog(
        task_id=task.id, user_id=actor.id, log_kind="RETURN_FOR_REVISION",
        content=reason, meta={"rework_count": task.rework_count},
    ))
    record_audit(
        user_id=actor.id, action="task.return_for_revision", entity_type="task", entity_id=task.id,
        new_values={"status": "NEEDS_REVISION"}, **meta,
    )
    db.session.commit()
    return get_task(task.id, actor=actor, scope=_AllScope())


def extend_deadline(task_id: int, data: dict, *, actor: User, scope, meta: dict) -> dict:
    task = _get_task(task_id)
    _assert_managed(task, actor=actor, scope=scope, required=(perms.TASK_MANAGE,))
    new_deadline = parse_date(data.get("new_deadline"), "new_deadline")
    if not new_deadline:
        raise ValidationError("Phải nhập hạn hoàn thành mới.")
    reason = clean_str(data.get("reason"))
    if not reason:
        raise ValidationError("Phải nêu lý do gia hạn.")
    old = task.extended_deadline or task.original_deadline
    task.extended_deadline = new_deadline
    _bump(task)
    db.session.add(TaskLog(
        task_id=task.id, user_id=actor.id, log_kind="EXTENSION_REQUEST",
        content=reason, meta={"old_deadline": old.isoformat() if old else None, "new_deadline": new_deadline.isoformat()},
    ))
    record_audit(
        user_id=actor.id, action="task.extend_deadline", entity_type="task", entity_id=task.id,
        old_values={"deadline": old.isoformat() if old else None},
        new_values={"deadline": new_deadline.isoformat()}, **meta,
    )
    db.session.commit()
    return get_task(task.id, actor=actor, scope=_AllScope())


def adjust_workload(task_id: int, data: dict, *, actor: User, scope, meta: dict) -> dict:
    task = _get_task(task_id)
    _assert_managed(task, actor=actor, scope=scope, required=(perms.TASK_MANAGE,))
    reason = clean_str(data.get("reason"))
    if not reason:
        raise ValidationError("Phải nêu lý do điều chỉnh khối lượng.")
    old = float(task.assigned_workload) if task.assigned_workload is not None else None
    task.assigned_workload = data.get("assigned_workload")
    if "workload_unit" in data:
        task.workload_unit = clean_str(data.get("workload_unit"))
    _bump(task)
    db.session.add(TaskLog(
        task_id=task.id, user_id=actor.id, log_kind="WORKLOAD_ADJUST",
        content=reason, meta={"old_workload": old, "new_workload": data.get("assigned_workload")},
    ))
    record_audit(
        user_id=actor.id, action="task.adjust_workload", entity_type="task", entity_id=task.id,
        old_values={"assigned_workload": old},
        new_values={"assigned_workload": data.get("assigned_workload")}, **meta,
    )
    db.session.commit()
    return get_task(task.id, actor=actor, scope=_AllScope())


def cancel_task(task_id: int, data: dict, *, actor: User, scope, meta: dict) -> dict:
    task = _get_task(task_id)
    _assert_managed(task, actor=actor, scope=scope, required=(perms.TASK_MANAGE,))
    if task.status in TASK_TERMINAL_STATUSES:
        raise BusinessRuleError("Nhiệm vụ đã kết thúc.")
    reason = clean_str(data.get("reason"))
    if not reason:
        raise ValidationError("Phải nêu lý do hủy nhiệm vụ.")
    task.status = "CANCELLED"
    task.cancel_reason = reason
    task.cancelled_by = actor.id
    task.cancelled_at = utcnow()
    _bump(task)
    db.session.add(TaskLog(task_id=task.id, user_id=actor.id, log_kind="CANCEL", content=reason))
    record_audit(
        user_id=actor.id, action="task.cancel", entity_type="task", entity_id=task.id,
        new_values={"status": "CANCELLED", "reason": reason}, **meta,
    )
    db.session.commit()
    return get_task(task.id, actor=actor, scope=_AllScope())


def add_comment(task_id: int, data: dict, *, actor: User, log_kind: str = "COMMENT") -> dict:
    task = _get_task(task_id)
    if not _is_participant(task, actor.id) and perms.TASK_VIEW_ALL not in actor.permission_codes() \
            and task.creator_id != actor.id and task.assigner_id != actor.id:
        raise PermissionDeniedError("Bạn không có quyền bình luận trên nhiệm vụ này.")
    content = clean_str(data.get("content"))
    if not content:
        raise ValidationError("Nội dung không được để trống.")
    log = TaskLog(task_id=task.id, user_id=actor.id, log_kind=log_kind, content=content, meta=data.get("meta"))
    db.session.add(log)
    db.session.commit()
    return log.to_dict()


def report_blocker(task_id: int, data: dict, *, actor: User) -> dict:
    task = _get_task(task_id)
    if not _is_participant(task, actor.id):
        raise PermissionDeniedError("Chỉ người thực hiện mới được báo cáo vướng mắc.")
    reason_code = clean_str(data.get("reason_code"))
    if reason_code not in TASK_PAUSE_REASONS:
        raise ValidationError(f"Lý do phải thuộc: {', '.join(sorted(TASK_PAUSE_REASONS))}.")
    note = clean_str(data.get("note"))
    task.is_blocked = True
    task.blocker_reason = note or reason_code
    if task.status in ("ASSIGNED", "IN_PROGRESS"):
        task.status = "PENDING_COLLAB" if reason_code == "WAITING_AGENCY" else "PAUSED"
    _bump(task)
    pause = TaskPause(
        task_id=task.id, reason_code=reason_code, started_at=utcnow(),
        evidence_ref=clean_str(data.get("evidence_ref")), note=note, created_by=actor.id,
    )
    db.session.add(pause)
    db.session.add(TaskLog(
        task_id=task.id, user_id=actor.id, log_kind="BLOCKER_REPORT", content=note,
        meta={"reason_code": reason_code},
    ))
    db.session.commit()
    return get_task(task.id, actor=actor, scope=_AllScope())


def confirm_pause(task_id: int, pause_id: int, *, actor: User, scope) -> dict:
    task = _get_task(task_id)
    _assert_managed(task, actor=actor, scope=scope, required=(perms.TASK_MANAGE,))
    pause = db.session.get(TaskPause, pause_id)
    if pause is None or pause.task_id != task_id:
        raise NotFoundError("Không tìm thấy bản ghi tạm dừng.")
    pause.confirmed_by = actor.id
    pause.confirmed_at = utcnow()
    db.session.commit()
    return pause.to_dict()


def resume_task(task_id: int, data: dict, *, actor: User, scope) -> dict:
    task = _get_task(task_id)
    if not _is_participant(task, actor.id):
        _assert_managed(task, actor=actor, scope=scope, required=(perms.TASK_MANAGE,))
    open_pause = next((p for p in sorted(task.pauses, key=lambda x: x.started_at, reverse=True) if p.ended_at is None), None)
    if open_pause:
        open_pause.ended_at = utcnow()
    task.is_blocked = False
    task.status = "IN_PROGRESS"
    _bump(task)
    db.session.add(TaskLog(task_id=task.id, user_id=actor.id, log_kind="STATUS_CHANGE",
                            content=clean_str(data.get("note")) or "Tiếp tục thực hiện",
                            meta={"to_status": "IN_PROGRESS"}))
    db.session.commit()
    return get_task(task.id, actor=actor, scope=_AllScope())


def add_assignment(task_id: int, data: dict, *, actor: User, scope, meta: dict) -> dict:
    task = _get_task(task_id)
    _assert_managed(task, actor=actor, scope=scope, required=(perms.TASK_ASSIGN,))
    assignment = _add_assignment(
        task, user_id=data["user_id"], role_in_task=data.get("role_in_task", "COLLABORATOR"),
        contribution_percent=data.get("contribution_percent"), actor=actor,
    )
    db.session.add(TaskLog(
        task_id=task.id, user_id=actor.id, log_kind="REASSIGN",
        content=f"Thêm người thực hiện: {assignment.user.full_name if assignment.user else assignment.user_id}",
        meta={"user_id": assignment.user_id, "role_in_task": assignment.role_in_task},
    ))
    record_audit(
        user_id=actor.id, action="task.add_assignment", entity_type="task", entity_id=task.id,
        new_values={"user_id": assignment.user_id, "role_in_task": assignment.role_in_task}, **meta,
    )
    db.session.commit()
    return get_task(task.id, actor=actor, scope=_AllScope())


def remove_assignment(task_id: int, assignment_id: int, data: dict, *, actor: User, scope, meta: dict) -> dict:
    task = _get_task(task_id)
    _assert_managed(task, actor=actor, scope=scope, required=(perms.TASK_ASSIGN,))
    assignment = db.session.get(TaskAssignment, assignment_id)
    if assignment is None or assignment.task_id != task_id:
        raise NotFoundError("Không tìm thấy phân công.")
    reason = clean_str(data.get("reason"))
    assignment.removed_at = utcnow()
    assignment.removed_reason = reason
    db.session.add(TaskLog(
        task_id=task.id, user_id=actor.id, log_kind="REASSIGN",
        content=f"Gỡ người thực hiện khỏi nhiệm vụ: {reason or ''}".strip(),
        meta={"user_id": assignment.user_id},
    ))
    record_audit(
        user_id=actor.id, action="task.remove_assignment", entity_type="task", entity_id=task.id,
        old_values={"user_id": assignment.user_id}, **meta,
    )
    db.session.commit()
    return get_task(task.id, actor=actor, scope=_AllScope())


# ------------------------------- tổng hợp -------------------------------

def list_assignable_people(args, *, actor: User, scope) -> list[dict]:
    """Danh sách tài khoản có hồ sơ nhân sự để chọn khi giao việc — tách khỏi
    ``/api/users`` (yêu cầu ``user.view``) vì người được giao quyền giao việc
    không nhất thiết có quyền quản trị tài khoản."""
    q = db.session.query(User).filter(User.employee_id.isnot(None), User.is_active.is_(True))
    search = clean_str(args.get("search"))
    if search:
        q = q.filter(User.full_name.ilike(f"%{search}%"))
    rows = q.order_by(User.full_name).limit(500).all()

    unit_id = args.get("unit_id")
    out = []
    for u in rows:
        emp = u.employee
        current = emp.primary_active_assignment() if emp else None
        cur_unit_id = current.unit_id if current else None
        if not scope.allows_unit(cur_unit_id) and cur_unit_id is not None:
            continue
        if unit_id and str(cur_unit_id) != str(unit_id):
            continue
        out.append({
            "user_id": u.id,
            "full_name": u.full_name,
            "unit_id": cur_unit_id,
            "unit_name": current.unit.name if current and current.unit else None,
            "position_id": current.position_id if current else None,
            "position_name": current.position.name if current and current.position else None,
            "is_managerial": bool(current.position.is_managerial) if current and current.position else False,
        })
    return out


def workload_snapshot(user_id: int) -> dict:
    """Khối lượng hiện tại của một người — dùng khi giao việc để tránh dồn
    việc, hiển thị CÓ CĂN CỨ (số nhiệm vụ + tổng khối lượng quy đổi), không
    xếp hạng so sánh giữa các vị trí việc làm khác nhau."""
    rows = (
        db.session.query(Task)
        .join(TaskAssignment, TaskAssignment.task_id == Task.id)
        .filter(
            TaskAssignment.user_id == user_id,
            TaskAssignment.removed_at.is_(None),
            Task.status.notin_(TASK_TERMINAL_STATUSES),
        )
        .all()
    )
    total_workload = sum(float(t.assigned_workload or 0) for t in rows)
    overdue = sum(1 for t in rows if t.is_overdue())
    return {
        "active_task_count": len(rows),
        "overdue_count": overdue,
        "total_assigned_workload": round(total_workload, 2),
        "basis": "Tổng khối lượng giao (assigned_workload) của các nhiệm vụ đang hoạt động, "
                 "chưa quy đổi Kn (quy đổi chỉ áp dụng khi tính KPI theo kỳ).",
    }


def executive_dashboard(*, actor: User, scope, args) -> dict:
    q = db.session.query(Task)
    if not scope.is_global:
        if not scope.unit_ids:
            q = q.filter(db.false())
        else:
            q = q.filter(or_(Task.assigning_unit_id.in_(scope.unit_ids), Task.executing_unit_id.in_(scope.unit_ids)))
    unit_id = args.get("unit_id")
    if unit_id:
        q = q.filter(or_(Task.assigning_unit_id == unit_id, Task.executing_unit_id == unit_id))

    tasks = q.all()
    today = date.today()
    soon = today + timedelta(days=3)

    def _deadline(t):
        return t.extended_deadline or t.original_deadline

    stats = {
        "total": len(tasks),
        "not_started": sum(1 for t in tasks if t.status in ("DRAFT", "ASSIGNED")),
        "in_progress": sum(1 for t in tasks if t.status == "IN_PROGRESS"),
        "due_soon": sum(1 for t in tasks if t.status not in TASK_TERMINAL_STATUSES and _deadline(t) and today <= _deadline(t) <= soon),
        "overdue": sum(1 for t in tasks if t.is_overdue()),
        "pending_collab": sum(1 for t in tasks if t.status == "PENDING_COLLAB"),
        "pending_acceptance": sum(1 for t in tasks if t.status == "PENDING_ACCEPTANCE"),
        "completed": sum(1 for t in tasks if t.status == "COMPLETED"),
        "cancelled": sum(1 for t in tasks if t.status == "CANCELLED"),
        "needs_revision": sum(1 for t in tasks if t.status == "NEEDS_REVISION"),
    }
    completed = [t for t in tasks if t.status == "COMPLETED"]
    on_time = [t for t in completed if t.submitted_at and _deadline(t) and t.submitted_at.date() <= _deadline(t)]
    stats["on_time_rate"] = round(len(on_time) / len(completed) * 100, 1) if completed else None
    assigned_total = sum(float(t.assigned_workload or 0) for t in tasks)
    accepted_total = sum(float(t.assigned_workload or 0) for t in completed)
    stats["assigned_workload_total"] = round(assigned_total, 2)
    stats["accepted_workload_total"] = round(accepted_total, 2)

    # Bảng theo người
    by_person: dict[int, dict] = {}
    for t in tasks:
        if t.status in TASK_TERMINAL_STATUSES:
            continue
        for a in t.active_assignments():
            if a.role_in_task == "REVIEWER":
                continue
            entry = by_person.setdefault(a.user_id, {"user_id": a.user_id, "tasks": []})
            entry["tasks"].append(t)

    people_rows = []
    for uid, entry in by_person.items():
        user = db.session.get(User, uid)
        emp = user.employee if user else None
        current = emp.primary_active_assignment() if emp else None
        rows_tasks = sorted(entry["tasks"], key=lambda t: (_deadline(t) or date.max))
        nearest = rows_tasks[0] if rows_tasks else None
        people_rows.append({
            "user_id": uid,
            "full_name": user.full_name if user else None,
            "unit_name": current.unit.name if current and current.unit else None,
            "position_name": current.position.name if current and current.position else None,
            "active_task_count": len(rows_tasks),
            "overdue_count": sum(1 for t in rows_tasks if t.is_overdue()),
            "nearest_task": {
                "id": nearest.id, "code": nearest.code, "name": nearest.name,
                "assigner_id": nearest.assigner_id,
                "assigned_date": nearest.assigned_date.isoformat() if nearest.assigned_date else None,
                "deadline": _deadline(nearest).isoformat() if _deadline(nearest) else None,
                "progress_percent": nearest.progress_percent,
                "status": nearest.status,
                "days_left": (_deadline(nearest) - today).days if _deadline(nearest) else None,
                "is_blocked": nearest.is_blocked,
                "blocker_reason": nearest.blocker_reason,
            } if nearest else None,
        })
    people_rows.sort(key=lambda r: (-r["overdue_count"], -r["active_task_count"]))

    return {"stats": stats, "people": people_rows}
