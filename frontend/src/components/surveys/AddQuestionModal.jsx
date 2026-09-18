import { useState } from "react";
import toast from "react-hot-toast";
import { Modal } from "../ui/Modal";
import { Button, FormField, Select, Textarea, TextInput } from "../ui/primitives";
import { QUESTION_TYPE_LABELS, QUESTION_TYPES_WITH_OPTIONS } from "../../lib/constants";
import { apiErrorMessage } from "../../lib/api";
import { IconTrash } from "../ui/icons";

const EMPTY = {
  question_text: "",
  question_type: "single_choice",
  is_required: false,
  section_id: "",
  yes_score: "",
  no_score: "",
};

export function AddQuestionModal({ open, onClose, onCreate, existingQuestions = [], sections = [] }) {
  const lastSectionId = existingQuestions[existingQuestions.length - 1]?.section_id || "";
  const [form, setForm] = useState({ ...EMPTY, section_id: lastSectionId });
  const [options, setOptions] = useState([
    { option_text: "", score: "" },
    { option_text: "", score: "" },
  ]);
  const [copyFromId, setCopyFromId] = useState("");
  const [saving, setSaving] = useState(false);
  const hasOptions = QUESTION_TYPES_WITH_OPTIONS.has(form.question_type);

  const sourceQuestions = existingQuestions.filter((q) => q.is_active);

  const reset = () => {
    setForm({ ...EMPTY, section_id: lastSectionId });
    setOptions([
      { option_text: "", score: "" },
      { option_text: "", score: "" },
    ]);
    setCopyFromId("");
  };

  const copyQuestionFrom = (questionId) => {
    setCopyFromId(questionId);
    const source = sourceQuestions.find((q) => String(q.id) === String(questionId));
    if (!source) return;
    setForm({
      question_text: source.question_text,
      question_type: source.question_type,
      is_required: source.is_required,
      section_id: source.section_id || "",
      yes_score: source.yes_score ?? "",
      no_score: source.no_score ?? "",
    });
    const copied = source.options
      .filter((o) => o.is_active)
      .map((o) => ({ option_text: o.option_text, score: o.score ?? "" }));
    setOptions(copied.length ? copied : [{ option_text: "", score: "" }, { option_text: "", score: "" }]);
  };

  const submit = async () => {
    if (!form.question_text.trim()) {
      toast.error("Nhập nội dung câu hỏi");
      return;
    }
    const opts = options
      .map((o) => ({
        option_text: o.option_text.trim(),
        score: o.score === "" ? null : Number(o.score),
      }))
      .filter((o) => o.option_text);
    if (hasOptions && opts.length < 2) {
      toast.error("Cần ít nhất 2 phương án trả lời");
      return;
    }
    setSaving(true);
    try {
      await onCreate({
        question_text: form.question_text.trim(),
        question_type: form.question_type,
        is_required: form.is_required,
        section_id: form.section_id ? Number(form.section_id) : null,
        yes_score:
          form.question_type === "yes_no" && form.yes_score !== "" ? Number(form.yes_score) : null,
        no_score:
          form.question_type === "yes_no" && form.no_score !== "" ? Number(form.no_score) : null,
        options: hasOptions ? opts : [],
      });
      reset();
      onClose();
    } catch (err) {
      toast.error(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Thêm câu hỏi"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Hủy
          </Button>
          <Button onClick={submit} disabled={saving}>
            {saving ? "Đang lưu…" : "Thêm câu hỏi"}
          </Button>
        </>
      }
    >
      <div className="grid gap-4">
        {sourceQuestions.length > 0 && (
          <FormField label="Sao chép câu hỏi để sửa tiếp" hint="Sao chép cả nội dung, loại câu hỏi, đáp án và điểm">
            <Select value={copyFromId} onChange={(e) => copyQuestionFrom(e.target.value)}>
              <option value="">-- Chọn câu hỏi có sẵn --</option>
              {sourceQuestions.map((q) => (
                <option key={q.id} value={q.id}>
                  {q.question_text.length > 70 ? `${q.question_text.slice(0, 70)}…` : q.question_text}
                </option>
              ))}
            </Select>
          </FormField>
        )}
        <FormField label="Phần">
          <Select
            value={form.section_id}
            onChange={(e) => setForm((f) => ({ ...f, section_id: e.target.value }))}
          >
            <option value="">Không thuộc phần nào</option>
            {sections.map((section) => (
              <option key={section.id} value={section.id}>{section.title}</option>
            ))}
          </Select>
        </FormField>
        <FormField label="Nội dung câu hỏi" required>
          <Textarea
            rows={2}
            value={form.question_text}
            onChange={(e) => setForm((f) => ({ ...f, question_text: e.target.value }))}
          />
        </FormField>
        <FormField label="Loại câu hỏi">
          <Select
            value={form.question_type}
            onChange={(e) => setForm((f) => ({ ...f, question_type: e.target.value }))}
          >
            {Object.entries(QUESTION_TYPE_LABELS).map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </Select>
        </FormField>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.is_required}
            onChange={(e) => setForm((f) => ({ ...f, is_required: e.target.checked }))}
          />
          Bắt buộc trả lời
        </label>

        {form.question_type === "yes_no" && (
          <FormField label="Điểm cho đáp án Có / Không" hint="Có thể để trống nếu câu hỏi này không tính điểm">
            <div className="grid grid-cols-2 gap-3">
              <TextInput
                type="number"
                step="any"
                value={form.yes_score}
                placeholder="Điểm Có"
                onChange={(e) => setForm((f) => ({ ...f, yes_score: e.target.value }))}
              />
              <TextInput
                type="number"
                step="any"
                value={form.no_score}
                placeholder="Điểm Không"
                onChange={(e) => setForm((f) => ({ ...f, no_score: e.target.value }))}
              />
            </div>
          </FormField>
        )}

        {hasOptions && (
          <FormField label="Phương án trả lời" required>
            <div className="grid gap-2">
              <div className="hidden grid-cols-[minmax(0,1fr)_6rem_1.5rem] gap-2 px-0.5 text-[11px] font-medium text-muted sm:grid">
                <span>Nội dung phương án</span>
                <span>Điểm</span>
                <span />
              </div>
              {options.map((o, i) => (
                <div key={i} className="flex items-center gap-2">
                  <TextInput
                    value={o.option_text}
                    placeholder={`Phương án ${i + 1}`}
                    onChange={(e) =>
                      setOptions((arr) =>
                        arr.map((v, idx) =>
                          idx === i ? { ...v, option_text: e.target.value } : v
                        )
                      )
                    }
                  />
                  <TextInput
                    type="number"
                    step="any"
                    value={o.score}
                    aria-label={`Điểm phương án ${i + 1}`}
                    placeholder="Điểm"
                    className="w-24 shrink-0"
                    onChange={(e) =>
                      setOptions((arr) =>
                        arr.map((v, idx) => (idx === i ? { ...v, score: e.target.value } : v))
                      )
                    }
                  />
                  {options.length > 2 && (
                    <button
                      type="button"
                      className="p-1 text-muted hover:text-danger"
                      onClick={() => setOptions((arr) => arr.filter((_, idx) => idx !== i))}
                    >
                      <IconTrash size={15} />
                    </button>
                  )}
                </div>
              ))}
              <Button
                variant="secondary"
                className="w-fit px-3 py-1 text-xs"
                onClick={() => setOptions((arr) => [...arr, { option_text: "", score: "" }])}
              >
                + Thêm phương án
              </Button>
            </div>
          </FormField>
        )}
      </div>
    </Modal>
  );
}
