"""Scoring at submission time, shared by reports through immutable answer snapshots."""
from collections import defaultdict


SATISFACTION_LEVELS = {
    "rất hài lòng": 5, "hài lòng": 4, "bình thường": 3,
    "không hài lòng": 2, "rất không hài lòng": 1,
}


def deduction_score(max_score, zero_score_at, selected_scores):
    if zero_score_at is not None and len(selected_scores) >= zero_score_at:
        return 0.0
    return max(0.0, float(max_score) - sum(selected_scores))


RATING_MAX = 5.0


def _question_ceiling(question, children_by_parent):
    """Điểm tối đa MỘT câu hỏi có thể đạt (đã gộp câu hỏi phụ thay nhánh kích
    hoạt, giống lúc chấm điểm thật ở `record_scores`) — None nếu câu hỏi
    không cấu hình điểm (không đóng góp vào tổng)."""
    children = children_by_parent.get(question.id, [])

    def branch_value(own_value, *, trigger_answer=None, trigger_option_id=None):
        for child in children:
            if (trigger_answer is not None and child.trigger_answer == trigger_answer) or (
                trigger_option_id is not None and child.trigger_option_id == trigger_option_id
            ):
                return _question_ceiling(child, children_by_parent)
        return own_value

    if question.question_type == "rating":
        return RATING_MAX
    if question.question_type == "yes_no":
        values = [
            v
            for v in (
                branch_value(question.yes_score, trigger_answer="yes"),
                branch_value(question.no_score, trigger_answer="no"),
            )
            if v is not None
        ]
        return max(values) if values else None
    if question.question_type == "multiple_choice" and question.scoring_mode == "deduction":
        return float(question.max_score or 0)
    if question.question_type in ("single_choice", "multiple_choice"):
        active_options = [o for o in question.options if o.is_active]
        satisfaction_fallback = {}
        if question.question_type == "single_choice":
            labels = {
                SATISFACTION_LEVELS.get(o.option_text.strip().lower()) for o in active_options
            }
            if labels == {1, 2, 3, 4, 5}:
                satisfaction_fallback = {
                    o.id: float(SATISFACTION_LEVELS[o.option_text.strip().lower()])
                    for o in active_options
                }
        values = []
        for o in active_options:
            own_value = o.score if o.score is not None else satisfaction_fallback.get(o.id)
            value = branch_value(own_value, trigger_option_id=o.id)
            if value is not None:
                values.append(value)
        if not values:
            return None
        if question.question_type == "single_choice":
            return max(values)
        return sum(v for v in values if v > 0)
    return None


def max_possible_score(questions) -> float | None:
    """Tổng điểm tối đa MỘT lượt phản hồi có thể đạt được với bộ câu hỏi hiện tại
    của khảo sát — cộng điểm tối đa từng câu hỏi gốc (không tính câu hỏi phụ
    riêng, vì điểm của nó đã gộp vào câu cha khi nhánh tương ứng được chọn)."""
    children_by_parent = defaultdict(list)
    for q in questions:
        if q.parent_question_id:
            children_by_parent[q.parent_question_id].append(q)
    total = None
    for q in questions:
        if q.parent_question_id:
            continue
        ceiling = _question_ceiling(q, children_by_parent)
        if ceiling is not None:
            total = (total or 0.0) + ceiling
    return total


def legacy_answer_score(answer):
    if answer.option is not None:
        return answer.option.score
    if answer.question.question_type == "rating":
        return answer.answer_number
    if answer.question.question_type == "yes_no":
        return answer.question.yes_score if answer.answer_text == "yes" else answer.question.no_score
    return None


def record_scores(planned, visible_questions):
    """Attach scores to validated answer rows. Child scores replace their triggering answer.

    A deduction is counted once per question. Child rows remain available for question
    reports, but are excluded from totals to avoid counting a parent and its child twice.
    Existing standard multiple-choice aggregation is kept (one value per selected option).
    """
    children = defaultdict(list)
    rows_by_question = {q.id: rows for q, rows in planned}
    for q in visible_questions:
        if q.parent_question_id:
            children[q.parent_question_id].append(q)

    for q, rows in planned:
        options = {o.id: o for o in q.options}
        labels = {
            SATISFACTION_LEVELS.get(o.option_text.strip().lower())
            for o in q.options if o.is_active
        }
        for row in rows:
            score = None
            if q.question_type in ("single_choice", "multiple_choice") and row.get("option_id"):
                option = options[row["option_id"]]
                score = option.score
                if score is None and q.question_type == "single_choice" and labels == {1, 2, 3, 4, 5}:
                    score = SATISFACTION_LEVELS.get(option.option_text.strip().lower())
            elif q.question_type == "yes_no":
                score = q.yes_score if row.get("answer_text") == "yes" else q.no_score
            elif q.question_type == "rating":
                score = row.get("answer_number")
            row.update(score_recorded=True, earned_score=score, score_in_total=not q.parent_question_id)
        if q.scoring_mode == "deduction":
            selected_scores = [float(options[r["option_id"]].score or 0) for r in rows if r.get("option_id")]
            for row in rows:
                row["earned_score"] = None
            rows[0]["earned_score"] = deduction_score(q.max_score, q.zero_score_at, selected_scores)

    for q, rows in planned:
        if not children[q.id]:
            continue
        for row in rows:
            matching = [
                child for child in children[q.id]
                if (child.trigger_answer and child.trigger_answer == row.get("answer_text"))
                or (child.trigger_option_id and child.trigger_option_id == row.get("option_id"))
            ]
            if matching:
                scores = [
                    child_row["earned_score"]
                    for child in matching
                    for child_row in rows_by_question.get(child.id, [])
                    if child_row["earned_score"] is not None
                ]
                row["earned_score"] = sum(scores) if scores else None
