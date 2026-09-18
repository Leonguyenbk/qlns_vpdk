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
