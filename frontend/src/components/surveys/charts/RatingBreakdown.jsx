import { BarRow } from "./BarRow";

// Thang màu phân cực (diverging) cho mức độ hài lòng 1–5: xanh lá (tốt) -> xám
// (trung tính) -> đỏ (kém), tái dùng chung hệ màu trạng thái của design system.
const LEVEL_COLORS = {
  5: "var(--color-ok)",
  4: "oklch(72% 0.10 155)",
  3: "oklch(70% 0.015 95)",
  2: "var(--color-warn)",
  1: "var(--color-danger)",
};

export function RatingBreakdown({ breakdown }) {
  if (!breakdown?.length) return null;
  return (
    <div className="grid gap-2.5">
      {breakdown.map((b) => (
        <BarRow
          key={b.level}
          label={b.label}
          percentage={b.percentage}
          valueLabel={`${b.count} · ${b.percentage}%`}
          color={LEVEL_COLORS[b.level]}
        />
      ))}
    </div>
  );
}
