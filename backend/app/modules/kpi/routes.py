"""Route Đánh giá KPI: danh mục sản phẩm, bộ tiêu chí, kỳ, tính điểm, quy trình
tự đánh giá -> theo dõi -> tổng hợp -> phê duyệt."""
from __future__ import annotations

from flask import Blueprint, request

from ...common.responses import success
from ...common.auth_context import require_permission
from ...permissions import constants as perms
from ...services import kpi_service
from .._helpers import actor_and_scope, audit_meta, json_body

bp = Blueprint("kpi", __name__, url_prefix="/api/kpi")


# --- Danh mục sản phẩm ---

@bp.get("/catalog-groups")
@require_permission(perms.KPI_VIEW_ALL, perms.KPI_CRITERIA_MANAGE, perms.TASK_CREATE, perms.TASK_VIEW_OWN)
def catalog_groups():
    return success(kpi_service.list_catalog_groups())


@bp.get("/products")
@require_permission(perms.KPI_VIEW_ALL, perms.KPI_CRITERIA_MANAGE, perms.TASK_CREATE, perms.TASK_VIEW_OWN)
def list_products():
    return success(kpi_service.list_products(request.args))


@bp.post("/products")
@require_permission(perms.KPI_CRITERIA_MANAGE)
def create_product():
    actor, _ = actor_and_scope()
    return success(kpi_service.create_product(json_body(), actor=actor), "Thêm sản phẩm thành công", status_code=201)


@bp.post("/products/<int:product_id>/conversions")
@require_permission(perms.KPI_CRITERIA_MANAGE)
def create_conversion(product_id: int):
    actor, _ = actor_and_scope()
    return success(
        kpi_service.create_conversion(product_id, json_body(), actor=actor),
        "Cấu hình hệ số quy đổi thành công", status_code=201,
    )


# --- Bộ tiêu chí ---

@bp.get("/criteria-sets")
@require_permission(perms.KPI_CRITERIA_MANAGE, perms.KPI_VIEW_ALL)
def list_criteria_sets():
    return success(kpi_service.list_criteria_sets())


@bp.post("/criteria-sets")
@require_permission(perms.KPI_CRITERIA_MANAGE)
def create_criteria_set():
    actor, _ = actor_and_scope()
    return success(kpi_service.create_criteria_set(json_body(), actor=actor), "Tạo bộ tiêu chí thành công", status_code=201)


@bp.post("/criteria-sets/default")
@require_permission(perms.KPI_CRITERIA_MANAGE)
def create_default_criteria_set():
    """Dựng sẵn bộ tiêu chí đầy đủ (30 + 70 điểm, cả 2 khung) đúng số liệu
    tài liệu dự thảo — điểm khởi đầu để chỉnh sửa, không phải nhập tay từ đầu."""
    actor, _ = actor_and_scope()
    return success(
        kpi_service.create_default_criteria_set(json_body(), actor=actor),
        "Đã tạo bộ tiêu chí dự thảo đầy đủ theo tài liệu — vui lòng rà soát trước khi dùng chính thức",
        status_code=201,
    )


@bp.get("/criteria-sets/<int:cset_id>")
@require_permission(perms.KPI_CRITERIA_MANAGE, perms.KPI_VIEW_ALL, perms.KPI_VIEW_OWN)
def get_criteria_set(cset_id: int):
    return success(kpi_service.get_criteria_set(cset_id))


# --- Kỳ đánh giá ---

@bp.get("/periods")
@require_permission(perms.KPI_PERIOD_MANAGE, perms.KPI_VIEW_ALL, perms.KPI_VIEW_OWN)
def list_periods():
    return success(kpi_service.list_periods())


@bp.post("/periods")
@require_permission(perms.KPI_PERIOD_MANAGE)
def create_period():
    actor, _ = actor_and_scope()
    return success(kpi_service.create_period(json_body(), actor=actor), "Tạo kỳ đánh giá thành công", status_code=201)


@bp.post("/periods/<int:period_id>/lock")
@require_permission(perms.KPI_PERIOD_MANAGE)
def lock_period(period_id: int):
    actor, _ = actor_and_scope()
    return success(kpi_service.lock_period(period_id, actor=actor, meta=audit_meta()), "Đã khoá kỳ đánh giá")


@bp.post("/periods/<int:period_id>/reopen")
@require_permission(perms.KPI_PERIOD_MANAGE)
def reopen_period(period_id: int):
    actor, _ = actor_and_scope()
    return success(kpi_service.reopen_period(period_id, json_body(), actor=actor, meta=audit_meta()), "Đã mở lại kỳ đánh giá")


@bp.get("/periods/<int:period_id>/scores")
@require_permission(perms.KPI_VIEW_ALL)
def list_period_scores(period_id: int):
    actor, scope = actor_and_scope()
    return success(kpi_service.list_scores_for_period(period_id, actor=actor, scope=scope))


@bp.post("/periods/<int:period_id>/scores/<int:user_id>/compute")
def compute_score(period_id: int, user_id: int):
    actor, _ = actor_and_scope()
    return success(
        kpi_service.compute_score(period_id, user_id, actor=actor, meta=audit_meta()),
        "Tính điểm tạm tính thành công",
    )


# --- Điểm KPI cá nhân / quy trình đánh giá ---

@bp.get("/scores/mine")
@require_permission(perms.KPI_VIEW_OWN)
def my_scores():
    actor, _ = actor_and_scope()
    return success(kpi_service.my_scores(actor=actor))


@bp.get("/scores/<int:score_id>")
def get_score(score_id: int):
    actor, _ = actor_and_scope()
    return success(kpi_service.get_score(score_id, actor=actor))


@bp.post("/scores/<int:score_id>/self-assess")
@require_permission(perms.KPI_SELF_ASSESS)
def self_assess(score_id: int):
    actor, _ = actor_and_scope()
    return success(kpi_service.self_assess(score_id, json_body(), actor=actor, meta=audit_meta()), "Đã lưu tự đánh giá")


@bp.post("/scores/<int:score_id>/review")
@require_permission(perms.KPI_REVIEW)
def review_score(score_id: int):
    actor, _ = actor_and_scope()
    return success(kpi_service.review_score(score_id, json_body(), actor=actor, meta=audit_meta()), "Đã lưu kết quả theo dõi, đánh giá")


@bp.post("/scores/<int:score_id>/aggregate")
@require_permission(perms.KPI_AGGREGATE)
def aggregate_score(score_id: int):
    actor, _ = actor_and_scope()
    return success(kpi_service.aggregate_score(score_id, json_body(), actor=actor, meta=audit_meta()), "Đã tổng hợp kết quả")


@bp.post("/scores/<int:score_id>/approve")
@require_permission(perms.KPI_APPROVE)
def approve_score(score_id: int):
    actor, _ = actor_and_scope()
    return success(kpi_service.approve_score(score_id, json_body(), actor=actor, meta=audit_meta()), "Đã phê duyệt xếp loại chính thức")


@bp.post("/scores/<int:score_id>/not-rated")
@require_permission(perms.KPI_APPROVE)
def mark_not_rated(score_id: int):
    actor, _ = actor_and_scope()
    return success(kpi_service.mark_not_rated(score_id, json_body(), actor=actor, meta=audit_meta()), "Đã đặt trạng thái không xếp loại")


@bp.post("/scores/<int:score_id>/adjust")
@require_permission(perms.KPI_ADJUST)
def adjust_score(score_id: int):
    actor, _ = actor_and_scope()
    return success(kpi_service.adjust_score(score_id, json_body(), actor=actor, meta=audit_meta()), "Đã tạo kết quả điều chỉnh thay thế", status_code=201)


@bp.post("/scores/<int:score_id>/comments")
def add_comment(score_id: int):
    actor, _ = actor_and_scope()
    return success(kpi_service.add_comment(score_id, json_body(), actor=actor), "Đã thêm ý kiến", status_code=201)
