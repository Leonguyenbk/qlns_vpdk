import { useState } from "react";
import { Modal } from "../ui/Modal";
import { QuestionRenderer } from "./QuestionRenderer";
import { LoadingState, EmptyState } from "../ui/DataStates";
import { useSurveyQuestions } from "../../hooks/useSurveyQuestions";
import { visibleSurveyQuestions, updateSurveyAnswer, questionValue } from "../../lib/surveyQuestions";

/** Xem trước khảo sát như người dân sẽ thấy — chỉ tương tác cục bộ, không gửi dữ liệu. */
export function PreviewModal({ survey, onClose }) {
  const { data: questions, isLoading } = useSurveyQuestions(survey?.id);
  const [answers, setAnswers] = useState({});

  return (
    <Modal open={!!survey} onClose={onClose} title={survey ? `Xem trước: ${survey.title}` : "Xem trước"} size="md">
      {survey?.description && <p className="mb-4 text-sm text-muted">{survey.description}</p>}
      {isLoading ? (
        <LoadingState />
      ) : !questions?.length ? (
        <EmptyState title="Khảo sát chưa có câu hỏi" />
      ) : (
        <div className="grid gap-6">
          {visibleSurveyQuestions(questions, answers).map((q) => (
            <div key={q.id} className={q.parent_question_id ? "ml-3 border-l-2 border-rule pl-4" : ""}>
              <QuestionRenderer
                question={q}
                value={questionValue(q, answers)}
                onChange={(v) => setAnswers((a) => updateSurveyAnswer(questions, a, q.id, v))}
              />
            </div>
          ))}
        </div>
      )}
    </Modal>
  );
}
