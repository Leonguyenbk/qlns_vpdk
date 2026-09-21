export function isQuestionVisible(question, answers) {
  if (!question.parent_question_id) return true;
  const parentValue = answers[question.parent_question_id];
  if (question.trigger_answer) return parentValue === question.trigger_answer;
  if (question.trigger_option_id) {
    return Array.isArray(parentValue)
      ? parentValue.includes(question.trigger_option_id)
      : parentValue === question.trigger_option_id;
  }
  return false;
}

function activeFields(question) {
  return (question.options || []).filter((o) => o.is_active !== false);
}

/** Câu nhiều ô nhập: value là { [option_id]: text }. */
export function filledFieldAnswers(question, value) {
  const values = value && typeof value === "object" ? value : {};
  return activeFields(question)
    .map((o) => ({ option_id: o.id, answer_text: String(values[o.id] ?? "").trim() }))
    .filter((f) => f.answer_text !== "");
}

/** Tên các ô bắt buộc còn để trống của câu nhiều ô nhập. */
export function missingRequiredFields(question, value) {
  const filled = new Set(filledFieldAnswers(question, value).map((f) => f.option_id));
  return activeFields(question)
    .filter((o) => o.is_required && !filled.has(o.id))
    .map((o) => o.option_text);
}

export function isQuestionAnswered(question, value) {
  if (question.question_type === "text_fields") return filledFieldAnswers(question, value).length > 0;
  if (question.question_type === "multiple_choice" && question.scoring_mode === "deduction") {
    return true;
  }
  if (value === null || value === undefined) return false;
  if (question.question_type === "multiple_choice") return Array.isArray(value) && value.length > 0;
  if (question.question_type === "number" || question.question_type === "rating") return value !== null;
  return String(value).trim() !== "";
}

export function questionValue(question, answers) {
  if (answers[question.id] !== undefined) return answers[question.id];
  if (question.question_type === "text_fields") return {};
  return question.question_type === "multiple_choice" ? [] : null;
}

export function visibleSurveyQuestions(questions, answers) {
  return questions.filter((q) => !q.parent_question_id).flatMap((parent) => [
    parent,
    ...questions.filter((child) => child.parent_question_id === parent.id && isQuestionVisible(child, answers)),
  ]);
}

export function updateSurveyAnswer(questions, answers, questionId, value) {
  const next = { ...answers, [questionId]: value };
  for (const question of questions) {
    if (question.parent_question_id && !isQuestionVisible(question, next)) delete next[question.id];
  }
  return next;
}
