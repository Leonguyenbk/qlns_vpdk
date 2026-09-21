import { useState } from "react";
import { Modal } from "../ui/Modal";
import { SurveyQuestionList } from "./SurveyQuestionList";
import { LoadingState, EmptyState } from "../ui/DataStates";
import { useSurveyQuestions } from "../../hooks/useSurveyQuestions";
import { visibleSurveyQuestions, updateSurveyAnswer } from "../../lib/surveyQuestions";

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
        <SurveyQuestionList
          questions={visibleSurveyQuestions(questions, answers)}
          answers={answers}
          onChange={(qid, v) => setAnswers((a) => updateSurveyAnswer(questions, a, qid, v))}
        />
      )}
    </Modal>
  );
}
