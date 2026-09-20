import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { DndContext } from "@dnd-kit/core";
import { SortableContext } from "@dnd-kit/sortable";
import { QuestionCard } from "../components/surveys/QuestionCard";

const noop = { mutateAsync: vi.fn(), isPending: false, mutate: vi.fn() };
const mutations = new Proxy({}, { get: () => noop });

function renderCard(props) {
  return render(
    <DndContext>
      <SortableContext items={["question-1"]}>
        <QuestionCard mutations={mutations} canManage index={0} sections={[]} {...props} />
      </SortableContext>
    </DndContext>
  );
}

const yesNo = {
  id: 1, question_text: "Hồ sơ đúng hạn?", question_type: "yes_no", is_required: true,
  is_active: true, options: [], parent_question_id: null,
};
const child = {
  id: 2, question_text: "Vì sao trễ?", question_type: "text", is_required: true,
  is_active: true, options: [], parent_question_id: 1, trigger_answer: "no",
};

describe("QuestionCard câu hỏi phụ theo đáp án", () => {
  it("nút câu phụ của Có/Không mở đúng đáp án được bấm", () => {
    const onAddChild = vi.fn();
    renderCard({ question: yesNo, questions: [yesNo, child], onAddChild });
    fireEvent.click(screen.getByText(/Câu hỏi phụ khi trả lời «Không»/));
    expect(onAddChild).toHaveBeenCalledWith(
      expect.objectContaining({ parentId: 1, triggerAnswer: "no", triggerLabel: "Không" })
    );
    fireEvent.click(screen.getByText(/Câu hỏi phụ khi trả lời «Có»/));
    expect(onAddChild).toHaveBeenLastCalledWith(
      expect.objectContaining({ parentId: 1, triggerAnswer: "yes", triggerLabel: "Có" })
    );
  });

  it("câu phụ lồng trong câu cha và nói rõ đáp án kích hoạt", () => {
    renderCard({ question: yesNo, questions: [yesNo, child], onAddChild: vi.fn() });
    expect(screen.getByDisplayValue("Vì sao trễ?")).toBeTruthy();
    expect(screen.getByText(/«Không»/, { selector: "strong" })).toBeTruthy();
  });

  it("thu gọn chỉ còn tiêu đề", () => {
    const toggle = vi.fn();
    renderCard({
      question: yesNo, questions: [yesNo, child],
      collapse: { ids: new Set([1]), toggle },
    });
    expect(screen.queryByDisplayValue("Hồ sơ đúng hạn?")).toBeNull();
    expect(screen.getByText("Hồ sơ đúng hạn?")).toBeTruthy();
    fireEvent.click(screen.getByLabelText("Mở rộng câu hỏi"));
    expect(toggle).toHaveBeenCalledWith(1);
  });
});
