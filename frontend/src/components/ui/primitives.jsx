import clsx from "clsx";
import { forwardRef, useState } from "react";
import { initials } from "../../lib/format";
import { IconEye, IconEyeOff } from "./icons";

const BTN = {
  primary: "btn btn-primary",
  secondary: "btn btn-secondary",
  danger: "btn btn-danger",
  ghost: "btn btn-ghost",
};

export function Button({ variant = "primary", className, type = "button", ...props }) {
  return <button type={type} className={clsx(BTN[variant] || BTN.primary, className)} {...props} />;
}

export function Card({ className, children }) {
  return <div className={clsx("card p-5", className)}>{children}</div>;
}

export function PageHeader({ title, subtitle, eyebrow, actions }) {
  return (
    <div className="mb-6 flex flex-col gap-3 border-b border-rule pb-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {eyebrow && <p className="eyebrow mb-1.5">{eyebrow}</p>}
        <h1 className="font-display text-xl font-semibold tracking-tight text-ink">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function FormField({ label, error, required, children, hint, htmlFor }) {
  return (
    <div>
      {label && (
        <label className="label" htmlFor={htmlFor}>
          {label}
          {required && (
            <span className="text-danger" aria-hidden="true">
              {" "}
              *
            </span>
          )}
        </label>
      )}
      {children}
      {/* Reserve one line so validation doesn't push the layout down */}
      <p
        className={clsx(
          "mt-1 min-h-[1.25rem] text-xs",
          error ? "text-danger" : "text-muted"
        )}
      >
        {error || hint || ""}
      </p>
    </div>
  );
}

export function Badge({ children, className }) {
  return <span className={clsx("badge", className || "badge-info")}>{children}</span>;
}

export function Avatar({ name, url, size = 36 }) {
  const style = { width: size, height: size };
  if (url) {
    return (
      <img
        src={url}
        alt={name || ""}
        style={style}
        className="rounded-md border border-rule object-cover"
      />
    );
  }
  return (
    <div
      style={style}
      className="mono flex items-center justify-center rounded-md bg-[color:var(--color-accent-quiet)] text-xs font-semibold text-[color:var(--color-accent-text)]"
    >
      {initials(name)}
    </div>
  );
}

export const TextInput = forwardRef(function TextInput({ error, className, ...props }, ref) {
  return (
    <input
      ref={ref}
      aria-invalid={error ? "true" : undefined}
      className={clsx("input", className)}
      {...props}
    />
  );
});

export const PasswordInput = forwardRef(function PasswordInput(
  { error, className, ...props },
  ref
) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        ref={ref}
        type={show ? "text" : "password"}
        aria-invalid={error ? "true" : undefined}
        className={clsx("input pr-11", className)}
        {...props}
      />
      <button
        type="button"
        onClick={() => setShow((s) => !s)}
        aria-pressed={show}
        aria-label={show ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
        title={show ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
        className="absolute inset-y-px right-px flex w-10 items-center justify-center rounded-r-[5px] text-muted transition-colors hover:text-ink-2 focus-visible:text-ink"
      >
        {show ? <IconEyeOff size={17} /> : <IconEye size={17} />}
      </button>
    </div>
  );
});

export const Select = forwardRef(function Select({ error, className, children, ...props }, ref) {
  return (
    <select
      ref={ref}
      aria-invalid={error ? "true" : undefined}
      className={clsx("input", className)}
      {...props}
    >
      {children}
    </select>
  );
});

export const Textarea = forwardRef(function Textarea({ error, className, ...props }, ref) {
  return (
    <textarea
      ref={ref}
      rows={3}
      aria-invalid={error ? "true" : undefined}
      className={clsx("input", className)}
      {...props}
    />
  );
});
