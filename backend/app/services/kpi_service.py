"""Nghiệp vụ Đánh giá KPI: danh mục sản phẩm, bộ tiêu chí, kỳ, tính điểm,
quy trình tự đánh giá -> theo dõi -> tổng hợp -> phê duyệt.

QUAN TRỌNG — đọc trước khi sửa:
- Toàn bộ hằng số/hệ số/ngưỡng là DỰ THẢO. Không được tự thêm giá trị minh
  hoạ nào từ tài liệu như thể đã chính thức.
- ``compute_score`` chỉ tính được các tiêu chí ĐỊNH LƯỢNG (Số lượng/Chất
  lượng/Tiến độ) từ dữ liệu ``tasks``. Tiêu chí định tính (đạo đức, năng lực
  tổ chức, đoàn kết...) KHÔNG bao giờ được suy ra tự động — luôn cần người
  chấm + minh chứng + nhận xét (``evaluator_id``/``evaluator_comment``).
- Kỳ đã khoá (``KpiPeriod.status == 'LOCKED'``) hoặc điểm đã khoá
  (``KpiScore.is_locked``) không được tính lại/sửa trực tiếp — chỉ sửa được
  qua ``adjust_score`` (tạo bản ghi mới, giữ nguyên bản cũ — Mẫu số 15).
"""
from __future__ import annotations

from datetime import date, timedelta

from ..common.exceptions import (
    BusinessRuleError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from ..common.utils import clean_str, parse_date, utcnow
from ..extensions import db
from ..models import (
    KpiCriteriaSet,
    KpiCriterion,
    KpiEvaluationComment,
    KpiPeriod,
    KpiScore,
    KpiScoreDetail,
    Product,
    ProductCatalogGroup,
    ProductConversion,
    Task,
    TaskAssignment,
    User,
)
from ..models.enums import (
    KPI_CRITERION_KINDS,
    KPI_EVALUATION_COMMENT_TYPES,
    KPI_FORMULA_KEYS,
    KPI_PERIOD_TYPES,
    CATALOG_STATUSES,
)
from ..permissions import constants as perms
from .audit_service import record_audit
from .kpi_formulas import apply_kn_cap, compute_ratio, points_from_ratio, suggested_rating, total_excluded_days
from .snapshot_utils import current_position_snapshot as _current_snapshot


# ------------------------------- Danh mục sản phẩm -------------------------------

def list_catalog_groups() -> list[dict]:
    rows = db.session.query(ProductCatalogGroup).order_by(ProductCatalogGroup.sort_order).all()
    return [r.to_dict() for r in rows]


def create_product(data: dict, *, actor: User) -> dict:
    if perms.KPI_CRITERIA_MANAGE not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền quản lý danh mục sản phẩm.")
    code = clean_str(data.get("code"))
    name = clean_str(data.get("name"))
    group_code = clean_str(data.get("group_code"))
    if not (code and name and group_code):
        raise ValidationError("Mã sản phẩm, tên và nhóm là bắt buộc.")
    if db.session.get(ProductCatalogGroup, group_code) is None:
        raise ValidationError("Nhóm sản phẩm không tồn tại.")
    status = clean_str(data.get("status")) or "DRAFT"
    if status not in CATALOG_STATUSES:
        raise ValidationError(f"Trạng thái phải thuộc: {', '.join(sorted(CATALOG_STATUSES))}.")
    product = Product(
        group_code=group_code, code=code, name=name,
        description=clean_str(data.get("description")),
        unit_of_measure=clean_str(data.get("unit_of_measure")),
        is_standard_product=bool(data.get("is_standard_product", False)),
        status=status,
        effective_date=parse_date(data.get("effective_date"), "effective_date"),
        notes=clean_str(data.get("notes")),
        created_by=actor.id,
    )
    db.session.add(product)
    db.session.commit()
    return product.to_dict()


def list_products(args) -> list[dict]:
    q = db.session.query(Product).filter(Product.is_active.is_(True))
    if args.get("group_code"):
        q = q.filter(Product.group_code == args["group_code"])
    return [p.to_dict() for p in q.order_by(Product.code).all()]


def create_conversion(product_id: int, data: dict, *, actor: User) -> dict:
    if perms.KPI_CRITERIA_MANAGE not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền cấu hình hệ số quy đổi.")
    product = db.session.get(Product, product_id)
    if product is None:
        raise NotFoundError("Không tìm thấy sản phẩm.")
    effective_from = parse_date(data.get("effective_from"), "effective_from")
    if not effective_from:
        raise ValidationError("Phải nhập ngày hiệu lực.")
    status = clean_str(data.get("status")) or "DRAFT"
    if status not in CATALOG_STATUSES:
        raise ValidationError(f"Trạng thái phải thuộc: {', '.join(sorted(CATALOG_STATUSES))}.")
    conv = ProductConversion(
        product_id=product_id,
        version=(max((c.version for c in product.conversions), default=0) + 1),
        kn_value=data.get("kn_value"),
        cap_value=data.get("cap_value"),
        standard_time_hours=data.get("standard_time_hours"),
        effective_from=effective_from,
        effective_to=parse_date(data.get("effective_to"), "effective_to"),
        status=status,
        approved_by=actor.id if status == "OFFICIAL" else None,
        notes=clean_str(data.get("notes")),
    )
    db.session.add(conv)
    record_audit(
        user_id=actor.id, action="kpi.set_conversion", entity_type="product", entity_id=product_id,
        new_values={"kn_value": conv.kn_value, "cap_value": conv.cap_value, "status": status},
    )
    db.session.commit()
    return conv.to_dict()


# ------------------------------- Bộ tiêu chí -------------------------------

def _flatten_criteria(nodes: list[KpiCriterion]) -> list[KpiCriterion]:
    out: list[KpiCriterion] = []
    for n in nodes:
        out.append(n)
        if n.children:
            out.extend(_flatten_criteria(n.children))
    return out


def _flatten_applicable_criteria(top_level: list[KpiCriterion], *, is_managerial: bool) -> list[KpiCriterion]:
    """Làm phẳng cây tiêu chí, LOẠI BỎ nhánh dành riêng cho loại vị trí khác
    (mục 7 áp dụng viên chức không quản lý, mục 8 áp dụng viên chức quản lý —
    hai khung không cộng dồn cho cùng một người)."""
    from ..models.enums import KPI_MANAGERIAL_ONLY_KINDS, KPI_NON_MANAGERIAL_ONLY_KINDS

    out: list[KpiCriterion] = []
    for root in top_level:
        if root.kind in KPI_MANAGERIAL_ONLY_KINDS and not is_managerial:
            continue
        if root.kind in KPI_NON_MANAGERIAL_ONLY_KINDS and is_managerial:
            continue
        out.append(root)
        if root.children:
            out.extend(_flatten_criteria(root.children))
    return out


def create_criteria_set(data: dict, *, actor: User) -> dict:
    if perms.KPI_CRITERIA_MANAGE not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền quản lý bộ tiêu chí KPI.")
    name = clean_str(data.get("name"))
    if not name:
        raise ValidationError("Tên bộ tiêu chí là bắt buộc.")
    effective_from = parse_date(data.get("effective_from"), "effective_from")
    if not effective_from:
        raise ValidationError("Phải nhập ngày hiệu lực.")
    status = clean_str(data.get("status")) or "DRAFT"
    if status not in CATALOG_STATUSES:
        raise ValidationError(f"Trạng thái phải thuộc: {', '.join(sorted(CATALOG_STATUSES))}.")

    cset = KpiCriteriaSet(
        name=name,
        version=data.get("version", 1),
        status=status,
        scope_unit_id=data.get("scope_unit_id"),
        applicable_position_type=clean_str(data.get("applicable_position_type")) or "ALL",
        applies_to_contract_labor=bool(data.get("applies_to_contract_labor", False)),
        effective_from=effective_from,
        effective_to=parse_date(data.get("effective_to"), "effective_to"),
        reference_documents=clean_str(data.get("reference_documents")),
        notes=clean_str(data.get("notes")),
        created_by=actor.id,
    )
    db.session.add(cset)
    db.session.flush()

    def _add_criteria(items: list[dict], parent_id: int | None):
        for i, item in enumerate(items):
            kind = item.get("kind")
            if kind not in KPI_CRITERION_KINDS:
                raise ValidationError(f"Loại tiêu chí không hợp lệ: {kind}")
            formula_key = item.get("formula_key")
            if formula_key and formula_key not in KPI_FORMULA_KEYS:
                raise ValidationError(f"Khoá công thức không hợp lệ: {formula_key}")
            node = KpiCriterion(
                criteria_set_id=cset.id, parent_id=parent_id,
                code=item.get("code") or f"C{i+1}", name=item.get("name") or "",
                kind=kind, max_points=item.get("max_points", 0), formula_key=formula_key,
                requires_evidence=item.get("requires_evidence", True),
                sort_order=item.get("sort_order", i),
                needs_confirmation=item.get("needs_confirmation", False),
                notes=clean_str(item.get("notes")),
            )
            db.session.add(node)
            db.session.flush()
            if item.get("children"):
                _add_criteria(item["children"], node.id)

    _add_criteria(data.get("criteria") or [], None)
    db.session.commit()
    return cset.to_dict(include_criteria=True)


def _general_group(code: str, name: str, max_points: float, items: list[tuple[str, str, float]]) -> dict:
    return {
        "code": code, "name": name, "kind": "GENERAL_GROUP", "max_points": max_points, "needs_confirmation": True,
        "notes": "Tên nhóm và nội dung định tính trích nguyên văn Phụ lục I Nghị định số 233/2026/NĐ-CP "
                 "(bắt buộc theo pháp luật); ĐIỂM SỐ từng tiêu chí con là phương án đề xuất thí điểm (mục 6.3).",
        "children": [
            {"code": code, "name": text, "kind": "GENERAL_ITEM", "max_points": pts,
             "requires_evidence": True, "needs_confirmation": True}
            for code, text, pts in items
        ],
    }


def build_draft_criteria_set_payload() -> dict:
    """Dựng sẵn cây tiêu chí đầy đủ theo đúng số liệu tại mục 6.3, 7.2, 8.2 và
    Phụ lục I của tài liệu dự thảo — KHÔNG bịa thêm nội dung ngoài tài liệu.
    Toàn bộ điểm số đều đánh dấu ``needs_confirmation=True`` vì tài liệu ghi rõ
    đây là "phương án đề xuất phục vụ thí điểm", chưa phải quyết định chính
    thức của Giám đốc VPĐKĐĐ.
    """
    nhom1 = _general_group("NHOM1", "Nhóm 1. Phẩm chất chính trị, đạo đức, kỷ luật, kỷ cương", 9.0, [
        ("N1a", "Chấp hành đường lối, chủ trương, chính sách, pháp luật, quy định của cơ quan", 1.0),
        ("N1b", "Lập trường chính trị vững vàng; đạo đức, lối sống lành mạnh", 1.0),
        ("N1c", "Chuẩn mực đạo đức nghề nghiệp; trung thực, khách quan, công bằng", 1.0),
        ("N1d", "Không tham nhũng, tiêu cực, lãng phí; không lợi dụng vị trí công tác để vụ lợi", 1.5),
        ("N1dd", "Tinh thần đoàn kết, hợp tác, xây dựng môi trường làm việc", 0.5),
        ("N1e", "Tự phê bình và phê bình; khắc phục hạn chế", 0.5),
        ("N1g", "Chấp hành phân công; thực hiện đầy đủ chức trách, nhiệm vụ", 1.0),
        ("N1h", "Thực hiện quy định, quy chế, nội quy cơ quan, đơn vị", 1.0),
        ("N1i", "Kê khai, công khai tài sản, thu nhập theo quy định", 0.5),
        ("N1k", "Báo cáo đầy đủ, trung thực, cung cấp thông tin chính xác", 1.0),
    ])
    nhom2 = _general_group(
        "NHOM2", "Nhóm 2. Năng lực chuyên môn, tinh thần trách nhiệm, thái độ phục vụ, phối hợp", 9.0, [
            ("N2a", "Năng lực chuyên môn, nghiệp vụ theo yêu cầu vị trí việc làm", 3.0),
            ("N2b", "Khả năng đáp ứng nhiệm vụ thường xuyên, đột xuất", 2.0),
            ("N2c", "Tinh thần trách nhiệm trong thực thi nhiệm vụ", 2.0),
            ("N2d", "Thái độ phục vụ người dân, doanh nghiệp / chất lượng phối hợp nội bộ", 2.0),
        ])
    nhom3 = _general_group(
        "NHOM3", "Nhóm 3. Đổi mới, sáng tạo, dám nghĩ, dám làm, dám chịu trách nhiệm", 12.0, [
            ("N3a", "Sản phẩm, giải pháp đột phá, sáng tạo, hiệu quả thiết thực", 4.0),
            ("N3b", "Chủ động nhận trách nhiệm khi có sai sót; biện pháp khắc phục rõ ràng", 4.0),
            ("N3c", "Chủ động quyết định trong thẩm quyền; tinh thần tiên phong", 4.0),
        ])

    staff_results = {
        "code": "STAFF70", "name": "Kết quả thực hiện nhiệm vụ (viên chức KHÔNG giữ chức vụ quản lý)",
        "kind": "STAFF_RESULTS", "max_points": 70.0, "needs_confirmation": True,
        "notes": "3 tiêu chí Số lượng/Chất lượng/Tiến độ bắt buộc theo khoản 1, 2 Điều 11 NĐ 233/2026; "
                 "trọng số 20/32/18 là đề xuất thí điểm (mục 7.2), ưu tiên chất lượng do rủi ro pháp lý đất đai.",
        "children": [
            {"code": "SL", "name": "Số lượng", "kind": "TASK_QUANTITY", "max_points": 20.0,
             "formula_key": "QUANTITY_RATIO", "requires_evidence": False, "needs_confirmation": True},
            {"code": "CL", "name": "Chất lượng", "kind": "TASK_QUALITY", "max_points": 32.0,
             "formula_key": "QUALITY_RATIO", "requires_evidence": False, "needs_confirmation": True},
            {"code": "TD", "name": "Tiến độ", "kind": "TASK_PROGRESS", "max_points": 18.0,
             "formula_key": "PROGRESS_RATIO", "requires_evidence": False, "needs_confirmation": True},
        ],
    }

    manager_personal = {
        "code": "MA", "name": "(a) Kết quả cá nhân trực tiếp thực hiện (viên chức giữ chức vụ quản lý)",
        "kind": "MANAGER_PERSONAL", "max_points": 28.0, "needs_confirmation": True,
        "notes": "Trọng số nội bộ SL/CL/TĐ giữ tương tự viên chức không quản lý (mục 8.2) — đề xuất thí điểm.",
        "children": [
            {"code": "MSL", "name": "Số lượng", "kind": "TASK_QUANTITY", "max_points": 8.0,
             "formula_key": "QUANTITY_RATIO", "requires_evidence": False, "needs_confirmation": True},
            {"code": "MCL", "name": "Chất lượng", "kind": "TASK_QUALITY", "max_points": 13.0,
             "formula_key": "QUALITY_RATIO", "requires_evidence": False, "needs_confirmation": True},
            {"code": "MTD", "name": "Tiến độ", "kind": "TASK_PROGRESS", "max_points": 7.0,
             "formula_key": "PROGRESS_RATIO", "requires_evidence": False, "needs_confirmation": True},
        ],
    }
    manager_unit = {
        "code": "MB", "name": "(b) Kết quả hoạt động của đơn vị/lĩnh vực được giao quản lý, phụ trách",
        "kind": "MANAGER_UNIT", "max_points": 21.0, "requires_evidence": True, "needs_confirmation": True,
        "notes": "Mức đạt 100%/50% theo mục 8.2 — chấm thủ công, bắt buộc minh chứng "
                 "(báo cáo hoạt động đơn vị/Chi nhánh, Mẫu số 10), KHÔNG suy ra tự động từ số liệu nhiệm vụ.",
    }
    manager_org = {
        "code": "MC", "name": "(c) Khả năng tổ chức triển khai thực hiện nhiệm vụ",
        "kind": "MANAGER_ORG_CAPABILITY", "max_points": 11.0, "requires_evidence": True, "needs_confirmation": True,
        "notes": "Mức đạt 100%/50% theo mục 8.2 — chấm thủ công, bắt buộc minh chứng.",
    }
    manager_cohesion = {
        "code": "MD", "name": "(d) Năng lực tập hợp, đoàn kết viên chức, người lao động thuộc phạm vi quản lý",
        "kind": "MANAGER_COHESION", "max_points": 10.0, "requires_evidence": True, "needs_confirmation": True,
        "notes": "Mức đạt 100%/50% theo mục 8.2 — chấm thủ công, bắt buộc minh chứng.",
    }

    return {
        "criteria": [
            nhom1, nhom2, nhom3, staff_results,
            manager_personal, manager_unit, manager_org, manager_cohesion,
        ],
    }


def create_default_criteria_set(data: dict, *, actor: User) -> dict:
    """Tạo bộ tiêu chí dự thảo đầy đủ (30 + 70 điểm, cả 2 khung quản lý/không
    quản lý) đúng số liệu tài liệu — dùng làm điểm khởi đầu để VPĐKĐĐ chỉnh
    sửa khi ban hành Quy chế chính thức, thay vì phải tự nhập lại từ đầu."""
    payload = build_draft_criteria_set_payload()
    payload["name"] = data.get("name") or "Bộ tiêu chí KPI VPĐKĐĐ (dự thảo theo Nghị định số 233/2026/NĐ-CP)"
    payload["effective_from"] = data.get("effective_from")
    payload["status"] = "DRAFT"
    payload["applicable_position_type"] = "ALL"
    payload["reference_documents"] = (
        "Nghị định số 233/2026/NĐ-CP ngày 26/6/2026; Dự thảo Đề án KPI công chức năm 2025 "
        "(Công văn số 02579/SNV-CCVC ngày 31/10/2025 của Sở Nội vụ tỉnh Đắk Lắk) — kế thừa có chọn lọc."
    )
    payload["notes"] = (
        "Toàn bộ điểm số, trọng số là phương án đề xuất phục vụ thí điểm (mục 6.3, 7.2, 8.2 tài liệu dự thảo), "
        "CHƯA phải quyết định chính thức — cần Giám đốc VPĐKĐĐ xem xét khi ban hành Quy chế đánh giá."
    )
    return create_criteria_set(payload, actor=actor)


def list_criteria_sets() -> list[dict]:
    rows = db.session.query(KpiCriteriaSet).order_by(KpiCriteriaSet.created_at.desc()).all()
    return [r.to_dict() for r in rows]


def get_criteria_set(cset_id: int) -> dict:
    cset = db.session.get(KpiCriteriaSet, cset_id)
    if cset is None:
        raise NotFoundError("Không tìm thấy bộ tiêu chí.")
    return cset.to_dict(include_criteria=True)


# ------------------------------- Kỳ đánh giá -------------------------------

def create_period(data: dict, *, actor: User) -> dict:
    if perms.KPI_PERIOD_MANAGE not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền quản lý kỳ đánh giá.")
    code = clean_str(data.get("code"))
    period_type = clean_str(data.get("period_type"))
    start_date = parse_date(data.get("start_date"), "start_date")
    end_date = parse_date(data.get("end_date"), "end_date")
    if not (code and period_type and start_date and end_date):
        raise ValidationError("Mã kỳ, loại kỳ, ngày bắt đầu/kết thúc là bắt buộc.")
    if period_type not in KPI_PERIOD_TYPES:
        raise ValidationError(f"Loại kỳ phải thuộc: {', '.join(sorted(KPI_PERIOD_TYPES))}.")
    if end_date < start_date:
        raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu.")
    period = KpiPeriod(
        code=code, period_type=period_type, start_date=start_date, end_date=end_date,
        criteria_set_id=data.get("criteria_set_id"),
        explanation_deadline_days=data.get("explanation_deadline_days", 5),
        created_by=actor.id,
    )
    db.session.add(period)
    db.session.commit()
    return period.to_dict()


def list_periods() -> list[dict]:
    rows = db.session.query(KpiPeriod).order_by(KpiPeriod.start_date.desc()).all()
    return [r.to_dict() for r in rows]


def _get_period(period_id: int) -> KpiPeriod:
    period = db.session.get(KpiPeriod, period_id)
    if period is None:
        raise NotFoundError("Không tìm thấy kỳ đánh giá.")
    return period


def lock_period(period_id: int, *, actor: User, meta: dict) -> dict:
    if perms.KPI_PERIOD_MANAGE not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền khoá kỳ đánh giá.")
    period = _get_period(period_id)
    if period.status == "LOCKED":
        raise BusinessRuleError("Kỳ đã khoá.")
    period.status = "LOCKED"
    period.locked_at = utcnow()
    period.locked_by = actor.id
    scores = db.session.query(KpiScore).filter(KpiScore.period_id == period_id).all()
    for s in scores:
        s.is_locked = True
    record_audit(
        user_id=actor.id, action="kpi.lock_period", entity_type="kpi_period", entity_id=period_id,
        new_values={"status": "LOCKED"}, **meta,
    )
    db.session.commit()
    return period.to_dict()


def reopen_period(period_id: int, data: dict, *, actor: User, meta: dict) -> dict:
    if perms.KPI_PERIOD_MANAGE not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền mở lại kỳ đánh giá.")
    period = _get_period(period_id)
    if period.status != "LOCKED":
        raise BusinessRuleError("Chỉ mở lại được kỳ đang ở trạng thái Đã khoá.")
    reason = clean_str(data.get("reason"))
    if not reason:
        raise ValidationError("Phải nêu lý do mở lại kỳ.")
    period.status = "REOPENED"
    period.reopened_reason = reason
    # KHÔNG tự mở khoá các KpiScore đã duyệt — sửa kết quả phải qua adjust_score
    # (giữ nguyên nguyên tắc "không xoá/ghi đè kết quả đã có" — mục 20.3).
    record_audit(
        user_id=actor.id, action="kpi.reopen_period", entity_type="kpi_period", entity_id=period_id,
        new_values={"status": "REOPENED", "reason": reason}, **meta,
    )
    db.session.commit()
    return period.to_dict()


# ------------------------------- Tính điểm định lượng -------------------------------

def _task_metrics_for_period(user_id: int, period: KpiPeriod) -> dict:
    """Xác định tập nhiệm vụ tính vào tử số/mẫu số của kỳ.

    QUY TẮC ÁP DỤNG (suy luận riêng của phần mềm — CHƯA được tài liệu chốt
    cho mọi trường hợp biên, xem docs/TASK_KPI_ANALYSIS.md mục 4.8):
    - Một nhiệm vụ được tính vào kỳ chứa HẠN HOÀN THÀNH HIỆU LỰC của nó (hoặc
      ngày giao nếu chưa có hạn) — nhờ vậy nhiệm vụ giao ở kỳ trước nhưng hạn
      rơi vào kỳ sau chỉ tính 1 lần, ở đúng kỳ chứa hạn (tránh trùng/carry-over).
    - Nhiệm vụ đã HỦY bị loại khỏi mẫu số hoàn toàn (kể cả huỷ vì lý do
      khách quan) — cần xác nhận khi ban hành Quy chế.
    - Nhiệm vụ cha thuần tổng hợp (``has_own_product=False``) không tính khối
      lượng, tránh trùng với nhiệm vụ con.
    - CAP áp theo luỹ kế từng sản phẩm trong kỳ (không theo từng nhiệm vụ đơn lẻ).
    """
    rows = (
        db.session.query(Task, TaskAssignment)
        .join(TaskAssignment, TaskAssignment.task_id == Task.id)
        .filter(
            TaskAssignment.user_id == user_id,
            TaskAssignment.removed_at.is_(None),
            TaskAssignment.role_in_task.in_(("LEAD", "COLLABORATOR")),
            Task.has_own_product.is_(True),
            Task.status != "CANCELLED",
        )
        .all()
    )

    def _period_ref(task: Task) -> date | None:
        return task.effective_deadline or task.assigned_date

    relevant = [(t, a) for t, a in rows if (_period_ref(t) and period.start_date <= _period_ref(t) <= period.end_date)]

    denom_total = 0.0
    denom_task_ids: list[int] = []
    quality_numerator = 0.0
    qual_task_ids: list[int] = []
    progress_numerator = 0.0
    prog_task_ids: list[int] = []
    completed_by_product: dict[int | None, float] = {}
    qty_task_ids: list[int] = []
    conv_cache: dict[int, tuple[float | None, float | None]] = {}

    for t, a in relevant:
        fraction = float(a.contribution_percent) / 100.0 if a.contribution_percent is not None else 1.0
        actual_qty = float(t.assigned_workload or 0) * fraction

        kn = cap = None
        if t.product_id:
            if t.product_id not in conv_cache:
                product = db.session.get(Product, t.product_id)
                conv = product.current_conversion(as_of=t.assigned_date) if product else None
                conv_cache[t.product_id] = (
                    float(conv.kn_value) if conv and conv.kn_value is not None else None,
                    float(conv.cap_value) if conv and conv.cap_value is not None else None,
                )
            kn, cap = conv_cache[t.product_id]

        converted, _ = apply_kn_cap(actual_qty, kn, None)
        denom_total += converted
        denom_task_ids.append(t.id)

        if t.status == "COMPLETED":
            completed_by_product[t.product_id] = completed_by_product.get(t.product_id, 0.0) + converted
            qty_task_ids.append(t.id)

            if t.quality_level is not None and t.quality_level >= 3:
                quality_numerator += converted
                qual_task_ids.append(t.id)

            eff_deadline = t.effective_deadline
            if eff_deadline is not None and t.submitted_at is not None:
                excluded_days = total_excluded_days([
                    (p.started_at, p.ended_at) for p in t.pauses
                    if p.confirmed_at is not None and p.ended_at is not None
                ])
                adjusted_deadline = eff_deadline + timedelta(days=excluded_days)
                if t.submitted_at.date() <= adjusted_deadline:
                    progress_numerator += converted
                    prog_task_ids.append(t.id)

    quantity_numerator = 0.0
    for product_id, converted_sum in completed_by_product.items():
        cap = conv_cache.get(product_id, (None, None))[1] if product_id else None
        quantity_numerator += converted_sum if cap is None else min(converted_sum, cap)

    return {
        "quantity": compute_ratio(quantity_numerator, denom_total, task_ids=qty_task_ids),
        "quality": compute_ratio(quality_numerator, denom_total, task_ids=qual_task_ids),
        "progress": compute_ratio(progress_numerator, denom_total, task_ids=prog_task_ids),
        "denominator_task_ids": denom_task_ids,
    }


def compute_score(period_id: int, user_id: int, *, actor: User, meta: dict) -> dict:
    if perms.KPI_REVIEW not in actor.permission_codes() and perms.KPI_AGGREGATE not in actor.permission_codes() \
            and perms.KPI_APPROVE not in actor.permission_codes() and user_id != actor.id:
        raise PermissionDeniedError("Bạn không có quyền tính điểm KPI cho người khác.")
    period = _get_period(period_id)
    if period.status != "OPEN":
        raise BusinessRuleError(
            "Kỳ đã khoá/đang xem xét lại — không thể tính hoặc tính lại điểm tạm tính. "
            "Dùng chức năng điều chỉnh kết quả (Mẫu số 15) nếu cần sửa sau khi khoá."
        )
    if period.criteria_set_id is None:
        raise BusinessRuleError("Kỳ chưa gắn bộ tiêu chí — hãy cấu hình trước khi tính điểm.")
    criteria_set = db.session.get(KpiCriteriaSet, period.criteria_set_id)
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản.")

    score = (
        db.session.query(KpiScore)
        .filter(KpiScore.period_id == period_id, KpiScore.user_id == user_id, KpiScore.replaces_id.is_(None))
        .order_by(KpiScore.id.desc())
        .first()
    )
    if score is not None and score.is_locked:
        raise BusinessRuleError("Kết quả đã được phê duyệt/khoá — dùng chức năng điều chỉnh để sửa.")

    if score is None:
        snap = _current_snapshot(user)
        score = KpiScore(
            period_id=period_id, user_id=user_id, employee_id_snapshot=user.employee_id,
            unit_id_snapshot=snap["unit_id"], position_id_snapshot=snap["position_id"],
            position_name_snapshot=snap["position_name"], is_managerial_snapshot=snap["is_managerial"],
            criteria_set_id_snapshot=criteria_set.id, status="DRAFT", created_by=actor.id,
        )
        db.session.add(score)
        db.session.flush()

    metrics = _task_metrics_for_period(user_id, period)
    formula_map = {
        "QUANTITY_RATIO": metrics["quantity"],
        "QUALITY_RATIO": metrics["quality"],
        "PROGRESS_RATIO": metrics["progress"],
    }

    top_level = [c for c in criteria_set.criteria if c.parent_id is None]
    all_criteria = _flatten_applicable_criteria(top_level, is_managerial=score.is_managerial_snapshot)
    for criterion in all_criteria:
        if criterion.kind in ("GENERAL_GROUP", "MANAGER_PERSONAL", "STAFF_RESULTS"):
            continue  # nhóm cha — không tự mang điểm
        detail = next((d for d in score.details if d.criteria_id == criterion.id), None)
        if detail is None:
            detail = KpiScoreDetail(kpi_score_id=score.id, criteria_id=criterion.id, max_points=criterion.max_points)
            db.session.add(detail)
            score.details.append(detail)
        detail.max_points = criterion.max_points
        if criterion.formula_key in formula_map:
            ratio = formula_map[criterion.formula_key]
            detail.raw_numerator = ratio.numerator
            detail.raw_denominator = ratio.denominator
            detail.ratio_percent = ratio.ratio_percent
            detail.points_earned = points_from_ratio(ratio.ratio_percent, float(criterion.max_points))
            detail.evidence_refs = {"task_ids": ratio.task_ids}
            # Quy tắc xác định tử số/mẫu số (carry-over, huỷ, đổi phạm vi...) là
            # suy luận riêng của phần mềm, CHƯA được Giám đốc VPĐKĐĐ xác nhận.
            detail.needs_confirmation = True
            detail.computed_at = utcnow()
        # Tiêu chí định tính: giữ nguyên điểm đã chấm thủ công (nếu có) — không tự suy luận.

    db.session.flush()
    score.provisional_total = round(
        sum(float(d.points_earned) for d in score.details if d.points_earned is not None), 2
    )
    db.session.commit()
    return get_score(score.id, actor=actor)


# ------------------------------- Quy trình đánh giá -------------------------------

def _get_score(score_id: int) -> KpiScore:
    score = db.session.get(KpiScore, score_id)
    if score is None:
        raise NotFoundError("Không tìm thấy kết quả KPI.")
    return score


def _assert_score_visible(score: KpiScore, *, actor: User) -> None:
    codes = actor.permission_codes()
    if perms.KPI_VIEW_ALL in codes or score.user_id == actor.id and perms.KPI_VIEW_OWN in codes:
        return
    raise PermissionDeniedError("Bạn không có quyền xem kết quả KPI này.")


def get_score(score_id: int, *, actor: User) -> dict:
    score = _get_score(score_id)
    _assert_score_visible(score, actor=actor)
    data = score.to_dict(include_details=True)
    data["comments"] = [
        c.to_dict() for c in
        db.session.query(KpiEvaluationComment).filter(KpiEvaluationComment.kpi_score_id == score_id)
        .order_by(KpiEvaluationComment.created_at).all()
    ]
    prev = score
    history = []
    while prev.replaces_id:
        prev = db.session.get(KpiScore, prev.replaces_id)
        if prev is None:
            break
        history.append(prev.to_dict())
    data["history"] = history
    return data


def _apply_detail_updates(score: KpiScore, updates: list[dict], actor: User) -> None:
    by_id = {d.criteria_id: d for d in score.details}
    for item in updates:
        detail = by_id.get(item.get("criteria_id"))
        if detail is None:
            continue
        criterion = detail.criteria
        if criterion is not None and criterion.formula_key:
            # Tiêu chí tự động — chỉ cho phép ghi nhận xét, KHÔNG cho sửa điểm tự tính
            detail.evaluator_comment = clean_str(item.get("evaluator_comment")) or detail.evaluator_comment
            continue
        points = item.get("points_earned")
        if points is not None:
            points = float(points)
            if not (0 <= points <= float(detail.max_points)):
                raise ValidationError(
                    f"Điểm tiêu chí '{criterion.name if criterion else detail.criteria_id}' phải trong khoảng 0-{detail.max_points}."
                )
            detail.points_earned = points
        comment = clean_str(item.get("evaluator_comment"))
        if criterion is not None and criterion.requires_evidence and not comment and not detail.evaluator_comment:
            raise ValidationError(
                f"Tiêu chí định tính '{criterion.name if criterion else ''}' bắt buộc có nhận xét của người chấm."
            )
        if comment:
            detail.evaluator_comment = comment
        detail.evaluator_id = actor.id
        detail.evidence_refs = item.get("evidence_refs", detail.evidence_refs)
        detail.is_confirmed = True


def _sum_points(score: KpiScore) -> float:
    return round(sum(float(d.points_earned) for d in score.details if d.points_earned is not None), 2)


def self_assess(score_id: int, data: dict, *, actor: User, meta: dict) -> dict:
    score = _get_score(score_id)
    if score.user_id != actor.id:
        raise PermissionDeniedError("Chỉ chính viên chức mới được tự đánh giá kết quả của mình.")
    if perms.KPI_SELF_ASSESS not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền tự đánh giá KPI.")
    if score.is_locked:
        raise BusinessRuleError("Kết quả đã khoá, không thể tự đánh giá lại.")
    _apply_detail_updates(score, data.get("details") or [], actor)
    score.self_assessed_total = _sum_points(score)
    score.status = "SELF_ASSESSED"
    score.self_assessed_at = utcnow()
    if data.get("proposed_rating"):
        score.proposed_rating = clean_str(data.get("proposed_rating"))
    record_audit(
        user_id=actor.id, action="kpi.self_assess", entity_type="kpi_score", entity_id=score.id,
        new_values={"self_assessed_total": score.self_assessed_total}, **meta,
    )
    db.session.commit()
    return get_score(score.id, actor=actor)


def review_score(score_id: int, data: dict, *, actor: User, meta: dict) -> dict:
    if perms.KPI_REVIEW not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền theo dõi, đánh giá KPI.")
    score = _get_score(score_id)
    if score.is_locked:
        raise BusinessRuleError("Kết quả đã khoá.")
    _apply_detail_updates(score, data.get("details") or [], actor)
    score.status = "REVIEWED"
    score.reviewed_by = actor.id
    score.reviewed_at = utcnow()
    record_audit(
        user_id=actor.id, action="kpi.review", entity_type="kpi_score", entity_id=score.id,
        new_values={"status": "REVIEWED"}, **meta,
    )
    db.session.commit()
    return get_score(score.id, actor=actor)


def aggregate_score(score_id: int, data: dict, *, actor: User, meta: dict) -> dict:
    if perms.KPI_AGGREGATE not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền tổng hợp KPI.")
    score = _get_score(score_id)
    if score.is_locked:
        raise BusinessRuleError("Kết quả đã khoá.")
    _apply_detail_updates(score, data.get("details") or [], actor)
    score.confirmed_total = _sum_points(score)
    score.proposed_rating = clean_str(data.get("proposed_rating")) or suggested_rating(score.confirmed_total)
    score.status = "AGGREGATED"
    score.aggregated_by = actor.id
    score.aggregated_at = utcnow()
    record_audit(
        user_id=actor.id, action="kpi.aggregate", entity_type="kpi_score", entity_id=score.id,
        new_values={"confirmed_total": score.confirmed_total, "proposed_rating": score.proposed_rating}, **meta,
    )
    db.session.commit()
    return get_score(score.id, actor=actor)


def approve_score(score_id: int, data: dict, *, actor: User, meta: dict) -> dict:
    if perms.KPI_APPROVE not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền quyết định xếp loại chất lượng.")
    score = _get_score(score_id)
    if score.user_id == actor.id:
        raise BusinessRuleError("Người tự đánh giá không được tự phê duyệt kết quả chính thức của chính mình.")
    if score.is_locked:
        raise BusinessRuleError("Kết quả đã được phê duyệt trước đó — dùng chức năng điều chỉnh nếu cần sửa.")
    official_rating = clean_str(data.get("official_rating"))
    if not official_rating:
        raise ValidationError(
            "Phải chọn mức xếp loại chính thức — hệ thống chỉ gợi ý theo ngưỡng điểm, "
            "không tự động xác định (mục 15 tài liệu yêu cầu xác nhận điều kiện loại trừ/trần tỷ lệ)."
        )
    score.official_rating = official_rating
    score.status = "APPROVED"
    score.approved_by = actor.id
    score.approved_at = utcnow()
    score.is_locked = True
    record_audit(
        user_id=actor.id, action="kpi.approve", entity_type="kpi_score", entity_id=score.id,
        new_values={"official_rating": official_rating}, **meta,
    )
    db.session.commit()
    return get_score(score.id, actor=actor)


def mark_not_rated(score_id: int, data: dict, *, actor: User, meta: dict) -> dict:
    """Mục 15.4/16.1 — trạng thái KHÔNG xếp loại (chưa đủ thời gian công tác...),
    KHÔNG phải mức "Không hoàn thành nhiệm vụ"."""
    if perms.KPI_APPROVE not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền đặt trạng thái không xếp loại.")
    score = _get_score(score_id)
    reason = clean_str(data.get("reason"))
    if not reason:
        raise ValidationError("Phải nêu căn cứ (Điều 14 Nghị định) cho việc không xếp loại.")
    score.status = "NOT_RATED"
    score.official_rating = None
    score.is_locked = True
    record_audit(
        user_id=actor.id, action="kpi.not_rated", entity_type="kpi_score", entity_id=score.id,
        new_values={"reason": reason}, **meta,
    )
    db.session.commit()
    return get_score(score.id, actor=actor)


def adjust_score(score_id: int, data: dict, *, actor: User, meta: dict) -> dict:
    """Mục 16.4/20.3 — Mẫu số 15: KHÔNG sửa bản ghi cũ, tạo bản ghi mới thay thế."""
    if perms.KPI_ADJUST not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền điều chỉnh kết quả KPI đã khoá.")
    old = _get_score(score_id)
    if not old.is_locked:
        raise BusinessRuleError("Chỉ điều chỉnh được kết quả đã phê duyệt/khoá; kết quả chưa khoá thì sửa trực tiếp.")
    reason = clean_str(data.get("reason"))
    if not reason:
        raise ValidationError("Phải nêu lý do điều chỉnh (sai sót/thiếu trung thực...).")
    new = KpiScore(
        period_id=old.period_id, user_id=old.user_id, employee_id_snapshot=old.employee_id_snapshot,
        unit_id_snapshot=old.unit_id_snapshot, position_id_snapshot=old.position_id_snapshot,
        position_name_snapshot=old.position_name_snapshot, is_managerial_snapshot=old.is_managerial_snapshot,
        criteria_set_id_snapshot=old.criteria_set_id_snapshot, status="DRAFT",
        provisional_total=old.provisional_total,
        replaces_id=old.id, replace_reason=reason, created_by=actor.id,
    )
    db.session.add(new)
    db.session.flush()
    for d in old.details:
        db.session.add(KpiScoreDetail(
            kpi_score_id=new.id, criteria_id=d.criteria_id, raw_numerator=d.raw_numerator,
            raw_denominator=d.raw_denominator, ratio_percent=d.ratio_percent,
            points_earned=d.points_earned, max_points=d.max_points, evidence_refs=d.evidence_refs,
        ))
    record_audit(
        user_id=actor.id, action="kpi.adjust", entity_type="kpi_score", entity_id=old.id,
        old_values={"official_rating": old.official_rating},
        new_values={"new_score_id": new.id, "reason": reason}, **meta,
    )
    db.session.commit()
    return get_score(new.id, actor=actor)


def add_comment(score_id: int, data: dict, *, actor: User) -> dict:
    score = _get_score(score_id)
    _assert_score_visible(score, actor=actor)
    comment_type = clean_str(data.get("comment_type")) or "STAKEHOLDER_INPUT"
    if comment_type not in KPI_EVALUATION_COMMENT_TYPES:
        raise ValidationError(f"Loại ý kiến phải thuộc: {', '.join(sorted(KPI_EVALUATION_COMMENT_TYPES))}.")
    content = clean_str(data.get("content"))
    if not content:
        raise ValidationError("Nội dung không được để trống.")
    comment = KpiEvaluationComment(
        kpi_score_id=score_id, comment_type=comment_type, author_id=actor.id,
        author_role_label=clean_str(data.get("author_role_label")), content=content,
    )
    db.session.add(comment)
    db.session.commit()
    return comment.to_dict()


def list_scores_for_period(period_id: int, *, actor: User, scope) -> list[dict]:
    if perms.KPI_VIEW_ALL not in actor.permission_codes():
        raise PermissionDeniedError("Bạn không có quyền xem tổng hợp KPI.")
    q = db.session.query(KpiScore).filter(KpiScore.period_id == period_id, KpiScore.replaces_id.is_(None))
    if not scope.is_global:
        if not scope.unit_ids:
            return []
        q = q.filter(KpiScore.unit_id_snapshot.in_(scope.unit_ids))
    return [s.to_dict(include_details=False) for s in q.all()]


def my_scores(*, actor: User) -> list[dict]:
    rows = (
        db.session.query(KpiScore)
        .filter(KpiScore.user_id == actor.id, KpiScore.replaces_id.is_(None))
        .order_by(KpiScore.period_id.desc())
        .all()
    )
    return [s.to_dict(include_details=True) for s in rows]
