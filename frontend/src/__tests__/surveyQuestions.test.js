import { describe, expect, it } from "vitest";
import {
  filledFieldAnswers,
  isQuestionAnswered,
  isQuestionVisible,
  missingRequiredFields,
  questionValue,
} from "../lib/surveyQuestions";

describe("survey question conditions", () => {
  it("shows a yes/no child only for its configured answer", () => {
    const child = { parent_question_id: 10, trigger_answer: "no" };
    expect(isQuestionVisible(child, { 10: "yes" })).toBe(false);
    expect(isQuestionVisible(child, { 10: "no" })).toBe(true);
  });

  it("supports option-triggered children", () => {
    const child = { parent_question_id: 10, trigger_option_id: 22 };
    expect(isQuestionVisible(child, { 10: 22 })).toBe(true);
    expect(isQuestionVisible(child, { 10: [21, 22] })).toBe(true);
    expect(isQuestionVisible(child, { 10: [21] })).toBe(false);
  });

  it("treats an empty deduction answer as a valid full-score answer", () => {
    const question = { id: 1, question_type: "multiple_choice", scoring_mode: "deduction" };
    expect(questionValue(question, {})).toEqual([]);
    expect(isQuestionAnswered(question, [])).toBe(true);
  });
});

describe("câu hỏi nhiều ô nhập (text_fields)", () => {
  const question = {
    id: 7,
    question_type: "text_fields",
    options: [
      { id: 1, option_text: "Họ và tên", is_required: true, is_active: true },
      { id: 2, option_text: "CCCD", is_required: true, is_active: true },
      { id: 3, option_text: "Địa chỉ", is_required: false, is_active: true },
      { id: 4, option_text: "Ô cũ", is_required: true, is_active: false },
    ],
  };

  it("chỉ lấy ô đã điền (bỏ khoảng trắng) theo đúng thứ tự ô", () => {
    expect(filledFieldAnswers(question, { 2: " 0123 ", 1: "An", 3: "   " })).toEqual([
      { option_id: 1, answer_text: "An" },
      { option_id: 2, answer_text: "0123" },
    ]);
  });

  it("báo các ô bắt buộc còn trống, bỏ qua ô đã ẩn và ô không bắt buộc", () => {
    expect(missingRequiredFields(question, { 1: "An" })).toEqual(["CCCD"]);
    expect(missingRequiredFields(question, { 1: "An", 2: "1" })).toEqual([]);
  });

  it("chưa trả lời khi mọi ô trống, giá trị mặc định là object rỗng", () => {
    expect(isQuestionAnswered(question, {})).toBe(false);
    expect(isQuestionAnswered(question, { 3: "Đà Nẵng" })).toBe(true);
    expect(questionValue(question, {})).toEqual({});
  });
});
