import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SurveyQuestionList } from "../components/surveys/SurveyQuestionList";

const q = (id, text, section, extra = {}) => ({
  id,
  question_text: text,
  question_type: "text",
  section,
  ...extra,
});

describe("SurveyQuestionList", () => {
  it("chèn tiêu đề mỗi khi sang Phần mới, giữ đúng thứ tự câu hỏi", () => {
    render(
      <SurveyQuestionList
        questions={[q(1, "Họ tên", "Thông tin người được khảo sát"), q(2, "SĐT", "Thông tin người được khảo sát"), q(3, "Thái độ", "Đánh giá")]}
        answers={{}}
        onChange={() => {}}
      />
    );
    const headings = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(headings).toEqual(["Thông tin người được khảo sát", "Đánh giá"]);
  });

  it("không hiện tiêu đề khi khảo sát không có Phần, câu phụ không lặp tiêu đề", () => {
    const { rerender } = render(
      <SurveyQuestionList questions={[q(1, "A", null)]} answers={{}} onChange={() => {}} />
    );
    expect(screen.queryAllByRole("heading", { level: 2 })).toHaveLength(0);

    rerender(
      <SurveyQuestionList
        questions={[q(1, "A", "Phần 1"), q(2, "A phụ", "Phần 1", { parent_question_id: 1 })]}
        answers={{}}
        onChange={() => {}}
      />
    );
    expect(screen.getAllByRole("heading", { level: 2 })).toHaveLength(1);
  });
});
