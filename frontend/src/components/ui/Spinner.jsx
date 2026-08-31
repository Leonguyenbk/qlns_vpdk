export function Spinner({ label, className = "" }) {
  return (
    <div className={`flex items-center gap-3 text-slate-500 ${className}`}>
      <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}
