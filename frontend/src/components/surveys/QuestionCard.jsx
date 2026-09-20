import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy, useSortable, arrayMove } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { QUESTION_TYPE_LABELS, QUESTION_TYPES_WITH_OPTIONS } from "../../lib/constants";
import { apiErrorMessage } from "../../lib/api";
import { Button, Select } from "../ui/primitives";
import { IconGrip, IconTrash, IconCopy } from "../ui/icons";
import { OptionRow } from "./OptionRow";
import { ConfirmDialog } from "../ui/Modal";

export function QuestionCard({
  question,
  mutations,
  canManage,
  index,
  sections = [],
  questions = [],
  nested = false,
  collapse,
  onAddChild,
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: `question-${question.id}`,
    disabled: nested,
  });
  const collapsed = collapse?.ids.has(question.id) ?? false;
  const [text, setText] = useState(question.question_text);
  const [yesScore, setYesScore] = useState(question.yes_score ?? "");
  const [noScore, setNoScore] = useState(question.no_score ?? "");
  const [maxScore, setMaxScore] = useState(question.max_score ?? "");
  const [zeroScoreAt, setZeroScoreAt] = useState(question.zero_score_at ?? "");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [newOption, setNewOption] = useState("");
  const [newOptionScore, setNewOptionScore] = useState("");
  const hasOptions = QUESTION_TYPES_WITH_OPTIONS.has(question.question_type);

  useEffect(() => setText(question.question_text), [question.question_text]);
  useEffect(() => setYesScore(question.yes_score ?? ""), [question.yes_score]);
  useEffect(() => setNoScore(question.no_score ?? ""), [question.no_score]);
  useEffect(() => setMaxScore(question.max_score ?? ""), [question.max_score]);
  useEffect(() => setZeroScoreAt(question.zero_score_at ?? ""), [question.zero_score_at]);

  const parentQuestion = questions.find((q) => q.id === question.parent_question_id);
  const triggerLabel = question.trigger_answer
    ? question.trigger_answer === "yes"
      ? "Có"
      : "Không"
    : parentQuestion?.options?.find((o) => o.id === question.trigger_option_id)?.option_text;
  const childQuestions = questions.filter((q) => q.parent_question_id === question.id);
  const canAddChild =
    canManage &&
    !nested &&
    !question.parent_question_id &&
    question.is_active &&
    question.scoring_mode !== "deduction" &&
    ["yes_no", "single_choice", "multiple_choice"].includes(question.question_type);
  const startChild = ({ triggerAnswer = null, option = null }) =>
    onAddChild?.({
      parentId: question.id,
      parentText: question.question_text,
      sectionId: question.section_id || "",
      triggerAnswer,
      triggerOptionId: option?.id ?? null,
      triggerLabel: triggerAnswer ? (triggerAnswer === "yes" ? "Có" : "Không") : option?.option_text,
    });
  const childCountFor = ({ triggerAnswer, optionId }) =>
    childQuestions.filter(
      (c) =>
        c.is_active &&
        (triggerAnswer ? c.trigger_answer === triggerAnswer : c.trigger_option_id === optionId)
    ).length;

  // Nhánh/phương án đang kích hoạt một câu hỏi phụ đang bật: điểm luôn lấy từ câu hỏi phụ
  // khi tính tổng, nên không cho nhập điểm ở đây nữa (tránh nhầm là điểm còn được dùng).
  const activeChildren = questions.filter((q) => q.is_active && q.parent_question_id === question.id);
  const yesLocked = activeChildren.some((c) => c.trigger_answer === "yes");
  const noLocked = activeChildren.some((c) => c.trigger_answer === "no");
  const lockedOptionIds = new Set(
    activeChildren.filter((c) => c.trigger_option_id).map((c) => c.trigger_option_id)
  );

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const notifyRevision = (data) => {
    if (data?.revised_from_id) {
      toast("Câu hỏi đã có phản hồi — đã tạo phiên bản mới, dữ liệu cũ vẫn được giữ nguyên.", { icon: "ℹ️" });
    }
  };

  const saveText = async () => {
    const trimmed = text.trim();
    if (!trimmed || trimmed === question.question_text) {
      setText(question.question_text);
      return;
    }
    try {
      const resp = await mutations.update.mutateAsync({ id: question.id, body: { question_text: trimmed } });
      notifyRevision(resp.data.data);
    } catch (err) {
      toast.error(apiErrorMessage(err));
      setText(question.question_text);
    }
  };

  const saveSection = async (sectionId) => {
    try {
      await mutations.update.mutateAsync({
        id: question.id,
        body: { section_id: sectionId ? Number(sectionId) : null },
      });
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const saveYesNoScores = async () => {
    const nextYes = yesLocked ? null : yesScore === "" ? null : Number(yesScore);
    const nextNo = noLocked ? null : noScore === "" ? null : Number(noScore);
    if (nextYes === (question.yes_score ?? null) && nextNo === (question.no_score ?? null)) return;
    try {
      const resp = await mutations.update.mutateAsync({
        id: question.id,
        body: { yes_score: nextYes, no_score: nextNo },
      });
      notifyRevision(resp.data.data);
    } catch (err) {
      toast.error(apiErrorMessage(err));
      setYesScore(question.yes_score ?? "");
      setNoScore(question.no_score ?? "");
    }
  };

  const saveDeductionSettings = async () => {
    const nextMax = maxScore === "" ? null : Number(maxScore);
    const nextZero = zeroScoreAt === "" ? null : Number(zeroScoreAt);
    if (nextMax === (question.max_score ?? null) && nextZero === (question.zero_score_at ?? null)) return;
    try {
      const resp = await mutations.update.mutateAsync({
        id: question.id,
        body: { max_score: nextMax, zero_score_at: nextZero },
      });
      notifyRevision(resp.data.data);
    } catch (err) {
      toast.error(apiErrorMessage(err));
      setMaxScore(question.max_score ?? "");
      setZeroScoreAt(question.zero_score_at ?? "");
    }
  };

  const changeScoringMode = async (mode) => {
    try {
      const resp = await mutations.update.mutateAsync({
        id: question.id,
        body: {
          scoring_mode: mode,
          max_score: mode === "deduction" ? question.max_score ?? 0 : null,
          zero_score_at: mode === "deduction" ? question.zero_score_at : null,
        },
      });
      notifyRevision(resp.data.data);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const unlinkParent = async () => {
    try {
      await mutations.update.mutateAsync({
        id: question.id,
        body: { parent_question_id: null, trigger_answer: null, trigger_option_id: null },
      });
      toast.success("Đã bỏ liên kết — câu hỏi trở thành câu hỏi thường");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const changeType = async (type) => {
    try {
      const resp = await mutations.update.mutateAsync({
        id: question.id,
        body: {
          question_type: type,
          options: QUESTION_TYPES_WITH_OPTIONS.has(type)
            ? hasOptions
              ? question.options.map((o) => ({ option_text: o.option_text, score: o.score }))
              : ["Phương án 1", "Phương án 2"].map((option_text) => ({ option_text, score: null }))
            : undefined,
        },
      });
      notifyRevision(resp.data.data);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const toggle = async (field, value) => {
    try {
      await mutations.update.mutateAsync({ id: question.id, body: { [field]: value } });
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const onDuplicate = async () => {
    try {
      await mutations.duplicate.mutateAsync(question.id);
      toast.success("Đã sao chép câu hỏi");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const onDelete = async () => {
    try {
      const resp = await mutations.remove.mutateAsync(question.id);
      toast.success(resp.data.data.hard_deleted ? "Đã xóa câu hỏi" : "Câu hỏi đã có phản hồi nên được ẩn thay vì xóa");
      setConfirmDelete(false);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const addOption = async () => {
    const t = newOption.trim();
    if (!t) return;
    const score = newOptionScore === "" ? null : Number(newOptionScore);
    try {
      await mutations.createOption.mutateAsync({
        questionId: question.id,
        body: { option_text: t, score },
      });
      setNewOption("");
      setNewOptionScore("");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const saveOption = async (option, body) => {
    try {
      const resp = await mutations.updateOption.mutateAsync({ id: option.id, body });
      if (resp.data.data.revised_from_id) {
        toast("Phương án đã có phản hồi — đã tạo phương án mới, dữ liệu cũ vẫn được giữ nguyên.", { icon: "ℹ️" });
      }
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const deleteOption = async (option) => {
    try {
      const resp = await mutations.removeOption.mutateAsync(option.id);
      toast.success(resp.data.data.hard_deleted ? "Đã xóa phương án" : "Phương án đã có phản hồi nên được ẩn");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const onOptionDragEnd = (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const ids = question.options.map((o) => `option-${o.id}`);
    const oldIndex = ids.indexOf(active.id);
    const newIndex = ids.indexOf(over.id);
    const reordered = arrayMove(question.options, oldIndex, newIndex);
    mutations.reorderOptions.mutate({
      questionId: question.id,
      items: reordered.map((o, i) => ({ id: o.id, sort_order: i + 1 })),
    });
  };

  return (
    <div ref={setNodeRef} style={style} className={`card min-w-0 p-4 ${!question.is_active ? "opacity-60" : ""}`}>
      <div className="flex items-start gap-2">
        {canManage && (
          <button
            type="button"
            className="mt-2 cursor-grab touch-none text-muted hover:text-ink-2 active:cursor-grabbing"
            aria-label="Kéo để đổi thứ tự câu hỏi"
            {...attributes}
            {...listeners}
          >
            <IconGrip size={18} />
          </button>
        )}
        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex flex-wrap items-center gap-2 text-xs font-medium text-muted">
            <button
              type="button"
              className="-ml-1 rounded px-1 text-sm text-muted hover:bg-paper-2 hover:text-ink-2"
              onClick={() => collapse?.toggle(question.id)}
              aria-expanded={!collapsed}
              aria-label={collapsed ? "Mở rộng câu hỏi" : "Thu gọn câu hỏi"}
              title={collapsed ? "Mở rộng" : "Thu gọn"}
            >
              {collapsed ? "▸" : "▾"}
            </button>
            <span>{nested ? "Câu phụ" : `Câu ${index + 1}`}</span>
            {!question.is_active && <span className="text-danger">(Đã tắt)</span>}
            {collapsed ? (
              <>
                <span className="text-[#cbd5e1]">·</span>
                <span>{QUESTION_TYPE_LABELS[question.question_type]}</span>
                {question.is_required && <span>· Bắt buộc</span>}
                {nested && triggerLabel && <span>· Khi trả lời «{triggerLabel}»</span>}
                {childQuestions.length > 0 && <span>· {childQuestions.length} câu phụ</span>}
              </>
            ) : canManage && !nested ? (
              <>
                <span className="text-[#cbd5e1]">·</span>
                <Select
                  className="h-7 w-56 py-0 text-xs"
                  value={question.section_id || ""}
                  onChange={(e) => saveSection(e.target.value)}
                >
                  <option value="">Không thuộc phần</option>
                  {sections.map((section) => (
                    <option key={section.id} value={section.id}>{section.title}</option>
                  ))}
                </Select>
              </>
            ) : (
              !nested && question.section && <span>· {question.section}</span>
            )}
          </div>

          {collapsed && (
            <p className="block truncate text-[0.95rem] font-medium text-ink">{question.question_text}</p>
          )}

          {!collapsed && (
          <>
          {question.parent_question_id && (
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-rule bg-paper-2 px-3 py-2 text-xs text-ink-2">
              <span>
                {nested ? "Chỉ hiển thị khi" : `Chỉ hiển thị khi «${parentQuestion?.question_text ?? "câu hỏi cha"}»`}{" "}
                trả lời <strong className="text-ink">«{triggerLabel ?? "?"}»</strong>. Điểm câu phụ thay điểm của đáp án đó.
              </span>
              {canManage && (
                <button type="button" className="shrink-0 text-danger hover:underline" onClick={unlinkParent}>
                  Bỏ liên kết
                </button>
              )}
            </div>
          )}

          <textarea
            className="input mb-3 text-[0.95rem] font-medium"
            rows={2}
            value={text}
            disabled={!canManage}
            onChange={(e) => setText(e.target.value)}
            onBlur={saveText}
          />

          <div className="mb-3 flex flex-wrap items-center gap-3">
            <Select
              value={question.question_type}
              onChange={(e) => changeType(e.target.value)}
              disabled={!canManage}
              className="w-48 py-1.5 text-sm"
            >
              {Object.entries(QUESTION_TYPE_LABELS).map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </Select>
            <label className="flex items-center gap-1.5 text-xs text-ink-2">
              <input
                type="checkbox"
                checked={question.is_required}
                disabled={!canManage}
                onChange={(e) => toggle("is_required", e.target.checked)}
              />
              Bắt buộc
            </label>
            <label className="flex items-center gap-1.5 text-xs text-ink-2">
              <input
                type="checkbox"
                checked={question.is_active}
                disabled={!canManage}
                onChange={(e) => toggle("is_active", e.target.checked)}
              />
              Đang bật
            </label>
          </div>

          {question.question_type === "yes_no" && (
            <div
              className="mb-3 grid grid-cols-2 gap-2 rounded-lg bg-paper-2 p-3"
              onBlur={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget)) saveYesNoScores();
              }}
            >
              <div>
                <label className="text-xs font-medium text-ink-2">
                  Điểm Có
                  <input
                    type="number"
                    step="any"
                    className="input mt-1 py-1.5 text-sm"
                    value={yesLocked ? "" : yesScore}
                    disabled={!canManage || yesLocked}
                    placeholder={yesLocked ? "Câu hỏi phụ" : undefined}
                    title={yesLocked ? "Điểm lấy từ câu hỏi phụ" : undefined}
                    onChange={(e) => setYesScore(e.target.value)}
                  />
                </label>
                {canAddChild && (
                  <button
                    type="button"
                    className="mt-1.5 text-xs font-medium text-accent-text hover:underline"
                    onClick={() => startChild({ triggerAnswer: "yes" })}
                  >
                    + Câu hỏi phụ khi trả lời «Có»
                    {childCountFor({ triggerAnswer: "yes" }) > 0 && ` (${childCountFor({ triggerAnswer: "yes" })})`}
                  </button>
                )}
              </div>
              <div>
                <label className="text-xs font-medium text-ink-2">
                  Điểm Không
                  <input
                    type="number"
                    step="any"
                    className="input mt-1 py-1.5 text-sm"
                    value={noLocked ? "" : noScore}
                    disabled={!canManage || noLocked}
                    placeholder={noLocked ? "Câu hỏi phụ" : undefined}
                    title={noLocked ? "Điểm lấy từ câu hỏi phụ" : undefined}
                    onChange={(e) => setNoScore(e.target.value)}
                  />
                </label>
                {canAddChild && (
                  <button
                    type="button"
                    className="mt-1.5 text-xs font-medium text-accent-text hover:underline"
                    onClick={() => startChild({ triggerAnswer: "no" })}
                  >
                    + Câu hỏi phụ khi trả lời «Không»
                    {childCountFor({ triggerAnswer: "no" }) > 0 && ` (${childCountFor({ triggerAnswer: "no" })})`}
                  </button>
                )}
              </div>
              {(yesLocked || noLocked) && (
                <p className="col-span-2 text-[11px] text-muted">
                  Nhánh đang có câu hỏi phụ lấy điểm từ câu hỏi phụ đó, không nhập điểm ở đây.
                </p>
              )}
            </div>
          )}

          {question.question_type === "multiple_choice" && (
            <div className="mb-3 grid grid-cols-[minmax(0,1fr)] gap-2 rounded-lg bg-paper-2 p-3">
              <label className="text-xs font-medium text-ink-2">
                Cách tính điểm
                <Select
                  className="mt-1"
                  value={question.scoring_mode || "standard"}
                  disabled={!canManage}
                  onChange={(e) => changeScoringMode(e.target.value)}
                >
                  <option value="standard">Điểm theo từng phương án đã chọn</option>
                  <option value="deduction">Trừ điểm từ điểm tối đa</option>
                </Select>
              </label>
              {question.scoring_mode === "deduction" && (
                <div
                  className="grid grid-cols-2 gap-2"
                  onBlur={(event) => {
                    if (!event.currentTarget.contains(event.relatedTarget)) saveDeductionSettings();
                  }}
                >
                  <label className="text-xs font-medium text-ink-2">
                    Điểm tối đa
                    <input
                      type="number"
                      step="any"
                      className="input mt-1 py-1.5 text-sm"
                      value={maxScore}
                      disabled={!canManage}
                      onChange={(e) => setMaxScore(e.target.value)}
                    />
                  </label>
                  <label className="text-xs font-medium text-ink-2">
                    Từ số lựa chọn thì về 0
                    <input
                      type="number"
                      min="1"
                      className="input mt-1 py-1.5 text-sm"
                      placeholder="Không dùng ngưỡng"
                      value={zeroScoreAt}
                      disabled={!canManage}
                      onChange={(e) => setZeroScoreAt(e.target.value)}
                    />
                  </label>
                </div>
              )}
              {question.scoring_mode === "deduction" && (
                <p className="text-[11px] text-muted">Không chọn phương án nào sẽ nhận trọn điểm tối đa.</p>
              )}
            </div>
          )}

          {hasOptions && (
            <div className="mb-3 ml-1 grid grid-cols-[minmax(0,1fr)] gap-1.5">
              <div
                className={`hidden gap-2 px-0.5 text-[11px] font-medium text-muted sm:grid ${
                  canAddChild
                    ? "grid-cols-[1rem_minmax(0,1fr)_5rem_6.5rem_1.5rem]"
                    : "grid-cols-[1rem_minmax(0,1fr)_5rem_1.5rem]"
                }`}
              >
                <span />
                <span>Nội dung phương án</span>
                <span>{question.scoring_mode === "deduction" ? "Điểm trừ" : "Điểm"}</span>
                {canAddChild && <span>Câu phụ</span>}
                <span />
              </div>
              {lockedOptionIds.size > 0 && (
                <p className="px-0.5 text-[11px] text-muted">
                  Phương án đang có câu hỏi phụ lấy điểm từ câu hỏi phụ đó, không nhập điểm ở đây.
                </p>
              )}
              <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onOptionDragEnd}>
                <SortableContext
                  items={question.options.map((o) => `option-${o.id}`)}
                  strategy={verticalListSortingStrategy}
                >
                  {question.options.map((o) => (
                    <OptionRow
                      key={o.id}
                      option={o}
                      disabled={!canManage}
                      onSave={(body) => saveOption(o, body)}
                      onDelete={() => deleteOption(o)}
                      scoreLabel={question.scoring_mode === "deduction" ? "Điểm trừ" : "Điểm"}
                      scoreLocked={lockedOptionIds.has(o.id)}
                      onAddChild={canAddChild && o.is_active ? () => startChild({ option: o }) : undefined}
                      childCount={childCountFor({ optionId: o.id })}
                    />
                  ))}
                </SortableContext>
              </DndContext>
              {canManage && (
                <div className="ml-6 flex items-center gap-2">
                  <input
                    className="input flex-1 py-1.5 text-sm"
                    placeholder="+ Thêm phương án"
                    value={newOption}
                    onChange={(e) => setNewOption(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addOption()}
                  />
                  <input
                    type="number"
                    step="any"
                    className="input w-20 shrink-0 py-1.5 text-sm"
                    placeholder={question.scoring_mode === "deduction" ? "Điểm trừ" : "Điểm"}
                    aria-label="Điểm phương án mới"
                    value={newOptionScore}
                    onChange={(e) => setNewOptionScore(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addOption()}
                  />
                  <Button variant="secondary" className="px-2.5 py-1 text-xs" onClick={addOption}>
                    Thêm
                  </Button>
                </div>
              )}
            </div>
          )}

          {childQuestions.length > 0 && (
            <div className="mt-1 grid grid-cols-[minmax(0,1fr)] gap-3 border-l-2 border-rule pl-3">
              <p className="text-xs font-medium text-muted">
                Câu hỏi phụ ({childQuestions.filter((c) => c.is_active).length} đang bật)
              </p>
              {childQuestions.map((child) => (
                <QuestionCard
                  key={child.id}
                  question={child}
                  mutations={mutations}
                  canManage={canManage}
                  index={0}
                  sections={sections}
                  questions={questions}
                  nested
                  collapse={collapse}
                />
              ))}
            </div>
          )}
          </>
          )}
        </div>

        {canManage && (
          <div className="flex shrink-0 gap-1">
            <button
              type="button"
              className="inline-flex items-center gap-1 rounded-md px-2 py-1.5 text-xs text-muted hover:bg-paper-2 hover:text-ink-2"
              onClick={onDuplicate}
              aria-label="Sao chép câu hỏi"
              title="Sao chép câu hỏi"
            >
              <IconCopy size={16} />
              <span>Sao chép</span>
            </button>
            <button
              type="button"
              className="rounded-md p-1.5 text-muted hover:bg-[color:var(--color-danger-quiet)] hover:text-danger"
              onClick={() => setConfirmDelete(true)}
              aria-label="Xóa câu hỏi"
              title="Xóa câu hỏi"
            >
              <IconTrash size={16} />
            </button>
          </div>
        )}
      </div>

      <ConfirmDialog
        open={confirmDelete}
        onClose={() => setConfirmDelete(false)}
        onConfirm={onDelete}
        loading={mutations.remove.isPending}
        title="Xóa câu hỏi"
        message="Nếu câu hỏi đã có phản hồi, hệ thống sẽ tắt hoạt động thay vì xóa để không làm sai lệch thống kê."
        confirmText="Xóa"
      />
    </div>
  );
}
