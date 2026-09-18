import { useState } from "react";
import toast from "react-hot-toast";
import { Modal } from "../ui/Modal";
import { Button, FormField, Select, Textarea, TextInput } from "../ui/primitives";
import { QUESTION_TYPE_LABELS, QUESTION_TYPES_WITH_OPTIONS } from "../../lib/constants";
import { apiErrorMessage } from "../../lib/api";
import { IconTrash } from "../ui/icons";

const EMPTY = { question_text: "", question_type: "single_choice", is_required: false, section: "" };

export function AddQuestionModal({ open, onClose, onCreate, existingQuestions = [] }) {
  const lastSection = existingQuestions[existingQuestions.length - 1]?.section || "";
  const [form, setForm] = useState({ ...EMPTY, section: lastSection });
  const [options, setOptions] = useState([
    { option_text: "", score: "" },
    { option_text: "", score: "" },
  ]);
  const [copyFromId, setCopyFromId] = useState("");
  const [saving, setSaving] = useState(false);
  const hasOptions = QUESTION_TYPES_WITH_OPTIONS.has(form.question_type);

  // Câu hỏi khác trong khảo sát đã có sẵn phương án trả lời — dùng để sao chép,
  // tránh gõ lại cùng 1 thang đo (vd. "Rất hài lòng".."Rất không hài lòng") nhiều lần.
  const sourceQuestions = existingQuestions.filter(
    (q) => QUESTION_TYPES_WITH_OPTIONS.has(q.question_type) && (q.options || []).some((o) => o.is_active)
  );
  // Danh sách "Phần" đã dùng trong khảo sát, gợi ý để không gõ lại/gõ sai tên phần.
  const sectionOptions = [...new Set(existingQuestions.map((q) => q.section).filter(Boolean))];

  const reset = () => {
    setForm({ ...EMPTY, section: lastSection });
    setOptions([
      { option_text: "", score: "" },
      { option_text: "", score: "" },
    ]);
    setCopyFromId("");
  };

  const copyOptionsFrom = (questionId) => {
    setCopyFromId(questionId);
    const source = sourceQuestions.find((q) => String(q.id) === String(questionId));
    if (!source) return;
    const copied = source.options
      .filter((o) => o.is_active)
      .map((o) => ({ option_text: o.option_text, score: o.score ?? "" }));
    if (copied.length) setOptions(copied);
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
    if (opts.some((o) => o.score != null && (o.score < 0 || o.score > 5))) {
      toast.error("Điểm phương án phải nằm trong khoảng 0–5");
      return;
    }
    setSaving(true);
    try {
      await onCreate({
        question_text: form.question_text.trim(),
        question_type: form.question_type,
        is_required: form.is_required,
        section: form.section.trim() || null,
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
        <FormField label="Phần" hint="Để nhóm nhiều câu hỏi lại, vd. &quot;Phần 1. Tiếp cận dịch vụ&quot; — bỏ trống nếu không cần chia phần">
          <TextInput
            list="survey-section-options"
            value={form.section}
            onChange={(e) => setForm((f) => ({ ...f, section: e.target.value }))}
            placeholder="Vd: Phần 1. Tiếp cận dịch vụ"
          />
          {sectionOptions.length > 0 && (
            <datalist id="survey-section-options">
              {sectionOptions.map((s) => (
                <option key={s} value={s} />
              ))}
            </datalist>
          )}
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

        {hasOptions && (
          <FormField label="Phương án trả lời" required>
            <div className="grid gap-2">
              {sourceQuestions.length > 0 && (
                <Select
                  value={copyFromId}
                  onChange={(e) => copyOptionsFrom(e.target.value)}
                  className="mb-1 text-xs"
                >
                  <option value="">-- Sao chép phương án từ câu hỏi khác (tuỳ chọn) --</option>
                  {sourceQuestions.map((q) => (
                    <option key={q.id} value={q.id}>
                      {q.question_text.length > 60 ? `${q.question_text.slice(0, 60)}…` : q.question_text}
                    </option>
                  ))}
                </Select>
              )}
              <div className="hidden grid-cols-[minmax(0,1fr)_6rem_1.5rem] gap-2 px-0.5 text-[11px] font-medium text-muted sm:grid">
                <span>Nội dung phương án</span>
                <span>Điểm (0–5)</span>
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
                    min="0"
                    max="5"
                    step="0.01"
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
