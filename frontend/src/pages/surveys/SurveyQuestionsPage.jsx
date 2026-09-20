import { useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy, arrayMove } from "@dnd-kit/sortable";
import { useSurvey } from "../../hooks/useSurveys";
import {
  useSurveyQuestions,
  useSurveyQuestionMutations,
  useSurveySections,
  useSurveySectionMutations,
} from "../../hooks/useSurveyQuestions";
import { useCan } from "../../components/Can";
import { PERMISSIONS, SURVEY_STATUS_LABELS, SURVEY_STATUS_BADGE } from "../../lib/constants";
import { PageHeader, Button, Badge } from "../../components/ui/primitives";
import { LoadingState, ErrorState, EmptyState } from "../../components/ui/DataStates";
import { QuestionCard } from "../../components/surveys/QuestionCard";
import { AddQuestionModal } from "../../components/surveys/AddQuestionModal";
import { PreviewModal } from "../../components/surveys/PreviewModal";
import { SectionManager } from "../../components/surveys/SectionManager";

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
  const { data: sections = [] } = useSurveySections(id);
  const sectionMutations = useSurveySectionMutations(id);
  const [showAdd, setShowAdd] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [preset, setPreset] = useState(null);
  const [collapsedIds, setCollapsedIds] = useState(() => new Set());

  // Câu hỏi phụ nằm lồng trong thẻ câu cha; chỉ câu gốc (hoặc câu phụ mồ côi) mới ở danh sách chính.
  const topLevel = useMemo(() => {
    const ids = new Set((questions || []).map((q) => q.id));
    return (questions || []).filter((q) => !q.parent_question_id || !ids.has(q.parent_question_id));
  }, [questions]);

  const collapse = useMemo(
    () => ({
      ids: collapsedIds,
      toggle: (id) =>
        setCollapsedIds((prev) => {
          const next = new Set(prev);
          if (next.has(id)) next.delete(id);
          else next.add(id);
          return next;
        }),
    }),
    [collapsedIds]
  );
  const collapseAll = () => setCollapsedIds(new Set((questions || []).map((q) => q.id)));
  const expandAll = () => setCollapsedIds(new Set());

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  const onDragEnd = (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id || !questions) return;
    const ids = topLevel.map((q) => `question-${q.id}`);
    const oldIndex = ids.indexOf(active.id);
    const newIndex = ids.indexOf(over.id);
    if (oldIndex < 0 || newIndex < 0) return;
    const reordered = arrayMove(topLevel, oldIndex, newIndex);
    // Câu phụ đi liền ngay sau câu cha để thứ tự lưu luôn nhất quán.
    const flat = reordered.flatMap((q) => [q, ...questions.filter((c) => c.parent_question_id === q.id)]);
    mutations.reorder.mutate(flat.map((q, i) => ({ id: q.id, sort_order: i + 1 })));
  };

  const onCreate = async (body) => {
    await mutations.create.mutateAsync(body);
    toast.success("Đã thêm câu hỏi");
  };

  let sectionCounter = 0;

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
            {questions?.length > 0 && (
              <>
                <Button variant="secondary" onClick={collapseAll}>
                  Thu gọn tất cả
                </Button>
                <Button variant="secondary" onClick={expandAll}>
                  Mở rộng tất cả
                </Button>
              </>
            )}
            <Button variant="secondary" onClick={() => setShowPreview(true)}>
              Xem trước
            </Button>
          </div>
        }
      />

      {canManage && <SectionManager sections={sections} mutations={sectionMutations} />}

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
          <SortableContext items={topLevel.map((q) => `question-${q.id}`)} strategy={verticalListSortingStrategy}>
            <div className="grid gap-4">
              {topLevel.map((q, i) => {
                const prevSection = topLevel[i - 1]?.section || "";
                const curSection = q.section || "";
                if (curSection !== prevSection) sectionCounter = 0;
                sectionCounter += 1;
                return (
                  <div key={q.id}>
                    {q.section && q.section !== prevSection && (
                      <h3 className="mb-2 mt-1 font-display text-sm font-semibold text-ink first:mt-0">
                        {q.section}
                      </h3>
                    )}
                    <QuestionCard
                      question={q}
                      mutations={mutations}
                      canManage={canManage}
                      index={sectionCounter - 1}
                      sections={sections}
                      questions={questions}
                      collapse={collapse}
                      onAddChild={(p) => {
                        setPreset(p);
                        setShowAdd(true);
                      }}
                    />
                  </div>
                );
              })}
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

      <AddQuestionModal
        open={showAdd}
        preset={preset}
        onClose={() => {
          setShowAdd(false);
          setPreset(null);
        }}
        onCreate={onCreate}
        existingQuestions={questions || []}
        sections={sections}
      />
      <PreviewModal survey={showPreview ? survey : null} onClose={() => setShowPreview(false)} />
    </div>
  );
}
