import clsx from "clsx";
import { Textarea, TextInput } from "../ui/primitives";

const RATING_LEVELS = [1, 2, 3, 4, 5];

function ChoiceButton({ selected, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        "flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left text-[0.95rem] transition-colors",
        selected
          ? "border-[color:var(--color-accent)] bg-[color:var(--color-accent-quiet)] font-medium text-[color:var(--color-accent-text)]"
          : "border-rule bg-paper hover:bg-paper-2"
      )}
    >
      <span
        className={clsx(
          "grid h-5 w-5 shrink-0 place-items-center rounded-full border-2",
          selected ? "border-[color:var(--color-accent)]" : "border-[#cbd5e1]"
        )}
      >
        {selected && <span className="h-2.5 w-2.5 rounded-full bg-[color:var(--color-accent)]" />}
      </span>
      {children}
    </button>
  );
}

function CheckButton({ selected, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        "flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left text-[0.95rem] transition-colors",
        selected
          ? "border-[color:var(--color-accent)] bg-[color:var(--color-accent-quiet)] font-medium text-[color:var(--color-accent-text)]"
          : "border-rule bg-paper hover:bg-paper-2"
      )}
    >
      <span
        className={clsx(
          "grid h-5 w-5 shrink-0 place-items-center rounded-md border-2",
          selected ? "border-[color:var(--color-accent)] bg-[color:var(--color-accent)]" : "border-[#cbd5e1]"
        )}
      >
        {selected && (
          <svg viewBox="0 0 20 20" fill="white" className="h-3.5 w-3.5">
            <path d="M16.7 5.3a1 1 0 0 1 0 1.4l-8 8a1 1 0 0 1-1.4 0l-4-4a1 1 0 1 1 1.4-1.4L8 12.6l7.3-7.3a1 1 0 0 1 1.4 0Z" />
          </svg>
        )}
      </span>
      {children}
    </button>
  );
}

/** Render một câu hỏi khảo sát theo đúng loại (question_type) — dùng cho cả trang
 * công khai và xem trước. `value`/`onChange` theo dạng điều khiển (controlled). */
export function QuestionRenderer({ question, value, onChange, error, disabled }) {
  const { question_type: type, options = [] } = question;

  let control = null;
  if (type === "single_choice") {
    control = (
      <div className="grid gap-2">
        {options.map((o) => (
          <ChoiceButton key={o.id} selected={value === o.id} onClick={() => !disabled && onChange(o.id)}>
            {o.option_text}
          </ChoiceButton>
        ))}
      </div>
    );
  } else if (type === "multiple_choice") {
    const arr = Array.isArray(value) ? value : [];
    control = (
      <div className="grid gap-2">
        {options.map((o) => {
          const checked = arr.includes(o.id);
          return (
            <CheckButton
              key={o.id}
              selected={checked}
              onClick={() =>
                !disabled && onChange(checked ? arr.filter((x) => x !== o.id) : [...arr, o.id])
              }
            >
              {o.option_text}
            </CheckButton>
          );
        })}
      </div>
    );
  } else if (type === "yes_no") {
    control = (
      <div className="grid grid-cols-2 gap-3">
        <ChoiceButton selected={value === "yes"} onClick={() => !disabled && onChange("yes")}>
          <span className="mx-auto">Có</span>
        </ChoiceButton>
        <ChoiceButton selected={value === "no"} onClick={() => !disabled && onChange("no")}>
          <span className="mx-auto">Không</span>
        </ChoiceButton>
      </div>
    );
  } else if (type === "rating") {
    control = (
      <div className="flex justify-between gap-2">
        {RATING_LEVELS.map((lvl) => (
          <button
            key={lvl}
            type="button"
            disabled={disabled}
            onClick={() => onChange(lvl)}
            aria-label={`${lvl} sao`}
            className={clsx(
              "flex h-14 flex-1 items-center justify-center rounded-xl border text-lg font-semibold transition-colors",
              value === lvl
                ? "border-[color:var(--color-accent)] bg-[color:var(--color-accent-quiet)] text-[color:var(--color-accent-text)]"
                : "border-rule bg-paper text-muted hover:bg-paper-2"
            )}
          >
            {lvl}
          </button>
        ))}
      </div>
    );
  } else if (type === "number") {
    control = (
      <TextInput
        type="number"
        disabled={disabled}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
        className="text-base"
      />
    );
  } else if (type === "date") {
    control = (
      <TextInput
        type="date"
        disabled={disabled}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value || null)}
        className="text-base"
      />
    );
  } else if (type === "textarea") {
    control = (
      <Textarea
        disabled={disabled}
        rows={4}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        className="text-base"
      />
    );
  } else {
    control = (
      <TextInput
        disabled={disabled}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        className="text-base"
      />
    );
  }

  return (
    <div>
      <p className="mb-2.5 text-[0.95rem] font-medium text-ink">
        {question.question_text}
        {question.is_required && (
          <span className="text-danger" aria-hidden="true">
            {" "}
            *
          </span>
        )}
      </p>
      {control}
      {type === "multiple_choice" && question.scoring_mode === "deduction" && (
        <p className="mt-2 text-xs text-muted">Nếu không có nội dung nào phù hợp, có thể bỏ chọn tất cả.</p>
      )}
      {error && <p className="mt-1.5 text-xs text-danger">{error}</p>}
    </div>
  );
}
