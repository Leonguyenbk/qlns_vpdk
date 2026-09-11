"""Model phân hệ Giao việc – Theo dõi nhiệm vụ.

Nguyên tắc thiết kế (xem docs/TASK_KPI_ANALYSIS.md):
- Không tạo danh sách nhân sự/đăng nhập riêng: mọi FK trỏ về ``users``/``employees``
  đã có sẵn.
- Snapshot đơn vị/chức vụ tại thời điểm giao việc (``TaskAssignment``) để việc
  chuyển đơn vị/chức vụ sau này không làm sai lệch báo cáo cũ.
- "Quá hạn" KHÔNG phải là một trạng thái lưu trong ``status`` — nó là chỉ số
  tính toán (xem ``Task.is_overdue``).
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..common.utils import utcnow
from ..extensions import db
from .base import TimestampMixin


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _num(value) -> float | None:
    return float(value) if value is not None else None


class Task(TimestampMixin, db.Model):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("code", name="uq_tasks_code"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_assigning_unit", "assigning_unit_id"),
        Index("ix_tasks_executing_unit", "executing_unit_id"),
        Index("ix_tasks_parent", "parent_task_id"),
        Index("ix_tasks_deadline", "extended_deadline", "original_deadline"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Phân loại nghiệp vụ — tham chiếu danh mục dùng chung (mục 9, 10 tài liệu)
    business_group_code: Mapped[str | None] = mapped_column(
        ForeignKey("product_catalog_groups.code", ondelete="SET NULL"), nullable=True, index=True
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="AD_HOC")

    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    assigner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    assigning_unit_id: Mapped[int] = mapped_column(
        ForeignKey("organization_units.id", ondelete="RESTRICT"), nullable=False
    )
    executing_unit_id: Mapped[int | None] = mapped_column(
        ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True
    )

    parent_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    # False = nhiệm vụ cha chỉ tổng hợp/điều phối, KHÔNG tự phát sinh sản phẩm
    # riêng -> không tính khối lượng KPI (tránh trùng khối lượng với việc con).
    has_own_product: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="NORMAL")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")

    assigned_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    original_deadline: Mapped[date | None] = mapped_column(Date, index=True)
    extended_deadline: Mapped[date | None] = mapped_column(Date, index=True)
    deadline_type: Mapped[str] = mapped_column(String(10), nullable=False, default="INTERNAL")

    assigned_workload: Mapped[float | None] = mapped_column(Numeric(14, 2))
    workload_unit: Mapped[str | None] = mapped_column(String(50))

    output_description: Mapped[str | None] = mapped_column(Text)
    quality_standard: Mapped[str | None] = mapped_column(Text)
    acceptance_conditions: Mapped[str | None] = mapped_column(Text)
    complexity_level: Mapped[str | None] = mapped_column(String(30))

    # Snapshot Kn/CAP áp dụng cho nhiệm vụ này tại thời điểm tính điểm gần nhất
    # (KHÔNG phải giá trị "hiện hành" của sản phẩm — để đổi cấu hình sau này
    # không làm sai lệch điểm của kỳ đã tính).
    kn_snapshot: Mapped[float | None] = mapped_column(Numeric(6, 3))
    cap_snapshot: Mapped[float | None] = mapped_column(Numeric(14, 2))

    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_summary: Mapped[str | None] = mapped_column(Text)
    # Thang 5 mức (mục 13.1), chỉ có giá trị sau khi nghiệm thu
    quality_level: Mapped[int | None] = mapped_column(Integer)
    error_severity: Mapped[str | None] = mapped_column(String(30))  # NHỎ/LỚN/NGHIÊM TRỌNG/KHÔNG SỬ DỤNG ĐƯỢC

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    rework_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    blocker_reason: Mapped[str | None] = mapped_column(Text)

    cancel_reason: Mapped[str | None] = mapped_column(Text)
    cancelled_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Khoá lạc quan — chống ghi đè đồng thời (mục 9 yêu cầu phân quyền/audit)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    parent = relationship("Task", remote_side="Task.id", backref="children")
    assigning_unit = relationship("OrganizationUnit", foreign_keys=[assigning_unit_id])
    executing_unit = relationship("OrganizationUnit", foreign_keys=[executing_unit_id])
    product = relationship("Product")
    assignments: Mapped[list["TaskAssignment"]] = relationship(
        "TaskAssignment", back_populates="task", cascade="all, delete-orphan",
        order_by="TaskAssignment.assigned_at",
    )
    pauses: Mapped[list["TaskPause"]] = relationship(
        "TaskPause", back_populates="task", cascade="all, delete-orphan",
        order_by="TaskPause.started_at",
    )
    logs: Mapped[list["TaskLog"]] = relationship(
        "TaskLog", back_populates="task", cascade="all, delete-orphan",
        order_by="TaskLog.created_at",
    )
    attachments: Mapped[list["TaskAttachment"]] = relationship(
        "TaskAttachment", back_populates="task", cascade="all, delete-orphan",
    )

    @property
    def effective_deadline(self) -> date | None:
        return self.extended_deadline or self.original_deadline

    def is_overdue(self, *, today: date | None = None) -> bool:
        """Chỉ số tính toán — KHÔNG lưu trong CSDL, KHÔNG phải một trạng thái."""
        today = today or date.today()
        deadline = self.effective_deadline
        if deadline is None or self.status in ("COMPLETED", "CANCELLED"):
            return False
        return deadline < today

    def active_assignments(self) -> list["TaskAssignment"]:
        return [a for a in self.assignments if a.removed_at is None]

    def to_dict(self, *, include_relations: bool = True) -> dict:
        data = {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "business_group_code": self.business_group_code,
            "product_id": self.product_id,
            "source": self.source,
            "creator_id": self.creator_id,
            "assigner_id": self.assigner_id,
            "assigning_unit_id": self.assigning_unit_id,
            "executing_unit_id": self.executing_unit_id,
            "parent_task_id": self.parent_task_id,
            "has_own_product": self.has_own_product,
            "priority": self.priority,
            "status": self.status,
            "assigned_date": _iso(self.assigned_date),
            "start_date": _iso(self.start_date),
            "original_deadline": _iso(self.original_deadline),
            "extended_deadline": _iso(self.extended_deadline),
            "effective_deadline": _iso(self.effective_deadline),
            "deadline_type": self.deadline_type,
            "assigned_workload": _num(self.assigned_workload),
            "workload_unit": self.workload_unit,
            "output_description": self.output_description,
            "quality_standard": self.quality_standard,
            "acceptance_conditions": self.acceptance_conditions,
            "complexity_level": self.complexity_level,
            "kn_snapshot": _num(self.kn_snapshot),
            "cap_snapshot": _num(self.cap_snapshot),
            "progress_percent": self.progress_percent,
            "result_summary": self.result_summary,
            "quality_level": self.quality_level,
            "error_severity": self.error_severity,
            "submitted_at": _iso(self.submitted_at),
            "accepted_at": _iso(self.accepted_at),
            "accepted_by": self.accepted_by,
            "rework_count": self.rework_count,
            "is_blocked": self.is_blocked,
            "blocker_reason": self.blocker_reason,
            "is_overdue": self.is_overdue(),
            "cancel_reason": self.cancel_reason,
            "cancelled_at": _iso(self.cancelled_at),
            "version": self.version,
            "created_by": self.created_by,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }
        if include_relations:
            data["assigning_unit"] = (
                {"id": self.assigning_unit.id, "name": self.assigning_unit.name}
                if self.assigning_unit else None
            )
            data["executing_unit"] = (
                {"id": self.executing_unit.id, "name": self.executing_unit.name}
                if self.executing_unit else None
            )
            data["assignments"] = [a.to_dict() for a in self.active_assignments()]
            data["product"] = self.product.to_dict() if self.product else None
        return data


class TaskAssignment(TimestampMixin, db.Model):
    """Người tham gia thực hiện nhiệm vụ (chủ trì/phối hợp/nghiệm thu).

    Lưu snapshot đơn vị/chức vụ tại thời điểm giao — KHÔNG suy ra từ hồ sơ
    nhân sự hiện tại, để nhân sự chuyển đơn vị sau này không làm sai báo cáo cũ.
    """

    __tablename__ = "task_assignments"
    __table_args__ = (
        Index("ix_task_assignments_task", "task_id"),
        Index("ix_task_assignments_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    role_in_task: Mapped[str] = mapped_column(String(15), nullable=False, default="LEAD")
    # % đóng góp — dùng khi nhiều người cùng làm chung MỘT sản phẩm (tổng = 100%)
    contribution_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))

    unit_id_snapshot: Mapped[int | None] = mapped_column(ForeignKey("organization_units.id", ondelete="SET NULL"))
    position_id_snapshot: Mapped[int | None] = mapped_column(ForeignKey("positions.id", ondelete="SET NULL"))
    position_name_snapshot: Mapped[str | None] = mapped_column(String(150))
    is_managerial_snapshot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    assigned_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    removed_reason: Mapped[str | None] = mapped_column(Text)

    task = relationship("Task", back_populates="assignments")
    user = relationship("User", foreign_keys=[user_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "user_full_name": self.user.full_name if self.user else None,
            "role_in_task": self.role_in_task,
            "contribution_percent": _num(self.contribution_percent),
            "unit_id_snapshot": self.unit_id_snapshot,
            "position_id_snapshot": self.position_id_snapshot,
            "position_name_snapshot": self.position_name_snapshot,
            "is_managerial_snapshot": self.is_managerial_snapshot,
            "assigned_at": _iso(self.assigned_at),
            "removed_at": _iso(self.removed_at),
        }


class TaskPause(TimestampMixin, db.Model):
    """Khoảng thời gian loại trừ khỏi tính tiến độ (chờ/tạm dừng có minh chứng).

    Nhiều khoảng có thể chồng lấn — khi tính tổng thời gian loại trừ, service
    phải gộp (merge-interval) trước khi trừ, tránh trừ trùng (mục 14.3).
    """

    __tablename__ = "task_pauses"
    __table_args__ = (Index("ix_task_pauses_task", "task_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(30), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_ref: Mapped[str | None] = mapped_column(String(255))
    # Chỉ được TRỪ khỏi thời gian tính tiến độ sau khi có xác nhận (mục 14.3)
    confirmed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    task = relationship("Task", back_populates="pauses")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "reason_code": self.reason_code,
            "started_at": _iso(self.started_at),
            "ended_at": _iso(self.ended_at),
            "evidence_ref": self.evidence_ref,
            "confirmed_by": self.confirmed_by,
            "confirmed_at": _iso(self.confirmed_at),
            "is_confirmed": self.confirmed_at is not None,
            "note": self.note,
        }


class TaskLog(db.Model):
    """Nhật ký/luồng hoạt động của nhiệm vụ — bất biến (không sửa/xoá)."""

    __tablename__ = "task_logs"
    __table_args__ = (
        Index("ix_task_logs_task", "task_id"),
        Index("ix_task_logs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    log_kind: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    task = relationship("Task", back_populates="logs")
    user = relationship("User", foreign_keys=[user_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "user_full_name": self.user.full_name if self.user else None,
            "log_kind": self.log_kind,
            "content": self.content,
            "meta": self.meta,
            "created_at": _iso(self.created_at),
        }


class TaskAttachment(db.Model):
    __tablename__ = "task_attachments"
    __table_args__ = (Index("ix_task_attachments_task", "task_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    task_log_id: Mapped[int | None] = mapped_column(ForeignKey("task_logs.id", ondelete="SET NULL"))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    kind: Mapped[str] = mapped_column(String(15), nullable=False, default="EVIDENCE")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_type: Mapped[str | None] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    task = relationship("Task", back_populates="attachments")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_log_id": self.task_log_id,
            "uploaded_by": self.uploaded_by,
            "kind": self.kind,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "created_at": _iso(self.created_at),
        }


class TaskTemplate(TimestampMixin, db.Model):
    """Mẫu nhiệm vụ tái sử dụng — phục vụ giao việc định kỳ/hàng loạt."""

    __tablename__ = "task_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    business_group_code: Mapped[str | None] = mapped_column(
        ForeignKey("product_catalog_groups.code", ondelete="SET NULL")
    )
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    default_output_description: Mapped[str | None] = mapped_column(Text)
    default_quality_standard: Mapped[str | None] = mapped_column(Text)
    default_acceptance_conditions: Mapped[str | None] = mapped_column(Text)
    default_workload: Mapped[float | None] = mapped_column(Numeric(14, 2))
    default_workload_unit: Mapped[str | None] = mapped_column(String(50))
    default_priority: Mapped[str] = mapped_column(String(10), nullable=False, default="NORMAL")
    is_recurring: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recurrence_interval: Mapped[str | None] = mapped_column(String(10))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "business_group_code": self.business_group_code,
            "product_id": self.product_id,
            "default_output_description": self.default_output_description,
            "default_quality_standard": self.default_quality_standard,
            "default_acceptance_conditions": self.default_acceptance_conditions,
            "default_workload": _num(self.default_workload),
            "default_workload_unit": self.default_workload_unit,
            "default_priority": self.default_priority,
            "is_recurring": self.is_recurring,
            "recurrence_interval": self.recurrence_interval,
            "is_active": self.is_active,
            "created_at": _iso(self.created_at),
        }
