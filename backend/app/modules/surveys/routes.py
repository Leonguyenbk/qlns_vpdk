"""Route module Khảo sát – Đánh giá mức độ hài lòng (quản trị + công khai)."""
from __future__ import annotations

from flask import Blueprint, request, send_file

from ...common.auth_context import require_permission
from ...common.responses import paginated, success
from ...permissions import constants as perms
from ...schemas import (
    reorder_schema,
    survey_branch_limits_schema,
    survey_create_schema,
    survey_option_create_schema,
    survey_option_update_schema,
    survey_question_create_schema,
    survey_question_update_schema,
    survey_section_create_schema,
    survey_section_update_schema,
    survey_results_public_schema,
    survey_status_schema,
    survey_submit_schema,
    survey_update_schema,
)
from ...services import (
    survey_question_service,
    survey_response_service,
    survey_service,
    survey_statistics_service,
)
from .._helpers import actor_and_scope, audit_meta, validated_json

bp = Blueprint("surveys", __name__, url_prefix="/api/surveys")
questions_bp = Blueprint("survey_questions", __name__, url_prefix="/api/survey-questions")
options_bp = Blueprint("survey_options", __name__, url_prefix="/api/survey-options")
sections_bp = Blueprint("survey_sections", __name__, url_prefix="/api/survey-sections")
public_bp = Blueprint("public_surveys", __name__, url_prefix="/api/public/surveys")


# ----------------------------- Khảo sát -----------------------------
@bp.get("")
@require_permission(perms.SURVEY_VIEW)
def list_surveys():
    res = survey_service.list_surveys(request.args)
    return paginated(res["items"], res["page"], res["page_size"], res["total"])


@bp.post("")
@require_permission(perms.SURVEY_CREATE)
def create_survey():
    actor, _ = actor_and_scope()
    data = survey_service.create_survey(
        validated_json(survey_create_schema), actor=actor, meta=audit_meta()
    )
    return success(data, "Tạo khảo sát thành công", status_code=201)


@bp.get("/<int:survey_id>")
@require_permission(perms.SURVEY_VIEW)
def get_survey(survey_id: int):
    return success(survey_service.get_survey(survey_id))


@bp.put("/<int:survey_id>")
@require_permission(perms.SURVEY_UPDATE)
def update_survey(survey_id: int):
    actor, _ = actor_and_scope()
    data = survey_service.update_survey(
        survey_id, validated_json(survey_update_schema), actor=actor, meta=audit_meta()
    )
    return success(data, "Cập nhật khảo sát thành công")


@bp.delete("/<int:survey_id>")
@require_permission(perms.SURVEY_DELETE)
def delete_survey(survey_id: int):
    actor, _ = actor_and_scope()
    survey_service.delete_survey(survey_id, actor=actor, meta=audit_meta())
    return success(None, "Đã xóa khảo sát")


@bp.post("/<int:survey_id>/status")
@require_permission(perms.SURVEY_UPDATE)
def change_status(survey_id: int):
    actor, _ = actor_and_scope()
    payload = validated_json(survey_status_schema)
    data = survey_service.change_status(
        survey_id, payload["status"], actor=actor, meta=audit_meta()
    )
    return success(data, "Cập nhật trạng thái khảo sát thành công")


@bp.put("/<int:survey_id>/results-public")
@require_permission(perms.SURVEY_UPDATE)
def set_results_public(survey_id: int):
    actor, _ = actor_and_scope()
    payload = validated_json(survey_results_public_schema)
    data = survey_service.set_results_public(
        survey_id, payload["is_results_public"], actor=actor, meta=audit_meta()
    )
    message = "Đã công khai bảng xếp hạng" if data["is_results_public"] else "Đã ẩn bảng xếp hạng công khai"
    return success(data, message)


@bp.post("/<int:survey_id>/duplicate")
@require_permission(perms.SURVEY_CREATE)
def duplicate_survey(survey_id: int):
    actor, _ = actor_and_scope()
    data = survey_service.duplicate_survey(survey_id, actor=actor, meta=audit_meta())
    return success(data, "Sao chép khảo sát thành công", status_code=201)


@bp.get("/<int:survey_id>/branch-limits")
@require_permission(perms.SURVEY_VIEW)
def get_branch_limits(survey_id: int):
    return success(survey_service.get_branch_limits(survey_id))


@bp.put("/<int:survey_id>/branch-limits")
@require_permission(perms.SURVEY_UPDATE)
def set_branch_limits(survey_id: int):
    actor, _ = actor_and_scope()
    payload = validated_json(survey_branch_limits_schema)
    data = survey_service.set_branch_limits(
        survey_id, payload["items"], actor=actor, meta=audit_meta()
    )
    return success(data, "Đã cập nhật chỉ tiêu theo chi nhánh")


# ----------------------------- Phần khảo sát -----------------------------
@bp.get("/<int:survey_id>/sections")
@require_permission(perms.SURVEY_VIEW)
def list_sections(survey_id: int):
    return success(survey_question_service.list_sections(survey_id))


@bp.post("/<int:survey_id>/sections")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def create_section(survey_id: int):
    actor, _ = actor_and_scope()
    data = survey_question_service.create_section(
        survey_id,
        validated_json(survey_section_create_schema),
        actor=actor,
        meta=audit_meta(),
    )
    return success(data, "Đã tạo phần khảo sát", status_code=201)


@bp.post("/<int:survey_id>/sections/reorder")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def reorder_sections(survey_id: int):
    actor, _ = actor_and_scope()
    payload = validated_json(reorder_schema)
    return success(
        survey_question_service.reorder_sections(
            survey_id, payload["items"], actor=actor, meta=audit_meta()
        ),
        "Đã sắp xếp các phần",
    )


@sections_bp.put("/<int:section_id>")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def update_section(section_id: int):
    actor, _ = actor_and_scope()
    data = survey_question_service.update_section(
        section_id,
        validated_json(survey_section_update_schema),
        actor=actor,
        meta=audit_meta(),
    )
    return success(data, "Đã cập nhật phần khảo sát")


@sections_bp.delete("/<int:section_id>")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def delete_section(section_id: int):
    actor, _ = actor_and_scope()
    survey_question_service.delete_section(section_id, actor=actor, meta=audit_meta())
    return success(None, "Đã xóa phần khảo sát")


# ----------------------------- Câu hỏi -----------------------------
@bp.get("/<int:survey_id>/questions")
@require_permission(perms.SURVEY_VIEW)
def list_questions(survey_id: int):
    include_inactive = str(request.args.get("include_inactive", "")).lower() in ("1", "true")
    return success(survey_question_service.list_questions(survey_id, include_inactive=include_inactive))


@bp.post("/<int:survey_id>/questions")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def create_question(survey_id: int):
    actor, _ = actor_and_scope()
    data = survey_question_service.create_question(
        survey_id, validated_json(survey_question_create_schema), actor=actor, meta=audit_meta()
    )
    return success(data, "Thêm câu hỏi thành công", status_code=201)


@bp.post("/<int:survey_id>/questions/reorder")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def reorder_questions(survey_id: int):
    actor, _ = actor_and_scope()
    payload = validated_json(reorder_schema)
    data = survey_question_service.reorder_questions(
        survey_id, payload["items"], actor=actor, meta=audit_meta()
    )
    return success(data, "Đã cập nhật thứ tự câu hỏi")


@questions_bp.put("/<int:question_id>")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def update_question(question_id: int):
    actor, _ = actor_and_scope()
    data = survey_question_service.update_question(
        question_id, validated_json(survey_question_update_schema), actor=actor, meta=audit_meta()
    )
    return success(data, "Cập nhật câu hỏi thành công")


@questions_bp.delete("/<int:question_id>")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def delete_question(question_id: int):
    actor, _ = actor_and_scope()
    res = survey_question_service.delete_question(question_id, actor=actor, meta=audit_meta())
    msg = "Đã xóa câu hỏi" if res["hard_deleted"] else "Câu hỏi đã có phản hồi nên được chuyển sang ngừng hoạt động"
    return success(res, msg)


@questions_bp.post("/<int:question_id>/duplicate")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def duplicate_question(question_id: int):
    actor, _ = actor_and_scope()
    data = survey_question_service.duplicate_question(question_id, actor=actor, meta=audit_meta())
    return success(data, "Sao chép câu hỏi thành công", status_code=201)


@questions_bp.post("/<int:question_id>/options")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def create_option(question_id: int):
    actor, _ = actor_and_scope()
    data = survey_question_service.create_option(
        question_id, validated_json(survey_option_create_schema), actor=actor, meta=audit_meta()
    )
    return success(data, "Thêm phương án thành công", status_code=201)


@questions_bp.post("/<int:question_id>/options/reorder")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def reorder_options(question_id: int):
    actor, _ = actor_and_scope()
    payload = validated_json(reorder_schema)
    data = survey_question_service.reorder_options(
        question_id, payload["items"], actor=actor, meta=audit_meta()
    )
    return success(data, "Đã cập nhật thứ tự phương án")


@options_bp.put("/<int:option_id>")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def update_option(option_id: int):
    actor, _ = actor_and_scope()
    data = survey_question_service.update_option(
        option_id, validated_json(survey_option_update_schema), actor=actor, meta=audit_meta()
    )
    return success(data, "Cập nhật phương án thành công")


@options_bp.delete("/<int:option_id>")
@require_permission(perms.SURVEY_MANAGE_QUESTIONS)
def delete_option(option_id: int):
    actor, _ = actor_and_scope()
    res = survey_question_service.delete_option(option_id, actor=actor, meta=audit_meta())
    msg = "Đã xóa phương án" if res["hard_deleted"] else "Phương án đã có phản hồi nên được ẩn thay vì xóa"
    return success(res, msg)


# ----------------------------- Kết quả & thống kê -----------------------------
@bp.get("/<int:survey_id>/responses")
@require_permission(perms.SURVEY_VIEW_STATISTICS)
def list_responses(survey_id: int):
    actor, scope = actor_and_scope()
    res = survey_response_service.list_responses(survey_id, request.args, actor=actor, scope=scope)
    return paginated(res["items"], res["page"], res["page_size"], res["total"])


@bp.get("/<int:survey_id>/statistics")
@require_permission(perms.SURVEY_VIEW_STATISTICS)
def get_statistics(survey_id: int):
    actor, scope = actor_and_scope()
    return success(
        survey_statistics_service.get_statistics(survey_id, request.args, actor=actor, scope=scope)
    )


@bp.get("/<int:survey_id>/export")
@require_permission(perms.SURVEY_EXPORT)
def export_survey(survey_id: int):
    actor, scope = actor_and_scope()
    buf = survey_response_service.export_responses(survey_id, request.args, actor=actor, scope=scope)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"khao-sat-{survey_id}.xlsx",
    )


@bp.get("/<int:survey_id>/statistics/export")
@require_permission(perms.SURVEY_EXPORT)
def export_survey_summary(survey_id: int):
    actor, scope = actor_and_scope()
    buf = survey_statistics_service.export_summary(survey_id, request.args, actor=actor, scope=scope)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"tong-hop-khao-sat-{survey_id}.xlsx",
    )


# ----------------------------- Công khai (người dân) -----------------------------
@public_bp.get("/<string:slug>")
def get_public_survey(slug: str):
    return success(survey_response_service.get_public_survey(slug))


@public_bp.get("/<string:slug>/results")
def get_public_leaderboard(slug: str):
    return success(survey_statistics_service.get_public_leaderboard(slug))


@public_bp.post("/<int:survey_id>/submit")
def submit_response(survey_id: int):
    data, idempotent = survey_response_service.submit_response(
        survey_id, validated_json(survey_submit_schema), meta=audit_meta()
    )
    message = "Đã ghi nhận trước đó, cảm ơn bạn đã đánh giá." if idempotent else "Cảm ơn Anh/Chị đã dành thời gian đánh giá chất lượng phục vụ."
    return success(data, message, status_code=200 if idempotent else 201)
