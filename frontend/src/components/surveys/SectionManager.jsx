import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { apiErrorMessage } from "../../lib/api";
import { Button, TextInput } from "../ui/primitives";
import { IconTrash } from "../ui/icons";

function SectionRow({ section, index, total, mutations }) {
  const [title, setTitle] = useState(section.title);
  useEffect(() => setTitle(section.title), [section.title]);

  const save = async () => {
    const value = title.trim();
    if (!value || value === section.title) {
      setTitle(section.title);
      return;
    }
    try {
      await mutations.update.mutateAsync({ id: section.id, body: { title: value } });
    } catch (error) {
      toast.error(apiErrorMessage(error));
      setTitle(section.title);
    }
  };

  const move = async (offset) => {
    const nextIndex = index + offset;
    if (nextIndex < 0 || nextIndex >= total.length) return;
    const reordered = [...total];
    [reordered[index], reordered[nextIndex]] = [reordered[nextIndex], reordered[index]];
    try {
      await mutations.reorder.mutateAsync(
        reordered.map((item, order) => ({ id: item.id, sort_order: order + 1 }))
      );
    } catch (error) {
      toast.error(apiErrorMessage(error));
    }
  };

  const remove = async () => {
    try {
      await mutations.remove.mutateAsync(section.id);
      toast.success("Đã xóa phần");
    } catch (error) {
      toast.error(apiErrorMessage(error));
    }
  };

  return (
    <div className="flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-2">
      <span className="w-7 shrink-0 text-xs font-semibold text-muted">{index + 1}</span>
      <TextInput
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        onBlur={save}
        onKeyDown={(event) => event.key === "Enter" && event.currentTarget.blur()}
        className="py-1.5 text-sm"
      />
      <span className="whitespace-nowrap text-xs text-muted">{section.question_count} câu</span>
      <button type="button" onClick={() => move(-1)} disabled={index === 0} className="px-1 text-muted disabled:opacity-30" title="Đưa lên">↑</button>
      <button type="button" onClick={() => move(1)} disabled={index === total.length - 1} className="px-1 text-muted disabled:opacity-30" title="Đưa xuống">↓</button>
      <button type="button" onClick={remove} className="p-1 text-muted hover:text-danger" title="Xóa phần">
        <IconTrash size={15} />
      </button>
    </div>
  );
}

export function SectionManager({ sections, mutations }) {
  const [title, setTitle] = useState("");
  const [collapsed, setCollapsed] = useState(false);

  const create = async () => {
    const value = title.trim();
    if (!value) return;
    try {
      await mutations.create.mutateAsync({ title: value });
      setTitle("");
      toast.success("Đã tạo phần khảo sát");
    } catch (error) {
      toast.error(apiErrorMessage(error));
    }
  };

  return (
    <div className="card mb-5 p-4">
      <div className={`flex items-start gap-2 ${collapsed ? "" : "mb-3"}`}>
        <button
          type="button"
          className="rounded px-1.5 py-0.5 text-base text-muted hover:bg-paper-2 hover:text-ink-2"
          onClick={() => setCollapsed((c) => !c)}
          aria-expanded={!collapsed}
          aria-label={collapsed ? "Mở rộng khung các phần" : "Thu gọn khung các phần"}
        >
          {collapsed ? "▸" : "▾"}
        </button>
        <div className="min-w-0 flex-1">
          <h3 className="font-display text-sm font-semibold text-ink">
            Các phần của khảo sát{sections.length > 0 ? ` (${sections.length})` : ""}
          </h3>
          {!collapsed && (
            <p className="mt-0.5 text-xs text-muted">
              Tạo phần ở đây; mỗi phần sẽ hiện thành một khối riêng bên dưới, bấm “+ Thêm câu hỏi”
              trong khối đó hoặc kéo câu hỏi vào để đưa câu hỏi về đúng phần.
            </p>
          )}
        </div>
      </div>
      {!collapsed && (
        <>
          <div className="mb-3 grid gap-2">
            {sections.map((section, index) => (
              <SectionRow key={section.id} section={section} index={index} total={sections} mutations={mutations} />
            ))}
          </div>
          <div className="flex gap-2">
            <TextInput
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && create()}
              placeholder="Tên phần mới, ví dụ: Phần 1. Tiếp cận dịch vụ"
            />
            <Button variant="secondary" onClick={create} disabled={mutations.create.isPending}>+ Tạo phần</Button>
          </div>
        </>
      )}
    </div>
  );
}
