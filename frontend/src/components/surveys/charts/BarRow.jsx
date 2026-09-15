/** Một dòng thanh ngang đơn giản (nhãn + giá trị + thanh tỉ lệ). Dùng cho phân bố
 * phương án, theo thời gian, theo chi nhánh — ưu tiên đơn giản, dễ đọc. */
export function BarRow({ label, percentage = 0, valueLabel, color = "var(--color-accent)" }) {
  return (
    <div className="grid gap-1">
      <div className="flex items-baseline justify-between gap-3 text-sm">
        <span className="min-w-0 truncate text-ink-2">{label}</span>
        <span className="mono shrink-0 text-xs text-muted">{valueLabel}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-[color:var(--color-rule-2)]">
        <div
          className="h-full rounded-full"
          style={{ width: `${Math.min(Math.max(percentage, 0), 100)}%`, background: color }}
        />
      </div>
    </div>
  );
}
