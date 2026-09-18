import { useEffect, useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { IconGrip, IconTrash } from "../ui/icons";

export function OptionRow({ option, onSave, onDelete, disabled }) {
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
    const nextScore = score === "" ? null : Number(score);
    if (!nextText) {
      setText(option.option_text);
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
      <input
        type="number"
        min="0"
        max="5"
        step="0.01"
        className="input w-20 shrink-0 py-1.5 text-sm"
        value={score}
        disabled={disabled}
        aria-label={`Điểm cho ${option.option_text}`}
        placeholder="Điểm"
        onChange={(e) => setScore(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
      />
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
