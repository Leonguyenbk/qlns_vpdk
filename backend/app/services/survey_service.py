"""Nghiệp vụ quản lý cuộc khảo sát: CRUD, vòng đời trạng thái, sao chép."""
from __future__ import annotations

from sqlalchemy import func

from ..common.exceptions import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from ..common.utils import clean_str, parse_pagination, slugify_vi
from ..extensions import db
from ..models.survey import SURVEY_STATUSES, Survey, SurveyOption, SurveyQuestion, SurveyResponse
from .audit_service import record_audit

# Chuyển trạng thái hợp lệ. "closed" là gần như chung cuộc; "archived" chỉ để ẩn
# khỏi danh sách mặc định, vẫn có thể đưa lại "closed" để xem/khôi phục.
_TRANSITIONS = {
    "draft": {"active"},
    "active": {"paused", "closed"},
    "paused": {"active", "closed"},
    "closed": {"archived"},
    "archived": {"closed"},
}


def _unique_slug(base_slug: str, *, exclude_id: int | None = None) -> str:
    slug = base_slug
    i = 2
    while True:
        q = db.session.query(Survey.id).filter(Survey.slug == slug)
        if exclude_id:
            q = q.filter(Survey.id != exclude_id)
        if not q.first():
            return slug
        slug = f"{base_slug}-{i}"
        i += 1


def _counts_for(survey_ids: list[int]) -> dict[int, dict]:
    if not survey_ids:
        return {}
    q_counts = dict(
        db.session.query(SurveyQuestion.survey_id, func.count(SurveyQuestion.id))
        .filter(SurveyQuestion.survey_id.in_(survey_ids), SurveyQuestion.is_active.is_(True))
        .group_by(SurveyQuestion.survey_id)
        .all()
    )
    r_counts = dict(
        db.session.query(SurveyResponse.survey_id, func.count(SurveyResponse.id))
        .filter(SurveyResponse.survey_id.in_(survey_ids))
        .group_by(SurveyResponse.survey_id)
        .all()
    )
    return {
        sid: {"question_count": q_counts.get(sid, 0), "response_count": r_counts.get(sid, 0)}
        for sid in survey_ids
    }


def get_survey_or_404(survey_id: int) -> Survey:
    survey = db.session.get(Survey, survey_id)
    if survey is None:
        raise NotFoundError("Không tìm thấy khảo sát.")
    return survey


def list_surveys(args) -> dict:
    page, page_size = parse_pagination(args)
    q = db.session.query(Survey)
    status = clean_str(args.get("status"))
    if status:
        if status not in SURVEY_STATUSES:
            raise ValidationError("Trạng thái lọc không hợp lệ.")
        q = q.filter(Survey.status == status)
    keyword = clean_str(args.get("keyword") or args.get("q"))
    if keyword:
        q = q.filter(Survey.title.ilike(f"%{keyword}%"))
    total = q.count()
    rows = (
        q.order_by(Survey.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    counts = _counts_for([s.id for s in rows])
    items = [s.to_dict(counts=counts.get(s.id)) for s in rows]
    return {"items": items, "page": page, "page_size": page_size, "total": total}


def get_survey(survey_id: int) -> dict:
    survey = get_survey_or_404(survey_id)
    data = survey.to_dict(counts=_counts_for([survey.id]).get(survey.id))
    return data


def create_survey(data: dict, *, actor, meta: dict) -> dict:
    title = clean_str(data.get("title"))
    if not title:
        raise ValidationError("Tên khảo sát là bắt buộc.")
    slug = _unique_slug(slugify_vi(title))
    survey = Survey(
        title=title,
        slug=slug,
        description=clean_str(data.get("description")),
        is_anonymous=bool(data.get("is_anonymous", True)),
        start_at=data.get("start_at"),
        end_at=data.get("end_at"),
        status="draft",
        created_by=actor.id,
    )
    db.session.add(survey)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey.create",
        entity_type="survey",
        entity_id=survey.id,
        new_values=survey.to_dict(),
        **meta,
    )
    db.session.commit()
    return survey.to_dict()


def update_survey(survey_id: int, data: dict, *, actor, meta: dict) -> dict:
    survey = get_survey_or_404(survey_id)
    if survey.status in ("closed", "archived"):
        raise BusinessRuleError("Khảo sát đã đóng/lưu trữ, không thể sửa thông tin.")
    old = survey.to_dict()
    if "title" in data:
        title = clean_str(data["title"])
        if not title:
            raise ValidationError("Tên khảo sát là bắt buộc.")
        survey.title = title
    if "description" in data:
        survey.description = clean_str(data["description"])
    if "is_anonymous" in data:
        survey.is_anonymous = bool(data["is_anonymous"])
    if "start_at" in data:
        survey.start_at = data["start_at"]
    if "end_at" in data:
        survey.end_at = data["end_at"]
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey.update",
        entity_type="survey",
        entity_id=survey.id,
        old_values=old,
        new_values=survey.to_dict(),
        **meta,
    )
    db.session.commit()
    return survey.to_dict()


def change_status(survey_id: int, new_status: str, *, actor, meta: dict) -> dict:
    survey = get_survey_or_404(survey_id)
    if new_status not in SURVEY_STATUSES:
        raise ValidationError("Trạng thái không hợp lệ.")
    allowed = _TRANSITIONS.get(survey.status, set())
    if new_status not in allowed:
        raise BusinessRuleError(
            f"Không thể chuyển khảo sát từ trạng thái '{survey.status}' sang '{new_status}'."
        )
    if new_status == "active" and survey.status == "draft":
        active_questions = (
            db.session.query(SurveyQuestion.id)
            .filter(SurveyQuestion.survey_id == survey.id, SurveyQuestion.is_active.is_(True))
            .first()
        )
        if not active_questions:
            raise ValidationError("Khảo sát cần ít nhất một câu hỏi đang hoạt động trước khi xuất bản.")
    old = survey.to_dict()
    survey.status = new_status
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action=f"survey.status.{new_status}",
        entity_type="survey",
        entity_id=survey.id,
        old_values=old,
        new_values=survey.to_dict(),
        **meta,
    )
    db.session.commit()
    return survey.to_dict()


def delete_survey(survey_id: int, *, actor, meta: dict) -> dict:
    survey = get_survey_or_404(survey_id)
    has_responses = (
        db.session.query(SurveyResponse.id).filter(SurveyResponse.survey_id == survey.id).first()
        is not None
    )
    if has_responses:
        raise ConflictError("Khảo sát đã có phản hồi nên không thể xóa.")
    old = survey.to_dict()
    db.session.delete(survey)  # cascade: questions -> options
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey.delete",
        entity_type="survey",
        entity_id=survey_id,
        old_values=old,
        **meta,
    )
    db.session.commit()
    return {"deleted": True}


def duplicate_survey(survey_id: int, *, actor, meta: dict) -> dict:
    survey = get_survey_or_404(survey_id)
    new_survey = Survey(
        title=f"{survey.title} (Bản sao)",
        slug=_unique_slug(slugify_vi(f"{survey.title}-ban-sao")),
        description=survey.description,
        is_anonymous=survey.is_anonymous,
        start_at=None,
        end_at=None,
        status="draft",
        created_by=actor.id,
    )
    db.session.add(new_survey)
    db.session.flush()

    for q in sorted(survey.questions, key=lambda x: x.sort_order):
        if not q.is_active:
            continue
        new_q = SurveyQuestion(
            survey_id=new_survey.id,
            question_text=q.question_text,
            question_type=q.question_type,
            is_required=q.is_required,
            is_active=True,
            sort_order=q.sort_order,
        )
        db.session.add(new_q)
        db.session.flush()
        for o in sorted(q.options, key=lambda x: x.sort_order):
            if not o.is_active:
                continue
            db.session.add(
                SurveyOption(
                    question_id=new_q.id,
                    option_text=o.option_text,
                    option_value=o.option_value,
                    sort_order=o.sort_order,
                    is_active=True,
                )
            )
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey.duplicate",
        entity_type="survey",
        entity_id=new_survey.id,
        new_values={"duplicated_from": survey.id, **new_survey.to_dict()},
        **meta,
    )
    db.session.commit()
    return new_survey.to_dict()
