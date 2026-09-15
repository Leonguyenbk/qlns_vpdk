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

export function QuestionCard({ question, mutations, canManage, index, sectionOptions = [] }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: `question-${question.id}`,
  });
  const [text, setText] = useState(question.question_text);
  const [sectionText, setSectionText] = useState(question.section || "");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [newOption, setNewOption] = useState("");
  const hasOptions = QUESTION_TYPES_WITH_OPTIONS.has(question.question_type);

  useEffect(() => setText(question.question_text), [question.question_text]);
  useEffect(() => setSectionText(question.section || ""), [question.section]);

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

  const saveSection = async () => {
    const trimmed = sectionText.trim();
    if (trimmed === (question.section || "")) return;
    try {
      await mutations.update.mutateAsync({ id: question.id, body: { section: trimmed || null } });
    } catch (err) {
      toast.error(apiErrorMessage(err));
      setSectionText(question.section || "");
    }
  };

  const changeType = async (type) => {
    try {
      const resp = await mutations.update.mutateAsync({
        id: question.id,
        body: {
          question_type: type,
          options: QUESTION_TYPES_WITH_OPTIONS.has(type)
            ? (hasOptions ? question.options.map((o) => o.option_text) : ["Phương án 1", "Phương án 2"]).map(
                (t) => ({ option_text: t })
              )
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
    try {
      await mutations.createOption.mutateAsync({ questionId: question.id, body: { option_text: t } });
      setNewOption("");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const saveOption = async (option, text2) => {
    try {
      const resp = await mutations.updateOption.mutateAsync({ id: option.id, body: { option_text: text2 } });
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
    <div ref={setNodeRef} style={style} className={`card p-4 ${!question.is_active ? "opacity-60" : ""}`}>
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
            <span>Câu {index + 1}</span>
            {!question.is_active && <span className="text-danger">(Đã tắt)</span>}
            {canManage ? (
              <>
                <span className="text-[#cbd5e1]">·</span>
                <input
                  list={`section-options-${question.id}`}
                  className="input h-6 w-56 py-0 text-xs"
                  placeholder="Thuộc phần (tuỳ chọn)"
                  value={sectionText}
                  onChange={(e) => setSectionText(e.target.value)}
                  onBlur={saveSection}
                />
                {sectionOptions.length > 0 && (
                  <datalist id={`section-options-${question.id}`}>
                    {sectionOptions.map((s) => (
                      <option key={s} value={s} />
                    ))}
                  </datalist>
                )}
              </>
            ) : (
              question.section && <span>· {question.section}</span>
            )}
          </div>
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

          {hasOptions && (
            <div className="mb-3 ml-1 grid gap-1.5">
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
                      onSave={(t) => saveOption(o, t)}
                      onDelete={() => deleteOption(o)}
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
                  <Button variant="secondary" className="px-2.5 py-1 text-xs" onClick={addOption}>
                    Thêm
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>

        {canManage && (
          <div className="flex shrink-0 gap-1">
            <button
              type="button"
              className="rounded-md p-1.5 text-muted hover:bg-paper-2 hover:text-ink-2"
              onClick={onDuplicate}
              aria-label="Sao chép câu hỏi"
              title="Sao chép câu hỏi"
            >
              <IconCopy size={16} />
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
