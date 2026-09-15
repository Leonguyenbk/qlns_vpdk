import { useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { usePublicSurvey, useSubmitSurveyResponse } from "../../hooks/usePublicSurvey";
import { QuestionRenderer } from "../../components/surveys/QuestionRenderer";
import { Button, FormField, Select, TextInput } from "../../components/ui/primitives";
import { Spinner } from "../../components/ui/Spinner";
import { apiErrorMessage } from "../../lib/api";

function makeClientToken() {
  try {
    return crypto.randomUUID();
  } catch {
    return `t-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }
}

function isAnswered(qtype, value) {
  if (value === null || value === undefined) return false;
  if (qtype === "multiple_choice") return Array.isArray(value) && value.length > 0;
  if (qtype === "number" || qtype === "rating") return value !== null;
  return String(value).trim() !== "";
}

function buildAnswerItem(question, value) {
  const { id, question_type } = question;
  if (question_type === "single_choice") return { question_id: id, option_id: value };
  if (question_type === "multiple_choice") return { question_id: id, option_ids: value };
  if (question_type === "rating" || question_type === "number")
    return { question_id: id, answer_number: value };
  return { question_id: id, answer_text: value };
}

export default function PublicSurveyPage() {
  const { slug } = useParams();
  const [searchParams] = useSearchParams();
  const { data: survey, isLoading, isError, error } = usePublicSurvey(slug);
  const submit = useSubmitSurveyResponse(survey?.id);
  const [answers, setAnswers] = useState({});
  const [errors, setErrors] = useState({});
  const [respondentName, setRespondentName] = useState("");
  const [respondentPhone, setRespondentPhone] = useState("");
  const [respondentEmail, setRespondentEmail] = useState("");
  const [respondentAddress, setRespondentAddress] = useState("");
  const [done, setDone] = useState(false);
  const [clientToken] = useState(makeClientToken);

  const questions = survey?.questions || [];
  const branches = survey?.branches || [];

  // Mã QR dán tại chi nhánh mang theo ?branch=<mã hoặc id chi nhánh> — tự chọn
  // sẵn để người dân không phải chọn tay; nếu không khớp branch nào thì vẫn
  // để trống cho người dân tự chọn (link chung, không dán ở chi nhánh cụ thể).
  const branchParam = searchParams.get("branch");
  const presetBranch = useMemo(() => {
    if (!branchParam) return null;
    return branches.find((b) => String(b.id) === branchParam || b.code === branchParam) || null;
  }, [branches, branchParam]);
  const [branchId, setBranchId] = useState("");
  const effectiveBranchId = presetBranch ? presetBranch.id : branchId;

  const setAnswer = (qid, value) => {
    setAnswers((a) => ({ ...a, [qid]: value }));
    setErrors((e) => ({ ...e, [qid]: null }));
  };

  const onSubmit = async () => {
    const nextErrors = {};
    if (branches.length > 0 && !effectiveBranchId) {
      nextErrors._branch = "Vui lòng chọn chi nhánh được khảo sát.";
    }
    for (const q of questions) {
      if (q.is_required && !isAnswered(q.question_type, answers[q.id])) {
        nextErrors[q.id] = "Câu hỏi này là bắt buộc.";
      }
    }
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      const firstId = questions.find((q) => nextErrors[q.id])?.id;
      document.getElementById(nextErrors._branch ? "q-branch" : `q-${firstId}`)?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      return;
    }
    const items = questions
      .filter((q) => isAnswered(q.question_type, answers[q.id]))
      .map((q) => buildAnswerItem(q, answers[q.id]));
    try {
      await submit.mutateAsync({
        client_token: clientToken,
        branch_id: effectiveBranchId || undefined,
        respondent_name: respondentName || undefined,
        respondent_phone: respondentPhone || undefined,
        respondent_email: respondentEmail || undefined,
        respondent_address: respondentAddress || undefined,
        answers: items,
      });
      setDone(true);
    } catch (err) {
      const msg = apiErrorMessage(err, "Không thể gửi đánh giá, vui lòng thử lại.");
      // Lỗi tổng quát hiển thị ở đầu trang (backend luôn kiểm tra lại toàn bộ).
      setErrors((e) => ({ ...e, _global: msg }));
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas">
        <Spinner label="Đang tải khảo sát…" />
      </div>
    );
  }

  if (isError || !survey) {
    return (
      <PublicShell>
        <p className="text-center text-ink-2">
          {apiErrorMessage(error, "Không tìm thấy khảo sát.")}
        </p>
      </PublicShell>
    );
  }

  if (!survey.available) {
    return (
      <PublicShell title={survey.title}>
        <p className="text-center text-ink-2">
          {survey.unavailable_reason || "Khảo sát hiện không nhận phản hồi."}
        </p>
      </PublicShell>
    );
  }

  if (done) {
    return (
      <PublicShell title={survey.title}>
        <div className="flex flex-col items-center gap-3 py-8 text-center">
          <span
            className="grid h-14 w-14 place-items-center rounded-full text-2xl text-white"
            style={{ backgroundImage: "var(--gradient-brand)" }}
          >
            ✓
          </span>
          <p className="text-base font-medium text-ink">
            Cảm ơn Anh/Chị đã dành thời gian đánh giá chất lượng phục vụ.
          </p>
        </div>
      </PublicShell>
    );
  }

  return (
    <PublicShell title={survey.title} description={survey.description}>
      {errors._global && (
        <div className="mb-4 rounded-lg border border-[color:var(--color-danger-quiet)] bg-[color:var(--color-danger-quiet)] px-3 py-2 text-sm text-danger">
          {errors._global}
        </div>
      )}

      {branches.length > 0 && (
        <div className="mb-5" id="q-branch">
          <FormField label="Chi nhánh được khảo sát" required error={errors._branch}>
            {presetBranch ? (
              <div className="rounded-lg border border-rule bg-canvas px-3 py-2 text-sm text-ink">
                {presetBranch.name}
              </div>
            ) : (
              <Select value={branchId} onChange={(e) => { setBranchId(e.target.value); setErrors((er) => ({ ...er, _branch: null })); }}>
                <option value="">-- Chọn chi nhánh --</option>
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </Select>
            )}
          </FormField>
        </div>
      )}

      {survey.is_anonymous === false && (
        <div className="mb-5 grid gap-3">
          <FormField label="Họ và tên">
            <TextInput value={respondentName} onChange={(e) => setRespondentName(e.target.value)} />
          </FormField>
          <FormField label="Số điện thoại">
            <TextInput value={respondentPhone} onChange={(e) => setRespondentPhone(e.target.value)} />
          </FormField>
          <FormField label="Email">
            <TextInput value={respondentEmail} onChange={(e) => setRespondentEmail(e.target.value)} />
          </FormField>
          <FormField label="Địa chỉ" hint="Nếu có">
            <TextInput value={respondentAddress} onChange={(e) => setRespondentAddress(e.target.value)} />
          </FormField>
        </div>
      )}

      <div className="grid gap-6">
        {questions.map((q) => (
          <div key={q.id} id={`q-${q.id}`}>
            <QuestionRenderer
              question={q}
              value={answers[q.id] ?? (q.question_type === "multiple_choice" ? [] : null)}
              onChange={(v) => setAnswer(q.id, v)}
              error={errors[q.id]}
              disabled={submit.isPending}
            />
          </div>
        ))}
      </div>

      <Button
        className="mt-7 w-full justify-center py-3 text-base"
        onClick={onSubmit}
        disabled={submit.isPending || questions.length === 0}
      >
        {submit.isPending ? "Đang gửi…" : "GỬI ĐÁNH GIÁ"}
      </Button>
    </PublicShell>
  );
}

function PublicShell({ title, description, children }) {
  return (
    <div className="min-h-screen bg-canvas px-4 py-8">
      <div className="mx-auto w-full max-w-md">
        <div className="mb-6 text-center">
          <p className="eyebrow mb-1">Văn phòng Đăng ký Đất đai</p>
          {title && (
            <h1 className="font-display text-lg font-semibold tracking-tight text-ink">{title}</h1>
          )}
          {description && <p className="mt-1.5 text-sm text-muted">{description}</p>}
        </div>
        <div className="card p-5">{children}</div>
      </div>
    </div>
  );
}
