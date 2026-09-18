"""Nghiệp vụ thống kê khảo sát: tổng quan, theo câu hỏi, theo thời gian, theo chi nhánh."""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func

from ..exports.survey_export import build_summary_workbook
from ..extensions import db
from ..models import OrganizationUnit
from ..models.survey import SurveyAnswer, SurveyOption, SurveyQuestion, SurveyResponse
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


def _score_sources(
    survey_id: int,
) -> tuple[list[int], dict[int, float], dict[int, dict[str, float]], dict[int, float]]:
    """Trả về nguồn điểm của khảo sát.

    Điểm cấu hình trên phương án được ưu tiên và áp dụng cả cho phiên bản phương
    án đã ẩn để số liệu lịch sử không đổi. Thang hài lòng 5 nhãn cũ vẫn được suy
    ra như trước nhằm tương thích với khảo sát đã tạo trước migration 0021.
    """
    questions = (
        db.session.query(SurveyQuestion)
        .filter(SurveyQuestion.survey_id == survey_id)
        .all()
    )
    rating_question_ids: list[int] = []
    option_score_map: dict[int, float] = {}
    yes_no_score_map: dict[int, dict[str, float]] = {}
    satisfaction_option_map: dict[int, float] = {}
    for q in questions:
        if q.question_type == "rating":
            rating_question_ids.append(q.id)
        elif q.question_type == "yes_no":
            scores = {}
            if q.yes_score is not None:
                scores["yes"] = float(q.yes_score)
            if q.no_score is not None:
                scores["no"] = float(q.no_score)
            if scores:
                yes_no_score_map[q.id] = scores
        if q.question_type in ("single_choice", "multiple_choice"):
            for option in q.options:
                if option.score is not None:
                    option_score_map[option.id] = float(option.score)

        if q.question_type == "single_choice":
            active_options = [o for o in q.options if o.is_active]
            levels = {
                _SATISFACTION_LEVEL_BY_LABEL.get(_normalize_label(o.option_text))
                for o in active_options
            }
            if levels == set(RATING_LABELS):
                for o in active_options:
                    level = float(
                        _SATISFACTION_LEVEL_BY_LABEL[_normalize_label(o.option_text)]
                    )
                    option_score_map.setdefault(o.id, level)
                    satisfaction_option_map[o.id] = level
    return (
        rating_question_ids,
        option_score_map,
        yes_no_score_map,
        satisfaction_option_map,
    )


def _score_values_by_response(
    response_ids: list[int],
    rating_question_ids: list[int],
    option_score_map: dict[int, float],
    yes_no_score_map: dict[int, dict[str, float]] | None = None,
) -> dict[int, list[float]]:
    """{response_id: [điểm, ...]} từ câu rating và phương án có cấu hình điểm."""
    values_by_response: dict[int, list[float]] = defaultdict(list)
    if not response_ids:
        return values_by_response
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
                values_by_response[rid].append(float(value))
    if option_score_map:
        rows = (
            db.session.query(SurveyAnswer.response_id, SurveyAnswer.option_id)
            .filter(
                SurveyAnswer.response_id.in_(response_ids),
                SurveyAnswer.option_id.in_(option_score_map.keys()),
            )
            .all()
        )
        for rid, option_id in rows:
            values_by_response[rid].append(option_score_map[option_id])
    if yes_no_score_map:
        rows = (
            db.session.query(
                SurveyAnswer.response_id,
                SurveyAnswer.question_id,
                SurveyAnswer.answer_text,
            )
            .filter(
                SurveyAnswer.response_id.in_(response_ids),
                SurveyAnswer.question_id.in_(yes_no_score_map.keys()),
            )
            .all()
        )
        for response_id, question_id, answer_text in rows:
            score = yes_no_score_map[question_id].get(answer_text)
            if score is not None:
                values_by_response[response_id].append(score)
    return values_by_response


def _scoped_response_ids(survey_id: int, args, *, actor, scope) -> list[int]:
    q = db.session.query(SurveyResponse.id).filter(SurveyResponse.survey_id == survey_id)
    q = apply_response_filters(q, args, response_model=SurveyResponse)
    q = apply_branch_scope(q, actor=actor, scope=scope, column=SurveyResponse.branch_id)
    return [r[0] for r in q.all()]


def get_statistics(survey_id: int, args, *, actor, scope) -> dict:
    get_survey_or_404(survey_id)
    response_ids = _scoped_response_ids(survey_id, args, actor=actor, scope=scope)
    rating_qids, option_score_map, yes_no_score_map, satisfaction_option_map = (
        _score_sources(survey_id)
    )
    values_by_response = _score_values_by_response(
        response_ids, rating_qids, option_score_map, yes_no_score_map
    )
    satisfaction_by_response = _score_values_by_response(
        response_ids, rating_qids, satisfaction_option_map
    )
    return {
        "overview": _overview(
            survey_id, response_ids, values_by_response, satisfaction_by_response
        ),
        "by_question": _by_question(survey_id, response_ids),
        "time_series": _time_series(response_ids),
        "by_branch": _by_branch(
            response_ids, values_by_response, satisfaction_by_response
        ),
    }


def _overview(
    survey_id: int,
    response_ids: list[int],
    values_by_response: dict[int, list[float]],
    satisfaction_by_response: dict[int, list[float]],
) -> dict:
    total_responses = len(response_ids)
    if not total_responses:
        return {
            "total_responses": 0,
            "completion_rate": 0,
            "average_score": None,
            "score_answer_count": 0,
            "satisfaction_answer_count": 0,
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

    score_values = [v for rid in response_ids for v in values_by_response.get(rid, [])]
    total_scores = len(score_values)
    satisfaction_values = [
        v for rid in response_ids for v in satisfaction_by_response.get(rid, [])
    ]
    total_satisfaction = len(satisfaction_values)
    satisfied = sum(1 for v in satisfaction_values if v >= 4)
    dissatisfied = sum(1 for v in satisfaction_values if v <= 2)
    rounded_levels = [max(1, min(5, round(v))) for v in satisfaction_values]
    breakdown = [
        {
            "level": level,
            "label": RATING_LABELS[level],
            "count": (c := sum(1 for v in rounded_levels if v == level)),
            "percentage": round(c / total_satisfaction * 100, 1)
            if total_satisfaction
            else 0,
        }
        for level in (5, 4, 3, 2, 1)
    ]

    return {
        "total_responses": total_responses,
        "completion_rate": completion_rate,
        "average_score": round(sum(score_values) / total_scores, 2) if total_scores else None,
        "score_answer_count": total_scores,
        "satisfaction_rate": round(satisfied / total_satisfaction * 100, 1)
        if total_satisfaction
        else 0,
        "dissatisfaction_rate": round(dissatisfied / total_satisfaction * 100, 1)
        if total_satisfaction
        else 0,
        "satisfaction_answer_count": total_satisfaction,
        "rating_breakdown": breakdown,
    }


def _empty_question_stats(qtype: str) -> dict:
    if qtype in ("single_choice", "multiple_choice"):
        return {
            "type": "choice",
            "total_respondents": 0,
            "average_score": None,
            "scored_answers": 0,
            "options": [],
        }
    if qtype == "yes_no":
        return {
            "type": "yes_no", "total_respondents": 0,
            "yes_count": 0, "no_count": 0, "yes_percentage": 0, "no_percentage": 0,
            "yes_score": None, "no_score": None, "average_score": None,
            "scored_answers": 0,
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
        scored_rows = (
            db.session.query(SurveyOption.score)
            .join(SurveyAnswer, SurveyAnswer.option_id == SurveyOption.id)
            .filter(
                SurveyAnswer.question_id == qid,
                SurveyAnswer.response_id.in_(response_ids),
                SurveyOption.score.isnot(None),
            )
            .all()
        )
        scored_values = [float(row[0]) for row in scored_rows]
        option_rows = list(question["options"])
        visible_option_ids = {option["id"] for option in option_rows}
        historical_options = (
            db.session.query(SurveyOption)
            .filter(
                SurveyOption.question_id == qid,
                SurveyOption.id.in_(set(counts) - visible_option_ids),
            )
            .order_by(SurveyOption.sort_order, SurveyOption.id)
            .all()
        )
        option_rows.extend(
            {
                **option.to_dict(),
                "option_text": f"{option.option_text} (phiên bản cũ)",
            }
            for option in historical_options
        )
        options = [
            {
                "option_id": opt["id"],
                "option_text": opt["option_text"],
                "score": opt.get("score"),
                "count": counts.get(opt["id"], 0),
                "percentage": round(counts.get(opt["id"], 0) / total_respondents * 100, 1)
                if total_respondents
                else 0,
            }
            for opt in option_rows
        ]
        return {
            "type": "choice",
            "total_respondents": total_respondents,
            "average_score": round(sum(scored_values) / len(scored_values), 2)
            if scored_values
            else None,
            "scored_answers": len(scored_values),
            "options": options,
        }

    if qtype == "yes_no":
        counts = dict(
            db.session.query(SurveyAnswer.answer_text, func.count(SurveyAnswer.id))
            .filter(SurveyAnswer.question_id == qid, SurveyAnswer.response_id.in_(response_ids))
            .group_by(SurveyAnswer.answer_text)
            .all()
        )
        yes, no = counts.get("yes", 0), counts.get("no", 0)
        total = yes + no
        scored_values = []
        if question.get("yes_score") is not None:
            scored_values.extend([float(question["yes_score"])] * yes)
        if question.get("no_score") is not None:
            scored_values.extend([float(question["no_score"])] * no)
        return {
            "type": "yes_no", "total_respondents": total,
            "yes_count": yes, "no_count": no,
            "yes_percentage": round(yes / total * 100, 1) if total else 0,
            "no_percentage": round(no / total * 100, 1) if total else 0,
            "yes_score": question.get("yes_score"),
            "no_score": question.get("no_score"),
            "average_score": round(sum(scored_values) / len(scored_values), 2)
            if scored_values
            else None,
            "scored_answers": len(scored_values),
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


def _by_branch(
    response_ids: list[int],
    values_by_response: dict[int, list[float]],
    satisfaction_by_response: dict[int, list[float]],
) -> list[dict]:
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
    ratings_by_branch: dict[int | None, list[float]] = defaultdict(list)
    for rid, values in values_by_response.items():
        ratings_by_branch[response_branch.get(rid)].extend(values)
    satisfaction_by_branch: dict[int | None, list[float]] = defaultdict(list)
    for rid, values in satisfaction_by_response.items():
        satisfaction_by_branch[response_branch.get(rid)].extend(values)

    result = []
    for branch_id, total in rows:
        values = ratings_by_branch.get(branch_id, [])
        tv = len(values)
        satisfaction_values = satisfaction_by_branch.get(branch_id, [])
        satisfaction_total = len(satisfaction_values)
        satisfied = sum(1 for v in satisfaction_values if v >= 4)
        dissatisfied = sum(1 for v in satisfaction_values if v <= 2)
        result.append(
            {
                "branch_id": branch_id,
                "branch_name": names.get(branch_id, "Không xác định"),
                "total_responses": total,
                "average_score": round(sum(values) / tv, 2) if tv else None,
                "scored_answers": tv,
                "satisfaction_rate": round(satisfied / satisfaction_total * 100, 1)
                if satisfaction_total
                else 0,
                "dissatisfaction_rate": round(dissatisfied / satisfaction_total * 100, 1)
                if satisfaction_total
                else 0,
            }
        )
    result.sort(
        key=lambda r: (
            r["branch_id"] is None or r["average_score"] is None,
            -(r["average_score"] or 0),
            -r["total_responses"],
            r["branch_name"],
        )
    )
    previous_score = None
    current_rank = 0
    for index, row in enumerate(result, start=1):
        if row["branch_id"] is None or row["average_score"] is None:
            row["rank"] = None
            continue
        if previous_score != row["average_score"]:
            current_rank = index
            previous_score = row["average_score"]
        row["rank"] = current_rank
    return result


def export_summary(survey_id: int, args, *, actor, scope):
    """Xuất Excel bảng TỔNG HỢP tỷ lệ theo câu hỏi (tôn trọng bộ lọc hiện tại),
    không có thông tin người trả lời — khác với `survey_response_service.export_responses`
    (danh sách từng lượt + chi tiết từng câu trả lời)."""
    survey = get_survey_or_404(survey_id)
    stats = get_statistics(survey_id, args, actor=actor, scope=scope)

    scope_label = "Toàn hệ thống"
    branch_id = args.get("branch_id")
    if branch_id:
        branch = db.session.get(OrganizationUnit, int(branch_id))
        if branch:
            scope_label = f"Chi nhánh {branch.name}"

    return build_summary_workbook(survey, stats, scope_label=scope_label)
