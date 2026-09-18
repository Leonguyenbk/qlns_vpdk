"""Nghiệp vụ quản lý câu hỏi và phương án trả lời của khảo sát.

Quy tắc bất biến dữ liệu lịch sử (xem thêm `app/models/survey.py`): khi một câu hỏi
hoặc phương án ĐÃ có câu trả lời, sửa nội dung/điểm sẽ tạo bản ghi mới (is_active=True)
và ẩn bản ghi cũ (is_active=False) thay vì ghi đè — nhờ đó `survey_answers` cũ vẫn
trỏ đúng nội dung tại thời điểm người dân trả lời. Đổi thứ tự, bật/tắt hoạt động,
bắt buộc trả lời... không làm thay đổi ý nghĩa dữ liệu nên luôn được sửa tại chỗ.
"""
from __future__ import annotations

from sqlalchemy import func

from ..common.exceptions import NotFoundError, ValidationError
from ..common.utils import clean_str
from ..extensions import db
from ..models.survey import (
    QUESTION_TYPES,
    QUESTION_TYPES_WITH_OPTIONS,
    SurveyAnswer,
    SurveyOption,
    SurveyQuestion,
)
from .audit_service import record_audit
from .survey_service import get_survey_or_404


def _question_has_responses(question_id: int) -> bool:
    return (
        db.session.query(SurveyAnswer.id).filter(SurveyAnswer.question_id == question_id).first()
        is not None
    )


def _option_has_answers(option_id: int) -> bool:
    return (
        db.session.query(SurveyAnswer.id).filter(SurveyAnswer.option_id == option_id).first()
        is not None
    )


def _get_question_or_404(question_id: int) -> SurveyQuestion:
    q = db.session.get(SurveyQuestion, question_id)
    if q is None:
        raise NotFoundError("Không tìm thấy câu hỏi.")
    return q


def _get_option_or_404(option_id: int) -> SurveyOption:
    o = db.session.get(SurveyOption, option_id)
    if o is None:
        raise NotFoundError("Không tìm thấy phương án trả lời.")
    return o


def _next_question_order(survey_id: int) -> int:
    m = (
        db.session.query(func.max(SurveyQuestion.sort_order))
        .filter(SurveyQuestion.survey_id == survey_id)
        .scalar()
    )
    return (m or 0) + 1


def _clone_question(q: SurveyQuestion) -> SurveyQuestion:
    """Tạo câu hỏi mới sao chép nội dung + phương án đang hoạt động, ẩn câu hỏi cũ."""
    new_q = SurveyQuestion(
        survey_id=q.survey_id,
        question_text=q.question_text,
        question_type=q.question_type,
        is_required=q.is_required,
        is_active=True,
        sort_order=q.sort_order,
        section=q.section,
    )
    db.session.add(new_q)
    db.session.flush()
    for o in q.options:
        if not o.is_active:
            continue
        db.session.add(
            SurveyOption(
                question_id=new_q.id,
                option_text=o.option_text,
                option_value=o.option_value,
                score=o.score,
                sort_order=o.sort_order,
                is_active=True,
            )
        )
    q.is_active = False
    db.session.flush()
    return new_q


def _apply_options(question: SurveyQuestion, items: list[dict]) -> None:
    """Thay thế danh sách phương án theo `items` ([{id?, option_text, option_value?, sort_order?}]).

    Áp dụng bất biến lịch sử theo từng phương án; phương án bị bỏ khỏi danh sách sẽ
    ẩn (nếu đã có câu trả lời) hoặc xóa hẳn (nếu chưa).
    """
    existing = {o.id: o for o in question.options}
    kept_ids: set[int] = set()
    for i, item in enumerate(items, start=1):
        text = clean_str(item.get("option_text"))
        if not text:
            raise ValidationError("Nội dung phương án không được để trống.")
        value = clean_str(item.get("option_value"))
        score = item.get("score")
        order = item.get("sort_order", i)
        oid = item.get("id")
        opt = existing.get(oid) if oid else None
        if opt is not None:
            kept_ids.add(opt.id)
            content_changed = (
                text != opt.option_text or value != opt.option_value or score != opt.score
            )
            if content_changed and _option_has_answers(opt.id):
                db.session.add(
                    SurveyOption(
                        question_id=question.id,
                        option_text=text,
                        option_value=value,
                        score=score,
                        sort_order=order,
                        is_active=True,
                    )
                )
                opt.is_active = False
            else:
                opt.option_text = text
                opt.option_value = value
                opt.score = score
                opt.sort_order = order
        else:
            db.session.add(
                SurveyOption(
                    question_id=question.id,
                    option_text=text,
                    option_value=value,
                    score=score,
                    sort_order=order,
                    is_active=True,
                )
            )
    for oid, opt in existing.items():
        if oid in kept_ids:
            continue
        if _option_has_answers(oid):
            opt.is_active = False
        else:
            db.session.delete(opt)
    db.session.flush()
    active = [o for o in question.options if o.is_active]
    if len(active) < 2:
        raise ValidationError("Câu hỏi cần ít nhất 2 phương án trả lời đang hoạt động.")


# ----------------------------- Câu hỏi -----------------------------
def list_questions(survey_id: int, *, include_inactive: bool = False) -> list[dict]:
    get_survey_or_404(survey_id)
    q = db.session.query(SurveyQuestion).filter(SurveyQuestion.survey_id == survey_id)
    if not include_inactive:
        q = q.filter(SurveyQuestion.is_active.is_(True))
    rows = q.order_by(SurveyQuestion.sort_order).all()
    return [r.to_dict(only_active_options=not include_inactive) for r in rows]


def create_question(survey_id: int, data: dict, *, actor, meta: dict) -> dict:
    get_survey_or_404(survey_id)
    text = clean_str(data.get("question_text"))
    if not text:
        raise ValidationError("Nội dung câu hỏi là bắt buộc.")
    qtype = data.get("question_type")
    if qtype not in QUESTION_TYPES:
        raise ValidationError("Loại câu hỏi không hợp lệ.")
    options_payload = data.get("options") or []
    if qtype in QUESTION_TYPES_WITH_OPTIONS and len(options_payload) < 2:
        raise ValidationError(f"Câu hỏi loại '{qtype}' phải có ít nhất 2 phương án trả lời.")

    question = SurveyQuestion(
        survey_id=survey_id,
        question_text=text,
        question_type=qtype,
        is_required=bool(data.get("is_required", False)),
        is_active=bool(data.get("is_active", True)),
        section=clean_str(data.get("section")),
        sort_order=_next_question_order(survey_id),
    )
    db.session.add(question)
    db.session.flush()
    if qtype in QUESTION_TYPES_WITH_OPTIONS:
        for i, item in enumerate(options_payload, start=1):
            otext = clean_str(item.get("option_text"))
            if not otext:
                raise ValidationError("Nội dung phương án không được để trống.")
            db.session.add(
                SurveyOption(
                    question_id=question.id,
                    option_text=otext,
                    option_value=clean_str(item.get("option_value")),
                    score=item.get("score"),
                    sort_order=i,
                    is_active=True,
                )
            )
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey_question.create",
        entity_type="survey_question",
        entity_id=question.id,
        new_values=question.to_dict(),
        **meta,
    )
    db.session.commit()
    return question.to_dict()


def update_question(question_id: int, data: dict, *, actor, meta: dict) -> dict:
    q = _get_question_or_404(question_id)
    old = q.to_dict()

    new_text = clean_str(data["question_text"]) if "question_text" in data else q.question_text
    if "question_text" in data and not new_text:
        raise ValidationError("Nội dung câu hỏi không được để trống.")
    new_type = data.get("question_type", q.question_type)
    if new_type not in QUESTION_TYPES:
        raise ValidationError("Loại câu hỏi không hợp lệ.")

    content_changed = new_text != q.question_text or new_type != q.question_type
    target = q
    revised_from = None
    if content_changed and _question_has_responses(q.id):
        target = _clone_question(q)
        revised_from = q.id

    target.question_text = new_text
    target.question_type = new_type
    if "is_required" in data:
        target.is_required = bool(data["is_required"])
    if "is_active" in data:
        target.is_active = bool(data["is_active"])
    if "section" in data:
        target.section = clean_str(data["section"])

    options_payload = data.get("options")
    if new_type in QUESTION_TYPES_WITH_OPTIONS:
        if options_payload is not None:
            _apply_options(target, options_payload)
        elif not any(o.is_active for o in target.options):
            raise ValidationError(f"Câu hỏi loại '{new_type}' phải có ít nhất 2 phương án trả lời.")
    else:
        for o in target.options:
            o.is_active = False

    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey_question.update",
        entity_type="survey_question",
        entity_id=target.id,
        old_values=old,
        new_values=target.to_dict(),
        **meta,
    )
    db.session.commit()
    result = target.to_dict()
    result["revised_from_id"] = revised_from
    return result


def delete_question(question_id: int, *, actor, meta: dict) -> dict:
    q = _get_question_or_404(question_id)
    old = q.to_dict()
    if _question_has_responses(q.id):
        q.is_active = False
        hard = False
    else:
        db.session.delete(q)
        hard = True
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey_question.delete" if hard else "survey_question.deactivate",
        entity_type="survey_question",
        entity_id=question_id,
        old_values=old,
        new_values=None if hard else q.to_dict(),
        **meta,
    )
    db.session.commit()
    return {"hard_deleted": hard}


def duplicate_question(question_id: int, *, actor, meta: dict) -> dict:
    q = _get_question_or_404(question_id)
    new_q = SurveyQuestion(
        survey_id=q.survey_id,
        question_text=f"{q.question_text} (Bản sao)",
        question_type=q.question_type,
        is_required=q.is_required,
        is_active=True,
        section=q.section,
        sort_order=_next_question_order(q.survey_id),
    )
    db.session.add(new_q)
    db.session.flush()
    for o in q.options:
        if not o.is_active:
            continue
        db.session.add(
            SurveyOption(
                question_id=new_q.id,
                option_text=o.option_text,
                option_value=o.option_value,
                score=o.score,
                sort_order=o.sort_order,
                is_active=True,
            )
        )
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey_question.duplicate",
        entity_type="survey_question",
        entity_id=new_q.id,
        new_values={"duplicated_from": q.id, **new_q.to_dict()},
        **meta,
    )
    db.session.commit()
    return new_q.to_dict()


def reorder_questions(survey_id: int, items: list[dict], *, actor, meta: dict) -> list[dict]:
    get_survey_or_404(survey_id)
    ids = {
        row[0]
        for row in db.session.query(SurveyQuestion.id)
        .filter(SurveyQuestion.survey_id == survey_id)
        .all()
    }
    for item in items:
        if item["id"] not in ids:
            raise ValidationError("Câu hỏi không thuộc khảo sát này.")
    for item in items:
        qq = db.session.get(SurveyQuestion, item["id"])
        qq.sort_order = item["sort_order"]
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey_question.reorder",
        entity_type="survey",
        entity_id=survey_id,
        new_values={"order": items},
        **meta,
    )
    db.session.commit()
    return list_questions(survey_id, include_inactive=True)


# ----------------------------- Phương án -----------------------------
def create_option(question_id: int, data: dict, *, actor, meta: dict) -> dict:
    q = _get_question_or_404(question_id)
    if q.question_type not in QUESTION_TYPES_WITH_OPTIONS:
        raise ValidationError("Loại câu hỏi này không sử dụng phương án trả lời.")
    text = clean_str(data.get("option_text"))
    if not text:
        raise ValidationError("Nội dung phương án là bắt buộc.")
    max_order = max([o.sort_order for o in q.options], default=0)
    opt = SurveyOption(
        question_id=q.id,
        option_text=text,
        option_value=clean_str(data.get("option_value")),
        score=data.get("score"),
        sort_order=max_order + 1,
        is_active=True,
    )
    db.session.add(opt)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey_option.create",
        entity_type="survey_option",
        entity_id=opt.id,
        new_values=opt.to_dict(),
        **meta,
    )
    db.session.commit()
    return opt.to_dict()


def update_option(option_id: int, data: dict, *, actor, meta: dict) -> dict:
    opt = _get_option_or_404(option_id)
    old = opt.to_dict()

    new_text = clean_str(data["option_text"]) if "option_text" in data else opt.option_text
    if "option_text" in data and not new_text:
        raise ValidationError("Nội dung phương án không được để trống.")
    new_value = clean_str(data["option_value"]) if "option_value" in data else opt.option_value
    new_score = data.get("score", opt.score)

    content_changed = (
        new_text != opt.option_text or new_value != opt.option_value or new_score != opt.score
    )
    target = opt
    revised_from = None
    if content_changed and _option_has_answers(opt.id):
        target = SurveyOption(
            question_id=opt.question_id,
            option_text=new_text,
            option_value=new_value,
            score=new_score,
            sort_order=opt.sort_order,
            is_active=True,
        )
        db.session.add(target)
        opt.is_active = False
        revised_from = opt.id
    else:
        target.option_text = new_text
        target.option_value = new_value
        target.score = new_score

    if "is_active" in data:
        target.is_active = bool(data["is_active"])
    if "sort_order" in data:
        target.sort_order = int(data["sort_order"])

    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey_option.update",
        entity_type="survey_option",
        entity_id=target.id,
        old_values=old,
        new_values=target.to_dict(),
        **meta,
    )
    db.session.commit()
    result = target.to_dict()
    result["revised_from_id"] = revised_from
    return result


def delete_option(option_id: int, *, actor, meta: dict) -> dict:
    opt = _get_option_or_404(option_id)
    q = db.session.get(SurveyQuestion, opt.question_id)
    remaining_active = [o for o in q.options if o.is_active and o.id != opt.id]
    if q.question_type in QUESTION_TYPES_WITH_OPTIONS and len(remaining_active) < 2:
        raise ValidationError("Câu hỏi phải còn ít nhất 2 phương án đang hoạt động.")
    old = opt.to_dict()
    if _option_has_answers(opt.id):
        opt.is_active = False
        hard = False
    else:
        db.session.delete(opt)
        hard = True
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey_option.delete" if hard else "survey_option.deactivate",
        entity_type="survey_option",
        entity_id=option_id,
        old_values=old,
        new_values=None if hard else opt.to_dict(),
        **meta,
    )
    db.session.commit()
    return {"hard_deleted": hard}


def reorder_options(question_id: int, items: list[dict], *, actor, meta: dict) -> list[dict]:
    q = _get_question_or_404(question_id)
    ids = {o.id for o in q.options}
    for item in items:
        if item["id"] not in ids:
            raise ValidationError("Phương án không thuộc câu hỏi này.")
    for item in items:
        opt = db.session.get(SurveyOption, item["id"])
        opt.sort_order = item["sort_order"]
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey_option.reorder",
        entity_type="survey_question",
        entity_id=question_id,
        new_values={"order": items},
        **meta,
    )
    db.session.commit()
    return [o.to_dict() for o in sorted(q.options, key=lambda o: o.sort_order)]
