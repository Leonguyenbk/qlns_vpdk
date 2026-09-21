import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { QuestionRenderer } from "../components/surveys/QuestionRenderer";

const question = {
  id: 7,
  question_text: "Thông tin người được khảo sát",
  question_type: "text_fields",
  options: [
    { id: 1, option_text: "Họ và tên", is_required: true },
    { id: 2, option_text: "Địa chỉ", is_required: false },
  ],
};

describe("QuestionRenderer text_fields", () => {
  it("hiện mỗi ô một nhãn, đánh dấu * ở ô bắt buộc", () => {
    render(<QuestionRenderer question={question} value={{}} onChange={() => {}} />);
    expect(screen.getAllByRole("textbox")).toHaveLength(2);
    expect(screen.getByText("Họ và tên").parentElement.textContent).toContain("*");
    expect(screen.getByText("Địa chỉ").parentElement.textContent).not.toContain("*");
  });

  it("gộp giá trị các ô thành object theo option_id khi gõ", () => {
    const onChange = vi.fn();
    render(<QuestionRenderer question={question} value={{ 2: "Đà Nẵng" }} onChange={onChange} />);
    fireEvent.change(screen.getAllByRole("textbox")[0], { target: { value: "An" } });
    expect(onChange).toHaveBeenCalledWith({ 1: "An", 2: "Đà Nẵng" });
  });
});
