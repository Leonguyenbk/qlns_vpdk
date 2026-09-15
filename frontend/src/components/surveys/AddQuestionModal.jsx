import { useState } from "react";
import toast from "react-hot-toast";
import { Modal } from "../ui/Modal";
import { Button, FormField, Select, Textarea, TextInput } from "../ui/primitives";
import { QUESTION_TYPE_LABELS, QUESTION_TYPES_WITH_OPTIONS } from "../../lib/constants";
import { apiErrorMessage } from "../../lib/api";
import { IconTrash } from "../ui/icons";

const EMPTY = { question_text: "", question_type: "single_choice", is_required: false };

export function AddQuestionModal({ open, onClose, onCreate, existingQuestions = [] }) {
  const [form, setForm] = useState(EMPTY);
  const [options, setOptions] = useState(["", ""]);
  const [copyFromId, setCopyFromId] = useState("");
  const [saving, setSaving] = useState(false);
  const hasOptions = QUESTION_TYPES_WITH_OPTIONS.has(form.question_type);

  // Câu hỏi khác trong khảo sát đã có sẵn phương án trả lời — dùng để sao chép,
  // tránh gõ lại cùng 1 thang đo (vd. "Rất hài lòng".."Rất không hài lòng") nhiều lần.
  const sourceQuestions = existingQuestions.filter(
    (q) => QUESTION_TYPES_WITH_OPTIONS.has(q.question_type) && (q.options || []).some((o) => o.is_active)
  );

  const reset = () => {
    setForm(EMPTY);
    setOptions(["", ""]);
    setCopyFromId("");
  };

  const copyOptionsFrom = (questionId) => {
    setCopyFromId(questionId);
    const source = sourceQuestions.find((q) => String(q.id) === String(questionId));
    if (!source) return;
    const texts = source.options.filter((o) => o.is_active).map((o) => o.option_text);
    if (texts.length) setOptions(texts);
  };

  const submit = async () => {
    if (!form.question_text.trim()) {
      toast.error("Nhập nội dung câu hỏi");
      return;
    }
    const opts = options.map((o) => o.trim()).filter(Boolean);
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
        options: hasOptions ? opts.map((option_text) => ({ option_text })) : [],
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
              {options.map((o, i) => (
                <div key={i} className="flex items-center gap-2">
                  <TextInput
                    value={o}
                    placeholder={`Phương án ${i + 1}`}
                    onChange={(e) =>
                      setOptions((arr) => arr.map((v, idx) => (idx === i ? e.target.value : v)))
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
                onClick={() => setOptions((arr) => [...arr, ""])}
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
