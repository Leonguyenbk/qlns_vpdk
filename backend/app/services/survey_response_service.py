"""Nghiệp vụ xem khảo sát công khai và ghi nhận phản hồi (submit).

`submit_response` chỉ `db.session.commit()` một lần duy nhất sau khi toàn bộ câu
trả lời đã được kiểm tra hợp lệ — nếu một câu trả lời lỗi, ngoại lệ được raise
trước khi commit nên toàn bộ response + answers của lượt đó không được lưu
(rollback tự nhiên nhờ session bị hủy ở cuối request, xem `app/errors.py`).
"""
from __future__ import annotations

from ..common.exceptions import BusinessRuleError, NotFoundError, ValidationError
from ..common.utils import clean_str, ensure_aware, parse_date, parse_pagination, utcnow
from ..exports.survey_export import build_workbook
from ..extensions import db
from ..models import Employee, OrganizationUnit
from ..models.survey import Survey, SurveyAnswer, SurveyQuestion, SurveyResponse
from .survey_filters import apply_branch_scope, apply_response_filters
from .survey_service import get_survey_or_404


def _assert_submittable(survey: Survey) -> None:
    if survey.status != "active":
        raise BusinessRuleError("Khảo sát hiện không nhận phản hồi.")
    now = utcnow()
    if survey.start_at and ensure_aware(survey.start_at) > now:
        raise BusinessRuleError("Khảo sát chưa đến thời gian bắt đầu.")
    if survey.end_at and ensure_aware(survey.end_at) < now:
        raise BusinessRuleError("Khảo sát đã kết thúc.")


def get_public_survey(slug: str) -> dict:
    survey = db.session.query(Survey).filter(Survey.slug == slug).first()
    if survey is None:
        raise NotFoundError("Không tìm thấy khảo sát.")
    try:
        _assert_submittable(survey)
        available, reason = True, None
    except BusinessRuleError as exc:
        available, reason = False, exc.message

    data = survey.to_dict()
    data["available"] = available
    data["unavailable_reason"] = reason
    data["questions"] = []
    if available:
        questions = (
            db.session.query(SurveyQuestion)
            .filter(SurveyQuestion.survey_id == survey.id, SurveyQuestion.is_active.is_(True))
            .order_by(SurveyQuestion.sort_order)
            .all()
        )
        data["questions"] = [q.to_dict(only_active_options=True) for q in questions]
    return data


def _is_answered(item: dict | None, qtype: str) -> bool:
    if item is None:
        return False
    if qtype == "single_choice":
        return item.get("option_id") is not None
    if qtype == "multiple_choice":
        return bool(item.get("option_ids") or item.get("option_id") is not None)
    if qtype in ("rating", "number"):
        return item.get("answer_number") is not None
    return bool(clean_str(item.get("answer_text")))


def _validate_answer(question: SurveyQuestion, item: dict) -> list[dict]:
    qtype = question.question_type
    label = question.question_text

    if qtype == "single_choice":
        option_id = item.get("option_id")
        opt = next((o for o in question.options if o.id == option_id and o.is_active), None)
        if opt is None:
            raise ValidationError(f"Phương án không hợp lệ cho câu hỏi '{label}'.")
        return [{"option_id": opt.id}]

    if qtype == "multiple_choice":
        option_ids = item.get("option_ids") or (
            [item["option_id"]] if item.get("option_id") is not None else []
        )
        if not option_ids:
            raise ValidationError(f"Câu hỏi '{label}' cần chọn ít nhất một phương án.")
        valid_ids = {o.id for o in question.options if o.is_active}
        rows = []
        for oid in option_ids:
            if oid not in valid_ids:
                raise ValidationError(f"Phương án không hợp lệ cho câu hỏi '{label}'.")
            rows.append({"option_id": oid})
        return rows

    if qtype == "yes_no":
        text = clean_str(item.get("answer_text"))
        if text not in ("yes", "no"):
            raise ValidationError(f"Câu hỏi '{label}' cần trả lời Có hoặc Không.")
        return [{"answer_text": text}]

    if qtype == "rating":
        try:
            num = float(item.get("answer_number"))
        except (TypeError, ValueError):
            raise ValidationError(f"Mức đánh giá cho câu hỏi '{label}' không hợp lệ.")
        if num < 1 or num > 5:
            raise ValidationError(f"Mức đánh giá cho câu hỏi '{label}' phải từ 1 đến 5.")
        return [{"answer_number": num}]

    if qtype == "number":
        try:
            num = float(item.get("answer_number"))
        except (TypeError, ValueError):
            raise ValidationError(f"Giá trị cho câu hỏi '{label}' phải là số.")
        return [{"answer_number": num}]

    if qtype == "date":
        d = parse_date(item.get("answer_text"), "answer_text")
        if d is None:
            raise ValidationError(f"Câu hỏi '{label}' cần chọn ngày.")
        return [{"answer_text": d.isoformat()}]

    # text, textarea
    text = clean_str(item.get("answer_text"))
    if not text:
        raise ValidationError(f"Câu hỏi '{label}' không được để trống.")
    return [{"answer_text": text}]


def submit_response(survey_id: int, data: dict, *, meta: dict) -> tuple[dict, bool]:
    survey = get_survey_or_404(survey_id)
    _assert_submittable(survey)

    client_token = clean_str(data.get("client_token"))
    if client_token:
        existing = (
            db.session.query(SurveyResponse)
            .filter(SurveyResponse.survey_id == survey.id, SurveyResponse.client_token == client_token)
            .first()
        )
        if existing:
            return existing.to_dict(include_answers=True), True

    questions = (
        db.session.query(SurveyQuestion)
        .filter(SurveyQuestion.survey_id == survey.id, SurveyQuestion.is_active.is_(True))
        .all()
    )
    answers_by_question = {a["question_id"]: a for a in data.get("answers", [])}

    planned: list[tuple[SurveyQuestion, list[dict]]] = []
    for q in questions:
        item = answers_by_question.get(q.id)
        if not _is_answered(item, q.question_type):
            if q.is_required:
                raise ValidationError(f"Câu hỏi '{q.question_text}' là bắt buộc.")
            continue
        planned.append((q, _validate_answer(q, item)))

    branch_id = data.get("branch_id")
    if branch_id is not None and db.session.get(OrganizationUnit, branch_id) is None:
        raise ValidationError("Chi nhánh không hợp lệ.")
    employee_id = data.get("employee_id")
    if employee_id is not None and db.session.get(Employee, employee_id) is None:
        raise ValidationError("Cán bộ không hợp lệ.")

    response = SurveyResponse(
        survey_id=survey.id,
        branch_id=branch_id,
        service_id=data.get("service_id"),
        counter_id=data.get("counter_id"),
        employee_id=employee_id,
        respondent_name=clean_str(data.get("respondent_name")),
        respondent_phone=clean_str(data.get("respondent_phone")),
        ip_address=meta.get("ip_address"),
        user_agent=(meta.get("user_agent") or "")[:255] or None,
        client_token=client_token,
        submitted_at=utcnow(),
    )
    db.session.add(response)
    db.session.flush()

    for question, rows in planned:
        for row in rows:
            db.session.add(SurveyAnswer(response_id=response.id, question_id=question.id, **row))

    db.session.flush()
    db.session.commit()
    return response.to_dict(include_answers=True), False


def list_responses(survey_id: int, args, *, actor, scope) -> dict:
    get_survey_or_404(survey_id)
    page, page_size = parse_pagination(args)
    q = db.session.query(SurveyResponse).filter(SurveyResponse.survey_id == survey_id)
    q = apply_response_filters(q, args, response_model=SurveyResponse)
    q = apply_branch_scope(q, actor=actor, scope=scope, column=SurveyResponse.branch_id)
    total = q.count()
    rows = (
        q.order_by(SurveyResponse.submitted_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [r.to_dict(include_answers=True) for r in rows]
    return {"items": items, "page": page, "page_size": page_size, "total": total}


def export_responses(survey_id: int, args, *, actor, scope):
    survey = get_survey_or_404(survey_id)
    q = db.session.query(SurveyResponse).filter(SurveyResponse.survey_id == survey_id)
    q = apply_response_filters(q, args, response_model=SurveyResponse)
    q = apply_branch_scope(q, actor=actor, scope=scope, column=SurveyResponse.branch_id)
    responses = q.order_by(SurveyResponse.submitted_at.asc()).all()
    return build_workbook(survey, responses)
