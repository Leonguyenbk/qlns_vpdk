export function Spinner({ label, className = "" }) {
  return (
    <div className={`flex items-center gap-3 text-muted ${className}`}>
      <span
        className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-rule-2 border-t-accent"
        aria-hidden="true"
      />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}
