"""Nghiệp vụ quản lý câu hỏi và phương án trả lời của khảo sát.

Quy tắc bất biến dữ liệu lịch sử (xem thêm `app/models/survey.py`): khi một câu hỏi
hoặc phương án ĐÃ có câu trả lời, sửa nội dung/điểm sẽ tạo bản ghi mới (is_active=True)
và ẩn bản ghi cũ (is_active=False) thay vì ghi đè — nhờ đó `survey_answers` cũ vẫn
trỏ đúng nội dung tại thời điểm người dân trả lời. Đổi thứ tự, bật/tắt hoạt động,
bắt buộc trả lời... không làm thay đổi ý nghĩa dữ liệu nên luôn được sửa tại chỗ.
"""
from __future__ import annotations

from sqlalchemy import func

from ..common.exceptions import ConflictError, NotFoundError, ValidationError
from ..common.utils import clean_str
from ..extensions import db
from ..models.survey import (
    QUESTION_TYPES,
    QUESTION_TYPES_WITH_OPTIONS,
    SurveyAnswer,
    SurveyOption,
    SurveyQuestion,
    SurveySection,
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


def _locked_trigger_branches(question_id: int) -> set[str]:
    """Nhánh Có/Không đang kích hoạt câu hỏi phụ — điểm luôn lấy từ câu hỏi phụ, không cho nhập."""
    rows = db.session.query(SurveyQuestion.trigger_answer).filter(
        SurveyQuestion.parent_question_id == question_id,
        SurveyQuestion.is_active.is_(True),
        SurveyQuestion.trigger_answer.isnot(None),
    ).all()
    return {r[0] for r in rows}


def _is_trigger_option(option_id: int) -> bool:
    """Phương án đang kích hoạt câu hỏi phụ — điểm luôn lấy từ câu hỏi phụ, không cho nhập."""
    return db.session.query(SurveyQuestion.id).filter(
        SurveyQuestion.trigger_option_id == option_id,
        SurveyQuestion.is_active.is_(True),
    ).first() is not None


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


def _get_section_or_404(section_id: int) -> SurveySection:
    section = db.session.get(SurveySection, section_id)
    if section is None:
        raise NotFoundError("Không tìm thấy phần khảo sát.")
    return section


def _section_for_survey(section_id: int | None, survey_id: int) -> SurveySection | None:
    if section_id is None:
        return None
    section = _get_section_or_404(section_id)
    if section.survey_id != survey_id:
        raise ValidationError("Phần không thuộc khảo sát này.")
    return section


def _next_question_order(survey_id: int) -> int:
    m = (
        db.session.query(func.max(SurveyQuestion.sort_order))
        .filter(SurveyQuestion.survey_id == survey_id)
        .scalar()
    )
    return (m or 0) + 1


def _condition_values(
    data: dict,
    *,
    survey_id: int,
    current: SurveyQuestion | None = None,
) -> tuple[int | None, int | None, str | None]:
    parent_id = data.get(
        "parent_question_id", current.parent_question_id if current is not None else None
    )
    trigger_option_id = data.get(
        "trigger_option_id", current.trigger_option_id if current is not None else None
    )
    trigger_answer = data.get(
        "trigger_answer", current.trigger_answer if current is not None else None
    )
    if parent_id is None:
        return None, None, None
    if current is not None and parent_id == current.id:
        raise ValidationError("Câu hỏi không thể là câu hỏi phụ của chính nó.")
    parent = db.session.get(SurveyQuestion, parent_id)
    if parent is None or parent.survey_id != survey_id or not parent.is_active:
        raise ValidationError("Câu hỏi cha không hợp lệ hoặc không thuộc khảo sát này.")
    if parent.parent_question_id is not None:
        raise ValidationError("Hiện tại hệ thống chỉ hỗ trợ câu hỏi phụ một cấp.")
    if current is not None and db.session.query(SurveyQuestion.id).filter(
        SurveyQuestion.parent_question_id == current.id
    ).first():
        raise ValidationError("Câu hỏi đã có câu hỏi phụ không thể chuyển thành câu hỏi phụ.")
    if parent.scoring_mode == "deduction":
        raise ValidationError("Hãy dùng câu trừ điểm làm câu hỏi phụ, không làm câu hỏi cha.")
    if parent.question_type == "yes_no":
        if trigger_answer not in ("yes", "no"):
            raise ValidationError("Câu hỏi phụ cần chọn điều kiện Có hoặc Không.")
        return parent.id, None, trigger_answer
    if parent.question_type in QUESTION_TYPES_WITH_OPTIONS:
        option = db.session.get(SurveyOption, trigger_option_id) if trigger_option_id else None
        if option is None or option.question_id != parent.id or not option.is_active:
            raise ValidationError("Phương án kích hoạt câu hỏi phụ không hợp lệ.")
        return parent.id, option.id, None
    raise ValidationError("Câu hỏi cha phải là loại Có/Không hoặc lựa chọn.")


def _scoring_values(data: dict, *, qtype: str, current: SurveyQuestion | None = None):
    mode = data.get("scoring_mode", current.scoring_mode if current is not None else "standard")
    if qtype != "multiple_choice" and "scoring_mode" not in data:
        mode = "standard"
    max_score = data.get("max_score", current.max_score if current is not None else None)
    zero_score_at = data.get(
        "zero_score_at", current.zero_score_at if current is not None else None
    )
    if mode == "deduction":
        if qtype != "multiple_choice":
            raise ValidationError("Chế độ trừ điểm chỉ áp dụng cho câu chọn nhiều đáp án.")
        if max_score is None or max_score < 0:
            raise ValidationError("Câu trừ điểm cần nhập điểm tối đa.")
        if current is not None and db.session.query(SurveyQuestion.id).filter(
            SurveyQuestion.parent_question_id == current.id
        ).first():
            raise ValidationError("Bỏ liên kết câu hỏi phụ trước khi đổi câu cha sang trừ điểm.")
        return mode, max_score, zero_score_at
    return "standard", None, None


def _validate_deduction_options(mode, options):
    if mode == "deduction" and any((o.get("score") or 0) < 0 for o in options):
        raise ValidationError("Nhập số điểm trừ không âm (ví dụ nhập 3 để trừ 3 điểm).")


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
        section_id=q.section_id,
        yes_score=q.yes_score,
        no_score=q.no_score,
        scoring_mode=q.scoring_mode,
        max_score=q.max_score,
        zero_score_at=q.zero_score_at,
        parent_question_id=q.parent_question_id,
        trigger_option_id=q.trigger_option_id,
        trigger_answer=q.trigger_answer,
    )
    db.session.add(new_q)
    db.session.flush()
    option_id_map: dict[int, int] = {}
    for o in q.options:
        if not o.is_active:
            continue
        new_option = SurveyOption(
            question_id=new_q.id,
            option_text=o.option_text,
            option_value=o.option_value,
            score=o.score,
            sort_order=o.sort_order,
            is_active=True,
        )
        db.session.add(new_option)
        db.session.flush()
        option_id_map[o.id] = new_option.id
    children = db.session.query(SurveyQuestion).filter(
        SurveyQuestion.parent_question_id == q.id,
        SurveyQuestion.is_active.is_(True),
    ).all()
    for child in children:
        child.parent_question_id = new_q.id
        if child.trigger_option_id in option_id_map:
            child.trigger_option_id = option_id_map[child.trigger_option_id]
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
        order = item.get("sort_order", i)
        oid = item.get("id")
        score = None if oid and _is_trigger_option(oid) else item.get("score")
        opt = existing.get(oid) if oid else None
        if opt is not None:
            kept_ids.add(opt.id)
            content_changed = (
                text != opt.option_text or value != opt.option_value or score != opt.score
            )
            if content_changed and _option_has_answers(opt.id):
                new_option = SurveyOption(
                    question_id=question.id,
                    option_text=text,
                    option_value=value,
                    score=score,
                    sort_order=order,
                    is_active=True,
                )
                db.session.add(new_option)
                db.session.flush()
                db.session.query(SurveyQuestion).filter(
                    SurveyQuestion.trigger_option_id == opt.id,
                    SurveyQuestion.is_active.is_(True),
                ).update(
                    {SurveyQuestion.trigger_option_id: new_option.id},
                    synchronize_session=False,
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
        if db.session.query(SurveyQuestion.id).filter(
            SurveyQuestion.trigger_option_id == oid,
            SurveyQuestion.is_active.is_(True),
        ).first():
            raise ConflictError(
                "Phương án đang kích hoạt câu hỏi phụ; hãy đổi điều kiện câu hỏi phụ trước."
            )
        if _option_has_answers(oid):
            opt.is_active = False
        else:
            db.session.delete(opt)
    db.session.flush()
    active = [o for o in question.options if o.is_active]
    if len(active) < 2:
        raise ValidationError("Câu hỏi cần ít nhất 2 phương án trả lời đang hoạt động.")


# ----------------------------- Phần khảo sát -----------------------------
def list_sections(survey_id: int) -> list[dict]:
    get_survey_or_404(survey_id)
    rows = (
        db.session.query(SurveySection)
        .filter(SurveySection.survey_id == survey_id)
        .order_by(SurveySection.sort_order, SurveySection.id)
        .all()
    )
    counts = dict(
        db.session.query(SurveyQuestion.section_id, func.count(SurveyQuestion.id))
        .filter(
            SurveyQuestion.survey_id == survey_id,
            SurveyQuestion.section_id.isnot(None),
        )
        .group_by(SurveyQuestion.section_id)
        .all()
    )
    return [{**row.to_dict(), "question_count": counts.get(row.id, 0)} for row in rows]


def create_section(survey_id: int, data: dict, *, actor, meta: dict) -> dict:
    get_survey_or_404(survey_id)
    title = clean_str(data.get("title"))
    if not title:
        raise ValidationError("Tên phần là bắt buộc.")
    duplicate = (
        db.session.query(SurveySection.id)
        .filter(SurveySection.survey_id == survey_id, SurveySection.title == title)
        .first()
    )
    if duplicate:
        raise ValidationError("Tên phần đã tồn tại trong khảo sát.")
    max_order = (
        db.session.query(func.max(SurveySection.sort_order))
        .filter(SurveySection.survey_id == survey_id)
        .scalar()
        or 0
    )
    section = SurveySection(survey_id=survey_id, title=title, sort_order=max_order + 1)
    db.session.add(section)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey_section.create",
        entity_type="survey_section",
        entity_id=section.id,
        new_values=section.to_dict(),
        **meta,
    )
    db.session.commit()
    return {**section.to_dict(), "question_count": 0}


def update_section(section_id: int, data: dict, *, actor, meta: dict) -> dict:
    section = _get_section_or_404(section_id)
    old = section.to_dict()
    title = clean_str(data.get("title", section.title))
    if not title:
        raise ValidationError("Tên phần là bắt buộc.")
    duplicate = (
        db.session.query(SurveySection.id)
        .filter(
            SurveySection.survey_id == section.survey_id,
            SurveySection.title == title,
            SurveySection.id != section.id,
        )
        .first()
    )
    if duplicate:
        raise ValidationError("Tên phần đã tồn tại trong khảo sát.")
    section.title = title
    db.session.query(SurveyQuestion).filter(
        SurveyQuestion.section_id == section.id
    ).update({SurveyQuestion.section: title}, synchronize_session=False)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey_section.update",
        entity_type="survey_section",
        entity_id=section.id,
        old_values=old,
        new_values=section.to_dict(),
        **meta,
    )
    db.session.commit()
    return section.to_dict()


def delete_section(section_id: int, *, actor, meta: dict) -> None:
    section = _get_section_or_404(section_id)
    if db.session.query(SurveyQuestion.id).filter(SurveyQuestion.section_id == section.id).first():
        raise ConflictError("Phần đang có câu hỏi; hãy chuyển câu hỏi sang phần khác trước.")
    old = section.to_dict()
    db.session.delete(section)
    db.session.flush()
    record_audit(
        user_id=actor.id,
        action="survey_section.delete",
        entity_type="survey_section",
        entity_id=section_id,
        old_values=old,
        **meta,
    )
    db.session.commit()


def reorder_sections(survey_id: int, items: list[dict], *, actor, meta: dict) -> list[dict]:
    get_survey_or_404(survey_id)
    valid_ids = {
        row[0]
        for row in db.session.query(SurveySection.id)
        .filter(SurveySection.survey_id == survey_id)
        .all()
    }
    if any(item["id"] not in valid_ids for item in items):
        raise ValidationError("Phần không thuộc khảo sát này.")
    for item in items:
        db.session.get(SurveySection, item["id"]).sort_order = item["sort_order"]
    record_audit(
        user_id=actor.id,
        action="survey_section.reorder",
        entity_type="survey",
        entity_id=survey_id,
        new_values={"order": items},
        **meta,
    )
    db.session.commit()
    return list_sections(survey_id)


# ----------------------------- Câu hỏi -----------------------------
def order_by_section(query):
    """Thứ tự hiển thị chuẩn: theo thứ tự Phần, rồi thứ tự câu hỏi trong phần.

    Câu chưa thuộc phần nào đứng trước. Dùng chung cho quản trị, xem trước và
    trang công khai để đổi thứ tự Phần có tác dụng ở mọi nơi.
    """
    return query.outerjoin(SurveySection, SurveyQuestion.section_id == SurveySection.id).order_by(
        func.coalesce(SurveySection.sort_order, -1),
        SurveyQuestion.sort_order,
        SurveyQuestion.id,
    )


def list_questions(survey_id: int, *, include_inactive: bool = False) -> list[dict]:
    get_survey_or_404(survey_id)
    q = db.session.query(SurveyQuestion).filter(SurveyQuestion.survey_id == survey_id)
    if not include_inactive:
        q = q.filter(SurveyQuestion.is_active.is_(True))
    rows = order_by_section(q).all()
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

    section_record = _section_for_survey(data.get("section_id"), survey_id)
    scoring_mode, max_score, zero_score_at = _scoring_values(data, qtype=qtype)
    _validate_deduction_options(scoring_mode, options_payload)
    parent_id, trigger_option_id, trigger_answer = _condition_values(
        data, survey_id=survey_id
    )
    question = SurveyQuestion(
        survey_id=survey_id,
        question_text=text,
        question_type=qtype,
        is_required=bool(data.get("is_required", False)),
        is_active=bool(data.get("is_active", True)),
        section=section_record.title if section_record else clean_str(data.get("section")),
        section_id=section_record.id if section_record else None,
        yes_score=data.get("yes_score") if qtype == "yes_no" else None,
        no_score=data.get("no_score") if qtype == "yes_no" else None,
        scoring_mode=scoring_mode,
        max_score=max_score,
        zero_score_at=zero_score_at,
        parent_question_id=parent_id,
        trigger_option_id=trigger_option_id,
        trigger_answer=trigger_answer,
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
    if new_type != q.question_type and db.session.query(SurveyQuestion.id).filter(
        SurveyQuestion.parent_question_id == q.id,
        SurveyQuestion.is_active.is_(True),
    ).first():
        raise ConflictError(
            "Câu hỏi đang có câu hỏi phụ; hãy bỏ liên kết câu hỏi phụ trước khi đổi loại."
        )
    if data.get("is_active") is False and db.session.query(SurveyQuestion.id).filter(
        SurveyQuestion.parent_question_id == q.id,
        SurveyQuestion.is_active.is_(True),
    ).first():
        raise ConflictError(
            "Câu hỏi đang có câu hỏi phụ; hãy bỏ liên kết câu hỏi phụ trước khi tắt."
        )

    new_yes_score = data.get("yes_score", q.yes_score)
    new_no_score = data.get("no_score", q.no_score)
    if new_type != "yes_no":
        new_yes_score = None
        new_no_score = None
    else:
        locked_branches = _locked_trigger_branches(q.id)
        if "yes" in locked_branches:
            new_yes_score = None
        if "no" in locked_branches:
            new_no_score = None
    new_scoring_mode, new_max_score, new_zero_score_at = _scoring_values(
        data, qtype=new_type, current=q
    )
    new_parent_id, new_trigger_option_id, new_trigger_answer = _condition_values(
        data, survey_id=q.survey_id, current=q
    )
    content_changed = (
        new_text != q.question_text
        or new_type != q.question_type
        or new_yes_score != q.yes_score
        or new_no_score != q.no_score
        or new_scoring_mode != q.scoring_mode
        or new_max_score != q.max_score
        or new_zero_score_at != q.zero_score_at
        or new_parent_id != q.parent_question_id
        or new_trigger_option_id != q.trigger_option_id
        or new_trigger_answer != q.trigger_answer
    )
    target = q
    revised_from = None
    if content_changed and _question_has_responses(q.id):
        target = _clone_question(q)
        revised_from = q.id

    target.question_text = new_text
    target.question_type = new_type
    target.yes_score = new_yes_score
    target.no_score = new_no_score
    target.scoring_mode = new_scoring_mode
    target.max_score = new_max_score
    target.zero_score_at = new_zero_score_at
    target.parent_question_id = new_parent_id
    target.trigger_option_id = new_trigger_option_id
    target.trigger_answer = new_trigger_answer
    if "is_required" in data:
        target.is_required = bool(data["is_required"])
    if "is_active" in data:
        target.is_active = bool(data["is_active"])
    if "section_id" in data:
        section_record = _section_for_survey(data["section_id"], target.survey_id)
        target.section_id = section_record.id if section_record else None
        target.section = section_record.title if section_record else None
    elif "section" in data:
        target.section = clean_str(data["section"])
        target.section_id = None

    options_payload = data.get("options")
    _validate_deduction_options(
        new_scoring_mode,
        options_payload if options_payload is not None else [o.to_dict() for o in target.options if o.is_active],
    )
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
    if db.session.query(SurveyQuestion.id).filter(
        SurveyQuestion.parent_question_id == q.id,
        SurveyQuestion.is_active.is_(True),
    ).first():
        raise ConflictError(
            "Câu hỏi đang có câu hỏi phụ; hãy bỏ liên kết câu hỏi phụ trước khi xóa."
        )
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
        section_id=q.section_id,
        yes_score=q.yes_score,
        no_score=q.no_score,
        scoring_mode=q.scoring_mode,
        max_score=q.max_score,
        zero_score_at=q.zero_score_at,
        parent_question_id=q.parent_question_id,
        trigger_option_id=q.trigger_option_id,
        trigger_answer=q.trigger_answer,
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
    _validate_deduction_options(q.scoring_mode, [data])
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
    new_score = None if _is_trigger_option(opt.id) else data.get("score", opt.score)
    _validate_deduction_options(opt.question.scoring_mode, [{"score": new_score}])
    if data.get("is_active") is False and db.session.query(SurveyQuestion.id).filter(
        SurveyQuestion.trigger_option_id == opt.id,
    ).first():
        raise ConflictError("Bỏ liên kết câu hỏi phụ trước khi tắt phương án kích hoạt.")

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

    if target is not opt:
        db.session.flush()
        db.session.query(SurveyQuestion).filter(
            SurveyQuestion.trigger_option_id == opt.id,
            SurveyQuestion.is_active.is_(True),
        ).update({SurveyQuestion.trigger_option_id: target.id}, synchronize_session=False)

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
    if db.session.query(SurveyQuestion.id).filter(
        SurveyQuestion.trigger_option_id == opt.id,
        SurveyQuestion.is_active.is_(True),
    ).first():
        raise ConflictError(
            "Phương án đang kích hoạt câu hỏi phụ; hãy đổi điều kiện câu hỏi phụ trước khi xóa."
        )
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
