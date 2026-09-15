export function KpiTile({ label, value, hint }) {
  return (
    <div className="card p-4">
      <p className="eyebrow mb-1.5">{label}</p>
      <p className="font-display text-2xl font-semibold tracking-tight text-ink">{value}</p>
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
    </div>
  );
}
