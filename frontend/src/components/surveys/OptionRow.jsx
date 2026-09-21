import { useEffect, useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { IconGrip, IconTrash } from "../ui/icons";

export function OptionRow({
  option,
  onSave,
  onDelete,
  disabled,
  scoreLabel = "Điểm",
  scoreLocked = false,
  scoreLockedHint = "Câu hỏi phụ",
  onAddChild,
  childCount = 0,
  fieldMode = false,
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: `option-${option.id}`,
  });
  const [text, setText] = useState(option.option_text);
  const [score, setScore] = useState(option.score ?? "");

  useEffect(() => setText(option.option_text), [option.option_text]);
  useEffect(() => setScore(option.score ?? ""), [option.score]);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const commit = () => {
    const nextText = text.trim();
    const nextScore = scoreLocked ? null : score === "" ? null : Number(score);
    if (!nextText) {
      setText(option.option_text);
      return;
    }
    if (fieldMode) {
      if (nextText !== option.option_text) onSave({ option_text: nextText });
      return;
    }
    if (nextText !== option.option_text || nextScore !== (option.score ?? null)) {
      onSave({ option_text: nextText, score: nextScore });
    }
  };

  const onRowBlur = (event) => {
    if (event.currentTarget.contains(event.relatedTarget)) return;
    commit();
  };

  return (
    <div ref={setNodeRef} style={style} className="flex items-center gap-2" onBlur={onRowBlur}>
      <button
        type="button"
        className="cursor-grab touch-none text-muted hover:text-ink-2 active:cursor-grabbing"
        aria-label="Kéo để đổi thứ tự"
        disabled={disabled}
        {...attributes}
        {...listeners}
      >
        <IconGrip size={16} />
      </button>
      <input
        className="input flex-1 py-1.5 text-sm"
        value={text}
        disabled={disabled}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
      />
      {fieldMode ? (
        <label className="flex w-[5.5rem] shrink-0 items-center gap-1.5 text-xs text-ink-2">
          <input
            type="checkbox"
            checked={!!option.is_required}
            disabled={disabled}
            onChange={(e) => onSave({ is_required: e.target.checked })}
          />
          Bắt buộc
        </label>
      ) : (
      <input
        type="number"
        step="any"
        className="input w-20 shrink-0 py-1.5 text-sm"
        value={scoreLocked ? "" : score}
        disabled={disabled || scoreLocked}
        aria-label={
          scoreLocked
            ? `${scoreLockedHint}, không nhập điểm cho ${option.option_text}`
            : `${scoreLabel} cho ${option.option_text}`
        }
        title={scoreLocked ? `Điểm lấy từ ${scoreLockedHint.toLowerCase()}` : undefined}
        placeholder={scoreLocked ? scoreLockedHint : scoreLabel}
        onChange={(e) => setScore(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
      />
      )}
      {onAddChild && (
        <button
          type="button"
          className="w-[6.5rem] shrink-0 whitespace-nowrap text-left text-xs font-medium text-accent-text hover:underline"
          onClick={onAddChild}
          title="Thêm câu hỏi chỉ hiện khi người trả lời chọn đáp án này"
        >
          + Câu phụ{childCount > 0 ? ` (${childCount})` : ""}
        </button>
      )}
      <button
        type="button"
        className="p-1 text-muted hover:text-danger disabled:opacity-40"
        onClick={onDelete}
        disabled={disabled}
        aria-label="Xóa phương án"
      >
        <IconTrash size={15} />
      </button>
    </div>
  );
}
