import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy, arrayMove } from "@dnd-kit/sortable";
import { useSurvey } from "../../hooks/useSurveys";
import { useSurveyQuestions, useSurveyQuestionMutations } from "../../hooks/useSurveyQuestions";
import { useCan } from "../../components/Can";
import { PERMISSIONS, SURVEY_STATUS_LABELS, SURVEY_STATUS_BADGE } from "../../lib/constants";
import { PageHeader, Button, Badge } from "../../components/ui/primitives";
import { LoadingState, ErrorState, EmptyState } from "../../components/ui/DataStates";
import { QuestionCard } from "../../components/surveys/QuestionCard";
import { AddQuestionModal } from "../../components/surveys/AddQuestionModal";
import { PreviewModal } from "../../components/surveys/PreviewModal";

export default function SurveyQuestionsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { can } = useCan();
  const canManage = can(PERMISSIONS.SURVEY_MANAGE_QUESTIONS);
  const { data: survey } = useSurvey(id);
  const { data: questions, isLoading, isError, error, refetch } = useSurveyQuestions(id, {
    includeInactive: true,
  });
  const mutations = useSurveyQuestionMutations(id);
  const [showAdd, setShowAdd] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  const onDragEnd = (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id || !questions) return;
    const ids = questions.map((q) => `question-${q.id}`);
    const oldIndex = ids.indexOf(active.id);
    const newIndex = ids.indexOf(over.id);
    const reordered = arrayMove(questions, oldIndex, newIndex);
    mutations.reorder.mutate(reordered.map((q, i) => ({ id: q.id, sort_order: i + 1 })));
  };

  const onCreate = async (body) => {
    await mutations.create.mutateAsync(body);
    toast.success("Đã thêm câu hỏi");
  };

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title={survey ? survey.title : "Quản lý câu hỏi"}
        subtitle="Kéo thả để đổi thứ tự câu hỏi và phương án trả lời"
        actions={
          <div className="flex flex-wrap gap-2">
            {survey && (
              <Badge className={SURVEY_STATUS_BADGE[survey.status]}>
                {SURVEY_STATUS_LABELS[survey.status]}
              </Badge>
            )}
            <Button variant="secondary" onClick={() => navigate(`/surveys/${id}`)}>
              ← Thông tin khảo sát
            </Button>
            <Button variant="secondary" onClick={() => setShowPreview(true)}>
              Xem trước
            </Button>
          </div>
        }
      />

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : !questions?.length ? (
        <EmptyState
          title="Khảo sát chưa có câu hỏi nào"
          action={canManage && <Button onClick={() => setShowAdd(true)}>+ Thêm câu hỏi</Button>}
        />
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
          <SortableContext items={questions.map((q) => `question-${q.id}`)} strategy={verticalListSortingStrategy}>
            <div className="grid gap-4">
              {questions.map((q, i) => (
                <QuestionCard key={q.id} question={q} mutations={mutations} canManage={canManage} index={i} />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}

      {canManage && questions?.length > 0 && (
        <div className="mt-4 text-center">
          <Button variant="secondary" onClick={() => setShowAdd(true)}>
            + Thêm câu hỏi
          </Button>
        </div>
      )}

      <AddQuestionModal open={showAdd} onClose={() => setShowAdd(false)} onCreate={onCreate} />
      <PreviewModal survey={showPreview ? survey : null} onClose={() => setShowPreview(false)} />
    </div>
  );
}
