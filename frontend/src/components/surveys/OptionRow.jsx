import { useEffect, useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { IconGrip, IconTrash } from "../ui/icons";

export function OptionRow({ option, onSave, onDelete, disabled }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: `option-${option.id}`,
  });
  const [text, setText] = useState(option.option_text);

  useEffect(() => setText(option.option_text), [option.option_text]);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className="flex items-center gap-2">
      <button
        type="button"
        className="cursor-grab touch-none text-muted hover:text-ink-2 active:cursor-grabbing"
        aria-label="Kéo để đổi thứ tự"
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
        onBlur={() => text.trim() && text !== option.option_text && onSave(text.trim())}
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
