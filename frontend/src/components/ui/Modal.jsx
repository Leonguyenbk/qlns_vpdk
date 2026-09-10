import { useEffect, useRef } from "react";
import { Button } from "./primitives";
import { IconClose } from "./icons";

export function Modal({ open, onClose, title, children, footer, size = "md" }) {
  const panelRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    // First focus lands inside the panel, not on the page behind.
    panelRef.current?.querySelector(
      "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
    )?.focus();
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;
  const width = { sm: "max-w-sm", md: "max-w-lg", lg: "max-w-2xl" }[size];

  return (
    <div
      className="fixed inset-0 grid place-items-center p-4"
      style={{ zIndex: "var(--z-modal)" }}
    >
      <div
        className="absolute inset-0 bg-[color:var(--color-scrim)]"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === "string" ? title : undefined}
        className={`card relative w-full ${width} p-0 shadow-md`}
        style={{ maxHeight: "min(85vh, 44rem)" }}
      >
        <div className="flex items-center justify-between border-b border-rule px-5 py-3">
          <h3 className="font-display text-base font-semibold text-ink">{title}</h3>
          <button
            className="btn btn-ghost -mr-2 px-2 py-1"
            onClick={onClose}
            aria-label="Đóng"
          >
            <IconClose size={17} />
          </button>
        </div>
        <div className="overflow-y-auto px-5 py-4" style={{ maxHeight: "calc(85vh - 8rem)" }}>
          {children}
        </div>
        {footer && (
          <div className="flex justify-end gap-2 border-t border-rule px-5 py-3">{footer}</div>
        )}
      </div>
    </div>
  );
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = "Xác nhận",
  message,
  confirmText = "Xác nhận",
  variant = "danger",
  loading = false,
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            Hủy
          </Button>
          <Button variant={variant} onClick={onConfirm} disabled={loading}>
            {loading ? "Đang xử lý…" : confirmText}
          </Button>
        </>
      }
    >
      <p className="text-sm text-ink-2">{message}</p>
    </Modal>
  );
}
