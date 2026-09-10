import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { IconSearch, IconArrowRight } from "./ui/icons";

/**
 * ⌘K palette — the Cobalt signature interaction. Opens on ⌘K / Ctrl+K anywhere,
 * filters the sections the account can reach, Arrow↑/↓ to move, Enter to go,
 * Esc or backdrop to close. Focus-managed, reduced-motion safe (no transition).
 */
export function CommandPalette({ open, setOpen, items }) {
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const [q, setQ] = useState("");
  const [active, setActive] = useState(0);

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [setOpen]);

  useEffect(() => {
    if (open) {
      setQ("");
      setActive(0);
      const t = setTimeout(() => inputRef.current?.focus(), 0);
      return () => clearTimeout(t);
    }
  }, [open]);

  const results = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return items;
    return items.filter(
      (it) =>
        it.label.toLowerCase().includes(needle) ||
        it.to.toLowerCase().includes(needle)
    );
  }, [q, items]);

  if (!open) return null;

  const go = (item) => {
    if (!item) return;
    setOpen(false);
    navigate(item.to);
  };

  const onKeyDown = (e) => {
    if (e.key === "Escape") return setOpen(false);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      go(results[active]);
    }
  };

  return (
    <div
      className="fixed inset-0 flex items-start justify-center px-4 pt-[12vh]"
      style={{ zIndex: "var(--z-modal)" }}
    >
      <div
        className="absolute inset-0 bg-[color:var(--color-scrim)]"
        onClick={() => setOpen(false)}
        aria-hidden="true"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Tìm kiếm điều hướng"
        className="card relative w-full max-w-lg overflow-hidden p-0 shadow-md"
        onKeyDown={onKeyDown}
      >
        <div className="flex items-center gap-2.5 border-b border-rule px-4 py-3">
          <IconSearch size={17} className="text-muted" />
          <input
            ref={inputRef}
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setActive(0);
            }}
            placeholder="Đi tới trang…"
            className="mono w-full bg-transparent text-sm text-ink outline-none placeholder:text-muted"
          />
          <kbd className="eyebrow rounded border border-rule-2 px-1.5 py-0.5">ESC</kbd>
        </div>
        <ul className="max-h-72 overflow-y-auto py-1.5">
          {results.length === 0 && (
            <li className="px-4 py-6 text-center text-sm text-muted">Không có kết quả</li>
          )}
          {results.map((item, i) => (
            <li key={item.to}>
              <button
                type="button"
                onMouseEnter={() => setActive(i)}
                onClick={() => go(item)}
                className={`flex w-full items-center justify-between gap-3 px-4 py-2 text-left text-sm ${
                  i === active ? "bg-[color:var(--color-accent-quiet)] text-accent-text" : "text-ink-2"
                }`}
              >
                <span className="flex items-center gap-2.5">
                  {item.icon}
                  {item.label}
                </span>
                {i === active && <IconArrowRight size={15} />}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
