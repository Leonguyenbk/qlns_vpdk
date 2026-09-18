"""Nghiệp vụ xem khảo sát công khai và ghi nhận phản hồi (submit).

`submit_response` chỉ `db.session.commit()` một lần duy nhất sau khi toàn bộ câu
trả lời đã được kiểm tra hợp lệ — nếu một câu trả lời lỗi, ngoại lệ được raise
trước khi commit nên toàn bộ response + answers của lượt đó không được lưu
(rollback tự nhiên nhờ session bị hủy ở cuối request, xem `app/errors.py`).
"""
from __future__ import annotations

from sqlalchemy import func

from ..common.exceptions import BusinessRuleError, NotFoundError, ValidationError
from ..common.utils import clean_str, ensure_aware, parse_date, parse_pagination, utcnow, validate_email
from ..exports.survey_export import build_workbook
from ..extensions import db
from ..models import Employee, OrganizationUnit
from ..models.survey import Survey, SurveyAnswer, SurveyBranchLimit, SurveyQuestion, SurveyResponse
from .survey_filters import apply_branch_scope, apply_response_filters
from .survey_service import get_survey_or_404
from .survey_scoring import record_scores


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
        # Điểm là cấu hình quản trị, không công khai cho người trả lời khảo sát.
        data["questions"] = [
            q.to_dict(
                only_active_options=True,
                include_option_scores=False,
                include_scores=False,
            )
            for q in questions
        ]
    # Câu hỏi mặc định "Chi nhánh được khảo sát": danh sách chi nhánh đang hoạt
    # động để trang công khai tự chọn theo mã QR hoặc hiển thị cho người dân chọn.
    # Chi nhánh đã đủ chỉ tiêu (survey_branch_limits) được đánh dấu `full` để
    # trang công khai khoá không cho chọn/nộp thêm.
    branches = (
        db.session.query(OrganizationUnit)
        .filter(OrganizationUnit.unit_type == "BRANCH", OrganizationUnit.is_active.is_(True))
        .order_by(OrganizationUnit.name)
        .all()
    )
    limits = {
        r.branch_id: r.max_responses
        for r in db.session.query(SurveyBranchLimit).filter(SurveyBranchLimit.survey_id == survey.id)
    }
    counts = dict(
        db.session.query(SurveyResponse.branch_id, func.count(SurveyResponse.id))
        .filter(SurveyResponse.survey_id == survey.id, SurveyResponse.branch_id.isnot(None))
        .group_by(SurveyResponse.branch_id)
        .all()
    )
    data["branches"] = [
        {
            "id": b.id,
            "code": b.code,
            "name": b.name,
            "full": b.id in limits and counts.get(b.id, 0) >= limits[b.id],
        }
        for b in branches
    ]
    return data


def _is_answered(item: dict | None, question: SurveyQuestion) -> bool:
    qtype = question.question_type
    if qtype == "multiple_choice" and question.scoring_mode == "deduction":
        return True
    if item is None:
        return False
    if qtype == "single_choice":
        return item.get("option_id") is not None
    if qtype == "multiple_choice":
        return bool(item.get("option_ids") or item.get("option_id") is not None)
    if qtype in ("rating", "number"):
        return item.get("answer_number") is not None
    return bool(clean_str(item.get("answer_text")))


def _condition_satisfied(question: SurveyQuestion, answers_by_question: dict[int, dict]) -> bool:
    if question.parent_question_id is None:
        return True
    parent_item = answers_by_question.get(question.parent_question_id)
    if parent_item is None:
        return False
    if question.trigger_answer is not None:
        return clean_str(parent_item.get("answer_text")) == question.trigger_answer
    if question.trigger_option_id is not None:
        selected = parent_item.get("option_ids") or (
            [parent_item["option_id"]] if parent_item.get("option_id") is not None else []
        )
        return question.trigger_option_id in selected
    return False


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
        option_ids = list(dict.fromkeys(option_ids))
        if not option_ids and question.scoring_mode == "deduction":
            return [{"answer_text": "__none__"}]
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
        .order_by(SurveyQuestion.sort_order, SurveyQuestion.id)
        .all()
    )
    answers_by_question = {a["question_id"]: a for a in data.get("answers", [])}
    active_ids = {q.id for q in questions}
    visible_questions = [
        q for q in questions
        if (q.parent_question_id is None or q.parent_question_id in active_ids)
        and _condition_satisfied(q, answers_by_question)
    ]

    planned: list[tuple[SurveyQuestion, list[dict]]] = []
    for q in visible_questions:
        item = answers_by_question.get(q.id)
        if not _is_answered(item, q):
            if q.is_required:
                raise ValidationError(f"Câu hỏi '{q.question_text}' là bắt buộc.")
            continue
        planned.append((q, _validate_answer(q, item or {"question_id": q.id, "option_ids": []})))

    record_scores(planned, visible_questions)

    branch_id = data.get("branch_id")
    if branch_id is not None and db.session.get(OrganizationUnit, branch_id) is None:
        raise ValidationError("Chi nhánh không hợp lệ.")
    if branch_id is not None:
        limit = (
            db.session.query(SurveyBranchLimit)
            .filter(SurveyBranchLimit.survey_id == survey.id, SurveyBranchLimit.branch_id == branch_id)
            .first()
        )
        if limit is not None:
            current = (
                db.session.query(func.count(SurveyResponse.id))
                .filter(SurveyResponse.survey_id == survey.id, SurveyResponse.branch_id == branch_id)
                .scalar()
                or 0
            )
            if current >= limit.max_responses:
                raise BusinessRuleError(
                    "Chi nhánh này đã đủ số lượt khảo sát, xin cảm ơn Quý khách đã quan tâm."
                )
    employee_id = data.get("employee_id")
    if employee_id is not None and db.session.get(Employee, employee_id) is None:
        raise ValidationError("Cán bộ không hợp lệ.")
    respondent_email = clean_str(data.get("respondent_email"))
    validate_email(respondent_email, "respondent_email")
    respondent_name = clean_str(data.get("respondent_name"))
    respondent_phone = clean_str(data.get("respondent_phone"))
    if not survey.is_anonymous:
        if not respondent_name:
            raise ValidationError("Vui lòng nhập họ và tên.")
        if not respondent_phone:
            raise ValidationError("Vui lòng nhập số điện thoại.")

    response = SurveyResponse(
        survey_id=survey.id,
        branch_id=branch_id,
        service_id=data.get("service_id"),
        counter_id=data.get("counter_id"),
        employee_id=employee_id,
        respondent_name=respondent_name,
        respondent_phone=respondent_phone,
        respondent_email=respondent_email,
        respondent_address=clean_str(data.get("respondent_address")),
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
