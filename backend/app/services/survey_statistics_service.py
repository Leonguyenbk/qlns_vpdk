"""Nghiệp vụ thống kê khảo sát: tổng quan, theo câu hỏi, theo thời gian, theo chi nhánh."""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func

from ..extensions import db
from ..models import OrganizationUnit
from ..models.survey import SurveyAnswer, SurveyQuestion, SurveyResponse
from .survey_filters import apply_branch_scope, apply_response_filters
from .survey_question_service import list_questions
from .survey_service import get_survey_or_404

RATING_LABELS = {
    5: "Rất hài lòng",
    4: "Hài lòng",
    3: "Bình thường",
    2: "Không hài lòng",
    1: "Rất không hài lòng",
}

# Khảo sát thực tế thường dùng câu hỏi "single_choice" với 5 phương án đúng nhãn
# mức độ hài lòng thay vì kiểu "rating" — coi các câu hỏi như vậy tương đương
# rating khi tính điểm trung bình/tỷ lệ hài lòng tổng quan và theo chi nhánh.
_SATISFACTION_LEVEL_BY_LABEL = {label.lower(): level for level, label in RATING_LABELS.items()}


def _normalize_label(text: str | None) -> str:
    return (text or "").strip().lower()


def _satisfaction_sources(survey_id: int) -> tuple[list[int], dict[int, int]]:
    """Trả về (id câu hỏi kiểu rating, {option_id: mức 1-5}) cho các câu hỏi
    single_choice có ĐÚNG 5 phương án đang hoạt động, khớp trọn vẹn 5 nhãn hài
    lòng (không thừa, không thiếu) — tránh nhầm với câu hỏi 2 lựa chọn tình cờ
    trùng chữ "Hài lòng/Không hài lòng" nhưng không phải thang 5 mức."""
    questions = (
        db.session.query(SurveyQuestion)
        .filter(SurveyQuestion.survey_id == survey_id, SurveyQuestion.is_active.is_(True))
        .all()
    )
    rating_question_ids: list[int] = []
    option_level_map: dict[int, int] = {}
    for q in questions:
        if q.question_type == "rating":
            rating_question_ids.append(q.id)
        elif q.question_type == "single_choice":
            active_options = [o for o in q.options if o.is_active]
            levels = {
                _SATISFACTION_LEVEL_BY_LABEL.get(_normalize_label(o.option_text))
                for o in active_options
            }
            if levels == set(RATING_LABELS):
                for o in active_options:
                    option_level_map[o.id] = _SATISFACTION_LEVEL_BY_LABEL[
                        _normalize_label(o.option_text)
                    ]
    return rating_question_ids, option_level_map


def _satisfaction_values_by_response(
    response_ids: list[int], rating_question_ids: list[int], option_level_map: dict[int, int]
) -> dict[int, list[int]]:
    """{response_id: [mức 1-5, ...]} gộp từ câu hỏi rating thật + single_choice hài lòng."""
    values_by_response: dict[int, list[int]] = defaultdict(list)
    if rating_question_ids:
        rows = (
            db.session.query(SurveyAnswer.response_id, SurveyAnswer.answer_number)
            .filter(
                SurveyAnswer.response_id.in_(response_ids),
                SurveyAnswer.question_id.in_(rating_question_ids),
            )
            .all()
        )
        for rid, value in rows:
            if value is not None:
                values_by_response[rid].append(round(value))
    if option_level_map:
        rows = (
            db.session.query(SurveyAnswer.response_id, SurveyAnswer.option_id)
            .filter(
                SurveyAnswer.response_id.in_(response_ids),
                SurveyAnswer.option_id.in_(option_level_map.keys()),
            )
            .all()
        )
        for rid, option_id in rows:
            values_by_response[rid].append(option_level_map[option_id])
    return values_by_response


def _scoped_response_ids(survey_id: int, args, *, actor, scope) -> list[int]:
    q = db.session.query(SurveyResponse.id).filter(SurveyResponse.survey_id == survey_id)
    q = apply_response_filters(q, args, response_model=SurveyResponse)
    q = apply_branch_scope(q, actor=actor, scope=scope, column=SurveyResponse.branch_id)
    return [r[0] for r in q.all()]


def get_statistics(survey_id: int, args, *, actor, scope) -> dict:
    get_survey_or_404(survey_id)
    response_ids = _scoped_response_ids(survey_id, args, actor=actor, scope=scope)
    rating_qids, option_level_map = _satisfaction_sources(survey_id)
    values_by_response = _satisfaction_values_by_response(response_ids, rating_qids, option_level_map)
    return {
        "overview": _overview(survey_id, response_ids, values_by_response),
        "by_question": _by_question(survey_id, response_ids),
        "time_series": _time_series(response_ids),
        "by_branch": _by_branch(response_ids, values_by_response),
    }


def _overview(
    survey_id: int, response_ids: list[int], values_by_response: dict[int, list[int]]
) -> dict:
    total_responses = len(response_ids)
    if not total_responses:
        return {
            "total_responses": 0,
            "completion_rate": 0,
            "average_score": None,
            "satisfaction_rate": 0,
            "dissatisfaction_rate": 0,
            "rating_breakdown": [
                {"level": lvl, "label": lbl, "count": 0, "percentage": 0}
                for lvl, lbl in sorted(RATING_LABELS.items(), reverse=True)
            ],
        }

    required_count = (
        db.session.query(func.count(SurveyQuestion.id))
        .filter(
            SurveyQuestion.survey_id == survey_id,
            SurveyQuestion.is_active.is_(True),
            SurveyQuestion.is_required.is_(True),
        )
        .scalar()
        or 0
    )
    if required_count:
        rows = (
            db.session.query(
                SurveyAnswer.response_id, func.count(func.distinct(SurveyAnswer.question_id))
            )
            .join(SurveyQuestion, SurveyQuestion.id == SurveyAnswer.question_id)
            .filter(
                SurveyAnswer.response_id.in_(response_ids),
                SurveyQuestion.is_required.is_(True),
            )
            .group_by(SurveyAnswer.response_id)
            .all()
        )
        complete = sum(1 for _, c in rows if c >= required_count)
        completion_rate = round(complete / total_responses * 100, 1)
    else:
        completion_rate = 100.0

    rating_values = [v for rid in response_ids for v in values_by_response.get(rid, [])]
    total_ratings = len(rating_values)
    satisfied = sum(1 for v in rating_values if v >= 4)
    dissatisfied = sum(1 for v in rating_values if v <= 2)
    breakdown = [
        {
            "level": level,
            "label": RATING_LABELS[level],
            "count": (c := sum(1 for v in rating_values if v == level)),
            "percentage": round(c / total_ratings * 100, 1) if total_ratings else 0,
        }
        for level in (5, 4, 3, 2, 1)
    ]

    return {
        "total_responses": total_responses,
        "completion_rate": completion_rate,
        "average_score": round(sum(rating_values) / total_ratings, 2) if total_ratings else None,
        "satisfaction_rate": round(satisfied / total_ratings * 100, 1) if total_ratings else 0,
        "dissatisfaction_rate": round(dissatisfied / total_ratings * 100, 1) if total_ratings else 0,
        "rating_breakdown": breakdown,
    }


def _empty_question_stats(qtype: str) -> dict:
    if qtype in ("single_choice", "multiple_choice"):
        return {"type": "choice", "total_respondents": 0, "options": []}
    if qtype == "yes_no":
        return {
            "type": "yes_no", "total_respondents": 0,
            "yes_count": 0, "no_count": 0, "yes_percentage": 0, "no_percentage": 0,
        }
    if qtype == "rating":
        return {"type": "rating", "total_respondents": 0, "average": None, "breakdown": []}
    if qtype == "number":
        return {"type": "number", "total_respondents": 0, "average": None, "min": None, "max": None}
    return {"type": "open_text", "total_respondents": 0, "samples": []}


def _question_stats(question: dict, response_ids: list[int]) -> dict:
    qtype = question["question_type"]
    qid = question["id"]

    if qtype in ("single_choice", "multiple_choice"):
        total_respondents = (
            db.session.query(func.count(func.distinct(SurveyAnswer.response_id)))
            .filter(SurveyAnswer.question_id == qid, SurveyAnswer.response_id.in_(response_ids))
            .scalar()
            or 0
        )
        counts = dict(
            db.session.query(SurveyAnswer.option_id, func.count(SurveyAnswer.id))
            .filter(SurveyAnswer.question_id == qid, SurveyAnswer.response_id.in_(response_ids))
            .group_by(SurveyAnswer.option_id)
            .all()
        )
        options = [
            {
                "option_id": opt["id"],
                "option_text": opt["option_text"],
                "count": counts.get(opt["id"], 0),
                "percentage": round(counts.get(opt["id"], 0) / total_respondents * 100, 1)
                if total_respondents
                else 0,
            }
            for opt in question["options"]
        ]
        return {"type": "choice", "total_respondents": total_respondents, "options": options}

    if qtype == "yes_no":
        counts = dict(
            db.session.query(SurveyAnswer.answer_text, func.count(SurveyAnswer.id))
            .filter(SurveyAnswer.question_id == qid, SurveyAnswer.response_id.in_(response_ids))
            .group_by(SurveyAnswer.answer_text)
            .all()
        )
        yes, no = counts.get("yes", 0), counts.get("no", 0)
        total = yes + no
        return {
            "type": "yes_no", "total_respondents": total,
            "yes_count": yes, "no_count": no,
            "yes_percentage": round(yes / total * 100, 1) if total else 0,
            "no_percentage": round(no / total * 100, 1) if total else 0,
        }

    if qtype == "rating":
        values = [
            round(v[0])
            for v in db.session.query(SurveyAnswer.answer_number)
            .filter(SurveyAnswer.question_id == qid, SurveyAnswer.response_id.in_(response_ids))
            .all()
            if v[0] is not None
        ]
        total = len(values)
        breakdown = [
            {
                "level": level,
                "label": RATING_LABELS[level],
                "count": (c := sum(1 for v in values if v == level)),
                "percentage": round(c / total * 100, 1) if total else 0,
            }
            for level in (5, 4, 3, 2, 1)
        ]
        return {
            "type": "rating", "total_respondents": total,
            "average": round(sum(values) / total, 2) if total else None,
            "breakdown": breakdown,
        }

    if qtype == "number":
        values = [
            v[0]
            for v in db.session.query(SurveyAnswer.answer_number)
            .filter(SurveyAnswer.question_id == qid, SurveyAnswer.response_id.in_(response_ids))
            .all()
            if v[0] is not None
        ]
        total = len(values)
        return {
            "type": "number", "total_respondents": total,
            "average": round(sum(values) / total, 2) if total else None,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
        }

    # text, textarea, date — câu trả lời mở, không gộp; trả mẫu gần nhất để tham khảo
    samples = [
        r[0]
        for r in db.session.query(SurveyAnswer.answer_text)
        .filter(SurveyAnswer.question_id == qid, SurveyAnswer.response_id.in_(response_ids))
        .order_by(SurveyAnswer.id.desc())
        .limit(20)
        .all()
        if r[0]
    ]
    return {"type": "open_text", "total_respondents": len(samples), "samples": samples}


def _by_question(survey_id: int, response_ids: list[int]) -> list[dict]:
    questions = list_questions(survey_id, include_inactive=False)
    if not response_ids:
        return [{**q, "stats": _empty_question_stats(q["question_type"])} for q in questions]
    return [{**q, "stats": _question_stats(q, response_ids)} for q in questions]


def _time_series(response_ids: list[int]) -> list[dict]:
    if not response_ids:
        return []
    day = func.date(SurveyResponse.submitted_at)
    rows = (
        db.session.query(day.label("day"), func.count(SurveyResponse.id))
        .filter(SurveyResponse.id.in_(response_ids))
        .group_by(day)
        .order_by(day)
        .all()
    )
    return [{"date": str(d), "count": c} for d, c in rows]


def _by_branch(response_ids: list[int], values_by_response: dict[int, list[int]]) -> list[dict]:
    if not response_ids:
        return []
    rows = (
        db.session.query(SurveyResponse.branch_id, func.count(SurveyResponse.id))
        .filter(SurveyResponse.id.in_(response_ids))
        .group_by(SurveyResponse.branch_id)
        .all()
    )
    branch_ids = [b for b, _ in rows if b is not None]
    names = {}
    if branch_ids:
        names = dict(
            db.session.query(OrganizationUnit.id, OrganizationUnit.name)
            .filter(OrganizationUnit.id.in_(branch_ids))
            .all()
        )

    response_branch = dict(
        db.session.query(SurveyResponse.id, SurveyResponse.branch_id)
        .filter(SurveyResponse.id.in_(response_ids))
        .all()
    )
    ratings_by_branch: dict[int | None, list[int]] = defaultdict(list)
    for rid, values in values_by_response.items():
        ratings_by_branch[response_branch.get(rid)].extend(values)

    result = []
    for branch_id, total in rows:
        values = ratings_by_branch.get(branch_id, [])
        tv = len(values)
        satisfied = sum(1 for v in values if v >= 4)
        dissatisfied = sum(1 for v in values if v <= 2)
        result.append(
            {
                "branch_id": branch_id,
                "branch_name": names.get(branch_id, "Không xác định"),
                "total_responses": total,
                "average_score": round(sum(values) / tv, 2) if tv else None,
                "satisfaction_rate": round(satisfied / tv * 100, 1) if tv else 0,
                "dissatisfaction_rate": round(dissatisfied / tv * 100, 1) if tv else 0,
            }
        )
    result.sort(key=lambda r: r["total_responses"], reverse=True)
    return result
