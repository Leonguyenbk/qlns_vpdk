"""Model danh mục sản phẩm và Đánh giá KPI (Nghị định số 233/2026/NĐ-CP —
dự thảo/thí điểm, xem docs/TASK_KPI_ANALYSIS.md).

Mọi bộ tiêu chí (``KpiCriteriaSet``) và bảng quy đổi (``ProductConversion``)
mặc định ``status='DRAFT'`` và KHÔNG được phần mềm tự suy ra hệ số minh hoạ —
để trống nghĩa là chưa cấu hình, không phải bằng 0.
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


class ProductCatalogGroup(db.Model):
    """18 nhóm sản phẩm/công việc cố định theo Phụ lục II tài liệu dự thảo.

    Đây là dữ liệu tham chiếu trích trực tiếp từ tài liệu (không phải dữ liệu
    demo) — seed một lần trong migration, có thể sửa tên/mô tả qua Admin
    nhưng KHÔNG tự xoá khi đã có sản phẩm/nhiệm vụ tham chiếu.
    """

    __tablename__ = "product_catalog_groups"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)  # N1..N18
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    complexity_note: Mapped[str | None] = mapped_column(Text)
    error_impact_note: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "complexity_note": self.complexity_note,
            "error_impact_note": self.error_impact_note,
            "sort_order": self.sort_order,
        }


class Product(TimestampMixin, db.Model):
    """Danh mục sản phẩm/công việc chuẩn hoá (Mẫu số 02, 03)."""

    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("code", name="uq_products_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_code: Mapped[str] = mapped_column(
        ForeignKey("product_catalog_groups.code", ondelete="RESTRICT"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    unit_of_measure: Mapped[str | None] = mapped_column(String(50))
    is_standard_product: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    effective_date: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    group = relationship("ProductCatalogGroup")
    conversions: Mapped[list["ProductConversion"]] = relationship(
        "ProductConversion", back_populates="product", cascade="all, delete-orphan",
        order_by="ProductConversion.effective_from.desc()",
    )

    def current_conversion(self, *, as_of: date | None = None) -> "ProductConversion | None":
        as_of = as_of or date.today()
        candidates = [
            c for c in self.conversions
            if c.effective_from <= as_of and (c.effective_to is None or c.effective_to >= as_of)
        ]
        return candidates[0] if candidates else None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "group_code": self.group_code,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "unit_of_measure": self.unit_of_measure,
            "is_standard_product": self.is_standard_product,
            "status": self.status,
            "version": self.version,
            "effective_date": _iso(self.effective_date),
            "is_active": self.is_active,
            "notes": self.notes,
            "current_conversion": (
                self.current_conversion().to_dict() if self.current_conversion() else None
            ),
        }


class ProductConversion(TimestampMixin, db.Model):
    """Bảng quy đổi Kn/CAP theo phiên bản (Mẫu số 04, mục 11).

    ``kn_value``/``cap_value`` để NULL nghĩa là CHƯA cấu hình — service tính
    KPI phải coi NULL = không quy đổi/không giới hạn, không được mặc định 1.0
    hay một con số minh hoạ nào trong tài liệu như thể đó là giá trị chính thức.
    """

    __tablename__ = "product_conversions"
    __table_args__ = (Index("ix_product_conversions_product", "product_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    kn_value: Mapped[float | None] = mapped_column(Numeric(6, 3))
    cap_value: Mapped[float | None] = mapped_column(Numeric(14, 2))
    standard_time_hours: Mapped[float | None] = mapped_column(Numeric(10, 2))
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="DRAFT")
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    notes: Mapped[str | None] = mapped_column(Text)

    product = relationship("Product", back_populates="conversions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "version": self.version,
            "kn_value": _num(self.kn_value),
            "cap_value": _num(self.cap_value),
            "standard_time_hours": _num(self.standard_time_hours),
            "effective_from": _iso(self.effective_from),
            "effective_to": _iso(self.effective_to),
            "status": self.status,
            "notes": self.notes,
        }


class KpiCriteriaSet(TimestampMixin, db.Model):
    """Bộ tiêu chí đánh giá — có phiên bản, phạm vi, trạng thái dự thảo/thí điểm.

    Đổi một bộ tiêu chí KHÔNG được tự động tính lại các kỳ đã khoá
    (``KpiPeriod.status == 'LOCKED'``) — service phải chặn việc này ở tầng
    nghiệp vụ, không chỉ ở giao diện.
    """

    __tablename__ = "kpi_criteria_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="DRAFT")
    scope_unit_id: Mapped[int | None] = mapped_column(
        ForeignKey("organization_units.id", ondelete="SET NULL")
    )  # NULL = áp dụng toàn VPĐKĐĐ
    applicable_position_type: Mapped[str] = mapped_column(String(15), nullable=False, default="ALL")
    applies_to_contract_labor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reference_documents: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    criteria: Mapped[list["KpiCriterion"]] = relationship(
        "KpiCriterion", back_populates="criteria_set", cascade="all, delete-orphan",
        order_by="KpiCriterion.sort_order",
    )

    def to_dict(self, *, include_criteria: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "scope_unit_id": self.scope_unit_id,
            "applicable_position_type": self.applicable_position_type,
            "applies_to_contract_labor": self.applies_to_contract_labor,
            "effective_from": _iso(self.effective_from),
            "effective_to": _iso(self.effective_to),
            "approved_by": self.approved_by,
            "approved_at": _iso(self.approved_at),
            "reference_documents": self.reference_documents,
            "notes": self.notes,
            "created_at": _iso(self.created_at),
        }
        if include_criteria:
            data["criteria"] = [c.to_dict() for c in self.criteria if c.parent_id is None]
        return data


class KpiCriterion(db.Model):
    """Cây tiêu chí: Nhóm -> tiêu chí con (mục 6, 7, 8, Phụ lục I)."""

    __tablename__ = "kpi_criteria"
    __table_args__ = (Index("ix_kpi_criteria_set", "criteria_set_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    criteria_set_id: Mapped[int] = mapped_column(
        ForeignKey("kpi_criteria_sets.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("kpi_criteria.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    max_points: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    # Khoá công thức tự động (chỉ áp dụng cho TASK_QUANTITY/QUALITY/PROGRESS);
    # NULL nghĩa là tiêu chí định tính, phải chấm thủ công có minh chứng.
    formula_key: Mapped[str | None] = mapped_column(String(30))
    requires_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Đánh dấu rõ khi nội dung tài liệu chưa chốt — hiển thị cảnh báo, KHÔNG ẩn.
    needs_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text)

    criteria_set = relationship("KpiCriteriaSet", back_populates="criteria")
    children = relationship(
        "KpiCriterion", backref=db.backref("parent", remote_side="KpiCriterion.id")
    )

    def to_dict(self, *, include_children: bool = True) -> dict:
        data = {
            "id": self.id,
            "criteria_set_id": self.criteria_set_id,
            "parent_id": self.parent_id,
            "code": self.code,
            "name": self.name,
            "kind": self.kind,
            "max_points": _num(self.max_points),
            "formula_key": self.formula_key,
            "requires_evidence": self.requires_evidence,
            "sort_order": self.sort_order,
            "needs_confirmation": self.needs_confirmation,
            "notes": self.notes,
        }
        if include_children:
            data["children"] = [c.to_dict(include_children=False) for c in sorted(self.children, key=lambda x: x.sort_order)]
        return data


class KpiPeriod(TimestampMixin, db.Model):
    """Kỳ theo dõi/đánh giá (tháng/quý/năm) — đơn vị khoá dữ liệu KPI."""

    __tablename__ = "kpi_periods"
    __table_args__ = (UniqueConstraint("code", name="uq_kpi_periods_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # "2026-Q3", "2026-12", "2026"
    period_type: Mapped[str] = mapped_column(String(10), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="OPEN")
    criteria_set_id: Mapped[int | None] = mapped_column(
        ForeignKey("kpi_criteria_sets.id", ondelete="SET NULL")
    )
    explanation_deadline_days: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reopened_reason: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    criteria_set = relationship("KpiCriteriaSet")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "period_type": self.period_type,
            "start_date": _iso(self.start_date),
            "end_date": _iso(self.end_date),
            "status": self.status,
            "criteria_set_id": self.criteria_set_id,
            "explanation_deadline_days": self.explanation_deadline_days,
            "locked_at": _iso(self.locked_at),
            "reopened_reason": self.reopened_reason,
        }


class KpiScore(TimestampMixin, db.Model):
    """Kết quả đánh giá KPI của một người trong một kỳ.

    ``replaces_id``/``replaced_by_id`` hiện thực mục 16.4/20.3: khi phát hiện
    sai sót sau khi đã xếp loại, KHÔNG sửa bản ghi cũ — tạo bản ghi mới trỏ
    tới bản cũ, bản cũ vẫn được giữ nguyên trong CSDL để truy vết (Mẫu số 15).
    """

    __tablename__ = "kpi_scores"
    __table_args__ = (
        UniqueConstraint("period_id", "user_id", "replaces_id", name="uq_kpi_scores_period_user_version"),
        Index("ix_kpi_scores_period", "period_id"),
        Index("ix_kpi_scores_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("kpi_periods.id", ondelete="RESTRICT"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    employee_id_snapshot: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"))
    unit_id_snapshot: Mapped[int | None] = mapped_column(ForeignKey("organization_units.id", ondelete="SET NULL"))
    position_id_snapshot: Mapped[int | None] = mapped_column(ForeignKey("positions.id", ondelete="SET NULL"))
    position_name_snapshot: Mapped[str | None] = mapped_column(String(150))
    is_managerial_snapshot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criteria_set_id_snapshot: Mapped[int | None] = mapped_column(
        ForeignKey("kpi_criteria_sets.id", ondelete="SET NULL")
    )

    status: Mapped[str] = mapped_column(String(15), nullable=False, default="DRAFT")

    provisional_total: Mapped[float | None] = mapped_column(Numeric(6, 2))
    self_assessed_total: Mapped[float | None] = mapped_column(Numeric(6, 2))
    confirmed_total: Mapped[float | None] = mapped_column(Numeric(6, 2))
    proposed_rating: Mapped[str | None] = mapped_column(String(50))
    official_rating: Mapped[str | None] = mapped_column(String(50))

    self_assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    aggregated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    aggregated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    replaces_id: Mapped[int | None] = mapped_column(ForeignKey("kpi_scores.id", ondelete="SET NULL"))
    replace_reason: Mapped[str | None] = mapped_column(Text)

    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    period = relationship("KpiPeriod")
    user = relationship("User", foreign_keys=[user_id])
    details: Mapped[list["KpiScoreDetail"]] = relationship(
        "KpiScoreDetail", back_populates="score", cascade="all, delete-orphan"
    )
    replaces = relationship("KpiScore", remote_side="KpiScore.id")

    def to_dict(self, *, include_details: bool = False) -> dict:
        data = {
            "id": self.id,
            "period_id": self.period_id,
            "user_id": self.user_id,
            "user_full_name": self.user.full_name if self.user else None,
            "employee_id_snapshot": self.employee_id_snapshot,
            "unit_id_snapshot": self.unit_id_snapshot,
            "position_name_snapshot": self.position_name_snapshot,
            "is_managerial_snapshot": self.is_managerial_snapshot,
            "criteria_set_id_snapshot": self.criteria_set_id_snapshot,
            "status": self.status,
            "provisional_total": _num(self.provisional_total),
            "self_assessed_total": _num(self.self_assessed_total),
            "confirmed_total": _num(self.confirmed_total),
            "proposed_rating": self.proposed_rating,
            "official_rating": self.official_rating,
            "replaces_id": self.replaces_id,
            "replace_reason": self.replace_reason,
            "is_locked": self.is_locked,
            "created_at": _iso(self.created_at),
        }
        if include_details:
            data["details"] = [d.to_dict() for d in self.details]
        return data


class KpiScoreDetail(db.Model):
    """Chi tiết điểm theo từng tiêu chí — cơ sở truy vết bắt buộc.

    ``ratio_percent`` = NULL nghĩa là "Chưa đủ dữ liệu/Chờ xác nhận" (mẫu số
    bằng 0 hoặc chưa xác định) — KHÔNG được tự quy về 0% hay 100%.
    """

    __tablename__ = "kpi_score_details"
    __table_args__ = (
        UniqueConstraint("kpi_score_id", "criteria_id", name="uq_kpi_score_detail"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kpi_score_id: Mapped[int] = mapped_column(ForeignKey("kpi_scores.id", ondelete="CASCADE"), nullable=False)
    criteria_id: Mapped[int] = mapped_column(ForeignKey("kpi_criteria.id", ondelete="RESTRICT"), nullable=False)

    raw_numerator: Mapped[float | None] = mapped_column(Numeric(14, 2))
    raw_denominator: Mapped[float | None] = mapped_column(Numeric(14, 2))
    ratio_percent: Mapped[float | None] = mapped_column(Numeric(6, 2))
    points_earned: Mapped[float | None] = mapped_column(Numeric(6, 2))
    max_points: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)

    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evaluator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    evaluator_comment: Mapped[str | None] = mapped_column(Text)
    # Danh sách id nhiệm vụ/minh chứng cấu thành số liệu — bắt buộc để truy vết
    evidence_refs: Mapped[dict | None] = mapped_column(JSON)
    needs_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    score = relationship("KpiScore", back_populates="details")
    criteria = relationship("KpiCriterion")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kpi_score_id": self.kpi_score_id,
            "criteria_id": self.criteria_id,
            "criteria_code": self.criteria.code if self.criteria else None,
            "criteria_name": self.criteria.name if self.criteria else None,
            "raw_numerator": _num(self.raw_numerator),
            "raw_denominator": _num(self.raw_denominator),
            "ratio_percent": _num(self.ratio_percent),
            "points_earned": _num(self.points_earned),
            "max_points": _num(self.max_points),
            "is_confirmed": self.is_confirmed,
            "evaluator_id": self.evaluator_id,
            "evaluator_comment": self.evaluator_comment,
            "evidence_refs": self.evidence_refs,
            "needs_confirmation": self.needs_confirmation,
            "no_data": self.ratio_percent is None and self.raw_denominator in (None, 0),
            "computed_at": _iso(self.computed_at),
        }


class KpiEvaluationComment(db.Model):
    """Biên bản họp / ý kiến cấp ủy / giải trình / đề nghị điều chỉnh (Mẫu 13, 14)."""

    __tablename__ = "kpi_evaluation_comments"
    __table_args__ = (Index("ix_kpi_eval_comments_score", "kpi_score_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    kpi_score_id: Mapped[int] = mapped_column(ForeignKey("kpi_scores.id", ondelete="CASCADE"), nullable=False)
    comment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    author_role_label: Mapped[str | None] = mapped_column(String(150))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(15), nullable=False, default="OPEN")  # OPEN/RESOLVED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kpi_score_id": self.kpi_score_id,
            "comment_type": self.comment_type,
            "author_id": self.author_id,
            "author_role_label": self.author_role_label,
            "content": self.content,
            "status": self.status,
            "created_at": _iso(self.created_at),
        }
