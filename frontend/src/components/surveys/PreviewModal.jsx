import { useState } from "react";
import { Modal } from "../ui/Modal";
import { QuestionRenderer } from "./QuestionRenderer";
import { LoadingState, EmptyState } from "../ui/DataStates";
import { useSurveyQuestions } from "../../hooks/useSurveyQuestions";

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
          {questions.map((q) => (
            <QuestionRenderer
              key={q.id}
              question={q}
              value={answers[q.id] ?? (q.question_type === "multiple_choice" ? [] : null)}
              onChange={(v) => setAnswers((a) => ({ ...a, [q.id]: v }))}
            />
          ))}
        </div>
      )}
    </Modal>
  );
}
