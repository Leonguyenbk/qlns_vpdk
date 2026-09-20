import { useEffect, useState } from "react";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { Button } from "../ui/primitives";
import { IconTrash } from "../ui/icons";
import { ConfirmDialog } from "../ui/Modal";

/** Một "Phần" khảo sát: tiêu đề + các câu hỏi của phần đó, thu gọn được.
 * Tạo phần nào thì thêm câu hỏi ngay trong phần đó; kéo câu hỏi sang phần khác để chuyển phần. */
export function SectionGroup({
  group,
  collapsed,
  onToggle,
  canManage,
  onAdd,
  plain = false,
  onRename,
  onMove,
  onDelete,
  isFirst = false,
  isLast = false,
  children,
}) {
  const { setNodeRef, isOver } = useDroppable({ id: `section-${group.key}` });
  const [title, setTitle] = useState(group.title);
  const [confirmDelete, setConfirmDelete] = useState(false);
  useEffect(() => setTitle(group.title), [group.title]);
  const count = group.items.length;
  const editable = canManage && group.id != null;

  const saveTitle = () => {
    const value = title.trim();
    if (!value || value === group.title) {
      setTitle(group.title);
      return;
    }
    onRename?.(value);
  };

  if (plain) {
    return (
      <div ref={setNodeRef}>
        <SortableContext
          items={group.items.map((q) => `question-${q.id}`)}
          strategy={verticalListSortingStrategy}
        >
          <div className="grid grid-cols-[minmax(0,1fr)] gap-4">{children}</div>
        </SortableContext>
      </div>
    );
  }

  return (
    <section
      ref={setNodeRef}
      aria-label={group.title}
      className={`min-w-0 rounded-xl border bg-paper-2/40 p-3 transition-colors ${
        isOver ? "border-[color:var(--color-accent)]" : "border-rule"
      }`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          className="rounded px-1.5 py-0.5 text-base text-muted hover:bg-paper-2 hover:text-ink-2"
          onClick={onToggle}
          aria-expanded={!collapsed}
          aria-label={collapsed ? `Mở rộng phần ${group.title}` : `Thu gọn phần ${group.title}`}
        >
          {collapsed ? "▸" : "▾"}
        </button>
        {editable ? (
          <input
            className="input min-w-0 flex-1 py-1 text-sm font-semibold"
            value={title}
            aria-label="Tên phần"
            onChange={(e) => setTitle(e.target.value)}
            onBlur={saveTitle}
            onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
          />
        ) : (
          <h3 className="min-w-0 flex-1 truncate font-display text-sm font-semibold text-ink">
            {group.title}
          </h3>
        )}
        <span className="whitespace-nowrap text-xs text-muted">{count} câu hỏi</span>
        {editable && (
          <>
            <button
              type="button"
              className="px-1 text-muted disabled:opacity-30"
              onClick={() => onMove?.(-1)}
              disabled={isFirst}
              title="Đưa phần lên"
              aria-label="Đưa phần lên"
            >
              ↑
            </button>
            <button
              type="button"
              className="px-1 text-muted disabled:opacity-30"
              onClick={() => onMove?.(1)}
              disabled={isLast}
              title="Đưa phần xuống"
              aria-label="Đưa phần xuống"
            >
              ↓
            </button>
            <button
              type="button"
              className="p-1 text-muted hover:text-danger"
              onClick={() => setConfirmDelete(true)}
              title="Xóa phần"
              aria-label="Xóa phần"
            >
              <IconTrash size={15} />
            </button>
          </>
        )}
        {canManage && (
          <Button variant="secondary" className="px-2.5 py-1 text-xs" onClick={onAdd}>
            + Thêm câu hỏi
          </Button>
        )}
      </div>

      {!collapsed && (
        <SortableContext
          items={group.items.map((q) => `question-${q.id}`)}
          strategy={verticalListSortingStrategy}
        >
          <div className="mt-3 grid grid-cols-[minmax(0,1fr)] gap-3">
            {count === 0 ? (
              <p className="rounded-lg border border-dashed border-rule px-3 py-4 text-center text-xs text-muted">
                Chưa có câu hỏi trong phần này — bấm “+ Thêm câu hỏi” hoặc kéo câu hỏi từ phần khác vào đây.
              </p>
            ) : (
              children
            )}
          </div>
        </SortableContext>
      )}

      <ConfirmDialog
        open={confirmDelete}
        onClose={() => setConfirmDelete(false)}
        onConfirm={() => {
          setConfirmDelete(false);
          onDelete?.();
        }}
        title="Xóa phần"
        message="Xóa phần này? Các câu hỏi trong phần sẽ chuyển sang “Chưa thuộc phần nào”, không bị xóa."
        confirmText="Xóa phần"
      />
    </section>
  );
}
