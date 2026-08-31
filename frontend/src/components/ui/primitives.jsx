import clsx from "clsx";
import { forwardRef } from "react";
import { initials } from "../../lib/format";

export function Button({ variant = "primary", className, type = "button", ...props }) {
  const map = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    danger: "btn-danger",
    ghost: "btn text-slate-600 hover:bg-slate-100",
  };
  return <button type={type} className={clsx(map[variant], className)} {...props} />;
}

export function Card({ className, children }) {
  return <div className={clsx("card p-5", className)}>{children}</div>;
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-xl font-semibold text-slate-800">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
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
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}
      {children}
      {hint && !error && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}

export function Badge({ children, className }) {
  return <span className={clsx("badge", className || "bg-brand-100 text-brand-700")}>{children}</span>;
}

export function Avatar({ name, url, size = 40 }) {
  const style = { width: size, height: size };
  if (url) {
    return <img src={url} alt={name} style={style} className="rounded-full object-cover" />;
  }
  return (
    <div
      style={style}
      className="flex items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700"
    >
      {initials(name)}
    </div>
  );
}

export const TextInput = forwardRef(function TextInput(
  { error, className, ...props },
  ref
) {
  return (
    <input
      ref={ref}
      className={clsx("input", error && "border-red-400", className)}
      {...props}
    />
  );
});

export const Select = forwardRef(function Select(
  { error, className, children, ...props },
  ref
) {
  return (
    <select
      ref={ref}
      className={clsx("input", error && "border-red-400", className)}
      {...props}
    >
      {children}
    </select>
  );
});

export const Textarea = forwardRef(function Textarea(
  { error, className, ...props },
  ref
) {
  return (
    <textarea
      ref={ref}
      rows={3}
      className={clsx("input", error && "border-red-400", className)}
      {...props}
    />
  );
});
