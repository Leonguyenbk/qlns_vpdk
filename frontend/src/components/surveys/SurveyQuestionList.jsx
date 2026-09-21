import { QuestionRenderer } from "./QuestionRenderer";
import { questionValue } from "../../lib/surveyQuestions";

/**
 * Danh sách câu hỏi hiển thị cho người trả lời: chèn tiêu đề Phần mỗi khi sang
 * phần mới. `questions` đã được backend sắp theo thứ tự Phần → câu hỏi; câu phụ
 * đi liền câu cha nên dùng section của câu gốc để không lặp tiêu đề.
 */
export function SurveyQuestionList({ questions, answers, onChange, errors = {}, disabled = false }) {
  const sectionOf = new Map(questions.map((q) => [q.id, q.section]));
  let lastSection;
  return (
    <div className="grid gap-6">
      {questions.map((q) => {
        const section = q.parent_question_id ? sectionOf.get(q.parent_question_id) : q.section;
        const showHeading = !q.parent_question_id && section && section !== lastSection;
        if (!q.parent_question_id) lastSection = section;
        return (
          <div key={q.id} id={`q-${q.id}`} className="grid gap-6">
            {showHeading && (
              <h2 className="border-b border-rule pb-1.5 font-display text-base font-semibold text-ink">
                {section}
              </h2>
            )}
            <div className={q.parent_question_id ? "ml-3 border-l-2 border-rule pl-4" : ""}>
              <QuestionRenderer
                question={q}
                value={questionValue(q, answers)}
                onChange={(v) => onChange(q.id, v)}
                error={errors[q.id]}
                disabled={disabled}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
