import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { Button } from "../ui/primitives";

/** Một "Phần" khảo sát: tiêu đề + các câu hỏi của phần đó, thu gọn được.
 * Kéo câu hỏi vào phần khác để chuyển phần — không cần chọn từng câu. */
export function SectionGroup({ group, collapsed, onToggle, canManage, onAdd, plain = false, children }) {
  const { setNodeRef, isOver } = useDroppable({ id: `section-${group.key}` });
  const count = group.items.length;

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
        <h3 className="min-w-0 flex-1 truncate font-display text-sm font-semibold text-ink">
          {group.title}
        </h3>
        <span className="whitespace-nowrap text-xs text-muted">{count} câu hỏi</span>
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
    </section>
  );
}
