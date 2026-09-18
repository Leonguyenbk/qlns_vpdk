import { describe, expect, it } from "vitest";
import { isQuestionAnswered, isQuestionVisible, questionValue } from "../lib/surveyQuestions";

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
