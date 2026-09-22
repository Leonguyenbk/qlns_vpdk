"""Nghiệp vụ quản lý cuộc khảo sát: CRUD, vòng đời trạng thái, sao chép."""
from __future__ import annotations

from sqlalchemy import func

from ..common.exceptions import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from ..common.utils import clean_str, parse_pagination, slugify_vi
from ..extensions import db
from ..models.organization import OrganizationUnit
from ..models.survey import (
    SURVEY_STATUSES,
    Survey,
    SurveyAnswer,
    SurveyBranchLimit,
    SurveyOption,
    SurveyQuestion,
    SurveyResponse,
    SurveySection,
)
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
        welcome_message=clean_str(data.get("welcome_message")),
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
    if "welcome_message" in data:
        survey.welcome_message = clean_str(data["welcome_message"])
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
    if has_responses and survey.status != "archived":
        raise ConflictError("Khảo sát đã có phản hồi nên không thể xóa (trừ khi đã lưu trữ).")
    old = survey.to_dict()
    if has_responses:
        # Xóa thủ công trước để tránh vướng ràng buộc RESTRICT của
        # survey_answers.question_id khi cascade từ surveys xóa luôn câu hỏi.
        response_ids = db.session.query(SurveyResponse.id).filter(
            SurveyResponse.survey_id == survey.id
        )
        db.session.query(SurveyAnswer).filter(
            SurveyAnswer.response_id.in_(response_ids)
        ).delete(synchronize_session=False)
        db.session.query(SurveyResponse).filter(
            SurveyResponse.survey_id == survey.id
        ).delete(synchronize_session=False)
        db.session.query(SurveyBranchLimit).filter(
            SurveyBranchLimit.survey_id == survey.id
        ).delete(synchronize_session=False)
    db.session.delete(survey)  # cascade: sections/questions -> options
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

    section_ids = {}
    for section in sorted(survey.sections, key=lambda row: row.sort_order):
        copied_section = SurveySection(
            survey_id=new_survey.id,
            title=section.title,
            sort_order=section.sort_order,
        )
        db.session.add(copied_section)
        db.session.flush()
        section_ids[section.id] = copied_section.id

    question_copies = {}
    option_copies = {}
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
            section=q.section,
            section_id=section_ids.get(q.section_id),
            yes_score=q.yes_score,
            no_score=q.no_score,
            scoring_mode=q.scoring_mode,
            max_score=q.max_score,
            zero_score_at=q.zero_score_at,
            trigger_answer=q.trigger_answer,
        )
        db.session.add(new_q)
        db.session.flush()
        question_copies[q.id] = new_q
        for o in sorted(q.options, key=lambda x: x.sort_order):
            if not o.is_active:
                continue
            copied_option = SurveyOption(
                    question_id=new_q.id,
                    option_text=o.option_text,
                    option_value=o.option_value,
                    score=o.score,
                    is_required=o.is_required,
                    sort_order=o.sort_order,
                    is_active=True,
                )
            db.session.add(copied_option)
            db.session.flush()
            option_copies[o.id] = copied_option.id
    for q in survey.questions:
        if q.id not in question_copies or not q.parent_question_id:
            continue
        copied = question_copies[q.id]
        parent_copy = question_copies.get(q.parent_question_id)
        if parent_copy is None:
            raise ValidationError("Câu hỏi phụ đang liên kết câu cha đã tắt; hãy kiểm tra trước khi sao chép.")
        copied.parent_question_id = parent_copy.id
        copied.trigger_option_id = option_copies.get(q.trigger_option_id)

    existing_limits = (
        db.session.query(SurveyBranchLimit).filter(SurveyBranchLimit.survey_id == survey.id).all()
    )
    for limit in existing_limits:
        db.session.add(
            SurveyBranchLimit(
                survey_id=new_survey.id,
                branch_id=limit.branch_id,
                max_responses=limit.max_responses,
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


# ------------------------- Giới hạn theo chi nhánh -------------------------

def get_branch_limits(survey_id: int) -> list[dict]:
    """Toàn bộ chi nhánh đang hoạt động, kèm chỉ tiêu (nếu có đặt) và số lượt
    đã nhận — để màn hình cấu hình hiển thị đủ danh sách cho admin điền."""
    get_survey_or_404(survey_id)
    branches = (
        db.session.query(OrganizationUnit)
        .filter(
            OrganizationUnit.unit_type.in_(("BRANCH", "HEAD_OFFICE")),
            OrganizationUnit.is_active.is_(True),
        )
        .order_by(OrganizationUnit.name)
        .all()
    )
    limits = {
        r.branch_id: r.max_responses
        for r in db.session.query(SurveyBranchLimit).filter(SurveyBranchLimit.survey_id == survey_id)
    }
    counts = dict(
        db.session.query(SurveyResponse.branch_id, func.count(SurveyResponse.id))
        .filter(SurveyResponse.survey_id == survey_id, SurveyResponse.branch_id.isnot(None))
        .group_by(SurveyResponse.branch_id)
        .all()
    )
    return [
        {
            "branch_id": b.id,
            "branch_name": b.name,
            "max_responses": limits.get(b.id),
            "response_count": counts.get(b.id, 0),
        }
        for b in branches
    ]


def set_branch_limits(survey_id: int, items: list[dict], *, actor, meta: dict) -> list[dict]:
    survey = get_survey_or_404(survey_id)
    branch_ids = [it["branch_id"] for it in items]
    valid_branch_ids = {
        b.id
        for b in db.session.query(OrganizationUnit.id)
        .filter(
            OrganizationUnit.id.in_(branch_ids),
            OrganizationUnit.unit_type.in_(("BRANCH", "HEAD_OFFICE")),
        )
        .all()
    }
    existing = {
        r.branch_id: r
        for r in db.session.query(SurveyBranchLimit).filter(SurveyBranchLimit.survey_id == survey_id)
    }
    for item in items:
        branch_id = item["branch_id"]
        if branch_id not in valid_branch_ids:
            raise ValidationError(f"Chi nhánh không hợp lệ: {branch_id}.")
        max_responses = item.get("max_responses")
        if max_responses is not None and max_responses < 1:
            raise ValidationError("Chỉ tiêu số lượt phải lớn hơn 0 (để trống nếu không giới hạn).")
        row = existing.get(branch_id)
        if max_responses is None:
            if row is not None:
                db.session.delete(row)
            continue
        if row is None:
            db.session.add(SurveyBranchLimit(survey_id=survey_id, branch_id=branch_id, max_responses=max_responses))
        else:
            row.max_responses = max_responses
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey.set_branch_limits",
        entity_type="survey",
        entity_id=survey.id,
        new_values={"items": items},
        **meta,
    )
    db.session.commit()
    return get_branch_limits(survey_id)
