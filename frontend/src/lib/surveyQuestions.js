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

export function isQuestionAnswered(question, value) {
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
