import { useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import {
  DndContext,
  closestCenter,
  pointerWithin,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";
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
import { SectionGroup } from "../../components/surveys/SectionGroup";
import { apiErrorMessage } from "../../lib/api";

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
  const [addSectionId, setAddSectionId] = useState(undefined);
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
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  // Nhóm câu hỏi theo Phần: mỗi phần có danh sách câu hỏi riêng, không cần chọn phần từng câu.
  const groups = useMemo(() => {
    const sectionIds = new Set(sections.map((sec) => sec.id));
    const loose = topLevel.filter((q) => !q.section_id || !sectionIds.has(q.section_id));
    const result = [];
    if (loose.length > 0 || sections.length === 0) {
      result.push({ key: "none", id: null, title: "Chưa thuộc phần nào", items: loose });
    }
    for (const sec of sections) {
      result.push({
        key: `s${sec.id}`,
        id: sec.id,
        title: sec.title,
        items: topLevel.filter((q) => q.section_id === sec.id),
      });
    }
    return result;
  }, [topLevel, sections]);

  const groupCollapseKey = (group) => `section-${group.key}`;
  const collapseAll = () =>
    setCollapsedIds(
      new Set([...(questions || []).map((q) => q.id), ...groups.map(groupCollapseKey)])
    );
  const expandAll = () => setCollapsedIds(new Set());

  // Thả vào câu hỏi thì xếp cạnh câu đó; thả vào khung phần (kể cả phần trống) thì xếp cuối phần.
  const collisionDetection = (args) => {
    const only = (prefix) =>
      args.droppableContainers.filter((c) => String(c.id).startsWith(prefix));
    const hitQuestion = pointerWithin({ ...args, droppableContainers: only("question-") });
    if (hitQuestion.length) return hitQuestion;
    const hitSection = pointerWithin({ ...args, droppableContainers: only("section-") });
    if (hitSection.length) return hitSection;
    return closestCenter({ ...args, droppableContainers: only("question-") });
  };

  const onDragEnd = async (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id || !questions) return;
    const activeId = Number(String(active.id).replace("question-", ""));
    const src = groups.find((g) => g.items.some((q) => q.id === activeId));
    let dst;
    let dstIndex;
    if (String(over.id).startsWith("question-")) {
      const overId = Number(String(over.id).replace("question-", ""));
      dst = groups.find((g) => g.items.some((q) => q.id === overId));
      dstIndex = dst ? dst.items.findIndex((q) => q.id === overId) : -1;
    } else {
      dst = groups.find((g) => `section-${g.key}` === over.id);
      dstIndex = dst ? dst.items.length : -1;
    }
    if (!src || !dst || dstIndex < 0) return;
    const moving = src.items.find((q) => q.id === activeId);

    const nextGroups = groups.map((g) => {
      if (g === src && g === dst) {
        const from = g.items.findIndex((q) => q.id === activeId);
        return { ...g, items: arrayMove(g.items, from, dstIndex) };
      }
      if (g === src) return { ...g, items: g.items.filter((q) => q.id !== activeId) };
      if (g === dst) {
        const items = [...g.items];
        items.splice(dstIndex, 0, moving);
        return { ...g, items };
      }
      return g;
    });
    // Câu phụ đi liền ngay sau câu cha để thứ tự lưu luôn nhất quán.
    const flat = nextGroups.flatMap((g) =>
      g.items.flatMap((q) => [q, ...questions.filter((c) => c.parent_question_id === q.id)])
    );
    try {
      if (src !== dst) {
        const ids = [
          activeId,
          ...questions.filter((c) => c.parent_question_id === activeId).map((c) => c.id),
        ];
        for (const qid of ids) {
          await mutations.update.mutateAsync({ id: qid, body: { section_id: dst.id } });
        }
      }
      await mutations.reorder.mutateAsync(flat.map((q, i) => ({ id: q.id, sort_order: i + 1 })));
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const openAdd = (sectionId) => {
    setPreset(null);
    setAddSectionId(sectionId);
    setShowAdd(true);
  };

  const onCreate = async (body) => {
    await mutations.create.mutateAsync(body);
    toast.success("Đã thêm câu hỏi");
  };

  return (
    <div className="mx-auto max-w-5xl">
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
          action={canManage && <Button onClick={() => openAdd(undefined)}>+ Thêm câu hỏi</Button>}
        />
      ) : (
        <>
        {sections.length === 0 && canManage && (
          <p className="mb-3 rounded-lg border border-dashed border-rule px-3 py-2 text-xs text-muted">
            Khảo sát chưa chia phần nào nên câu hỏi đang hiện chung một danh sách. Tạo phần ở khung
            “Các phần của khảo sát” phía trên để câu hỏi được gom thành từng khối theo phần.
          </p>
        )}
        <DndContext sensors={sensors} collisionDetection={collisionDetection} onDragEnd={onDragEnd}>
          <div className="grid grid-cols-[minmax(0,1fr)] gap-4">
            {groups.map((group) => (
              <SectionGroup
                key={group.key}
                group={group}
                plain={sections.length === 0}
                collapsed={collapsedIds.has(groupCollapseKey(group))}
                onToggle={() => collapse.toggle(groupCollapseKey(group))}
                canManage={canManage}
                onAdd={() => openAdd(group.id ?? "")}
              >
                {group.items.map((q, i) => (
                  <div key={q.id} className="min-w-0">
                    <QuestionCard
                      question={q}
                      mutations={mutations}
                      canManage={canManage}
                      index={i}
                      questions={questions}
                      collapse={collapse}
                      onAddChild={(p) => {
                        setPreset(p);
                        setAddSectionId(undefined);
                        setShowAdd(true);
                      }}
                    />
                  </div>
                ))}
              </SectionGroup>
            ))}
          </div>
        </DndContext>
        </>
      )}

      {canManage && questions?.length > 0 && (
        <div className="mt-4 text-center">
          <Button variant="secondary" onClick={() => openAdd(undefined)}>
            + Thêm câu hỏi
          </Button>
        </div>
      )}

      <AddQuestionModal
        open={showAdd}
        preset={preset}
        defaultSectionId={addSectionId}
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
