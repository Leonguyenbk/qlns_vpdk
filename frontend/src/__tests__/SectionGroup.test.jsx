import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { DndContext } from "@dnd-kit/core";
import { SectionGroup } from "../components/surveys/SectionGroup";

const group = { key: "s1", id: 1, title: "Phần 1. Tiếp nhận", items: [{ id: 1 }, { id: 2 }] };

function renderGroup(props) {
  return render(
    <DndContext>
      <SectionGroup group={group} canManage onToggle={vi.fn()} onAdd={vi.fn()} {...props}>
        <div>câu 1</div>
        <div>câu 2</div>
      </SectionGroup>
    </DndContext>
  );
}

describe("SectionGroup", () => {
  it("hiện tiêu đề, số câu và câu hỏi của phần", () => {
    renderGroup({ collapsed: false });
    expect(screen.getByText("Phần 1. Tiếp nhận")).toBeTruthy();
    expect(screen.getByText("2 câu hỏi")).toBeTruthy();
    expect(screen.getByText("câu 1")).toBeTruthy();
  });

  it("thu gọn ẩn câu hỏi, nút thêm gọi đúng phần", () => {
    const onToggle = vi.fn();
    const onAdd = vi.fn();
    renderGroup({ collapsed: true, onToggle, onAdd });
    expect(screen.queryByText("câu 1")).toBeNull();
    fireEvent.click(screen.getByLabelText(/Mở rộng phần/));
    expect(onToggle).toHaveBeenCalled();
    fireEvent.click(screen.getByText("+ Thêm câu hỏi"));
    expect(onAdd).toHaveBeenCalled();
  });

  it("phần trống hiện gợi ý", () => {
    renderGroup({ collapsed: false, group: { ...group, items: [] }, children: null });
    expect(screen.getByText(/Chưa có câu hỏi trong phần này/)).toBeTruthy();
  });
});
