import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTaskDashboard } from "../../hooks/useTasks";
import { useUnits } from "../../hooks/useUnits";
import { PageHeader, Select } from "../../components/ui/primitives";
import { LoadingState, ErrorState, EmptyState } from "../../components/ui/DataStates";
import { formatDate } from "../../lib/format";
import { TASK_STATUS_LABELS, TASK_STATUS_BADGE } from "../../lib/constants";
import {
  IconOverview,
  IconInbox,
  IconAlert,
  IconClock,
  IconTask,
  IconGauge,
  IconArrowRight,
} from "../../components/ui/icons";

function StatCard({ Icon, value, label, tone }) {
  return (
    <div className="card flex items-center gap-3 p-4">
      <span
        className="grid h-11 w-11 shrink-0 place-items-center rounded-[10px]"
        style={{
          background: tone === "danger" ? "var(--color-danger-quiet)" : "var(--color-accent-quiet)",
          color: tone === "danger" ? "var(--color-danger-text)" : "var(--color-accent-text)",
        }}
      >
        <Icon size={19} />
      </span>
      <span className="min-w-0">
        <span className="tabular block text-xl font-bold leading-none tracking-tight text-ink">
          {value ?? "—"}
        </span>
        <span className="mt-1 block truncate text-xs text-muted">{label}</span>
      </span>
    </div>
  );
}

function DaysLeftBadge({ days }) {
  if (days === null || days === undefined) return <span className="text-muted">—</span>;
  if (days < 0) return <span className="badge badge-danger">Quá hạn {Math.abs(days)} ngày</span>;
  if (days <= 3) return <span className="badge badge-warn">Còn {days} ngày</span>;
  return <span className="badge badge-neutral">Còn {days} ngày</span>;
}

export default function ExecutiveDashboardPage() {
  const [unitId, setUnitId] = useState("");
  const params = useMemo(() => (unitId ? { unit_id: unitId } : {}), [unitId]);
  const { data, isLoading, isError, error, refetch } = useTaskDashboard(params);
  const { data: units } = useUnits({ only_active: true });

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const s = data.stats;

  return (
    <div className="space-y-5">
      <PageHeader
        title="Tổng quan điều hành"
        subtitle="Ai đang làm việc gì, ai giao, hạn khi nào, đang vướng ở đâu — theo phạm vi đơn vị được phân quyền."
        actions={
          <Select value={unitId} onChange={(e) => setUnitId(e.target.value)} className="w-56">
            <option value="">Tất cả đơn vị</option>
            {units?.map((u) => (
              <option key={u.id} value={u.id}>
                {u.path || u.name}
              </option>
            ))}
          </Select>
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5">
        <StatCard Icon={IconTask} value={s.total} label="Tổng số nhiệm vụ" />
        <StatCard Icon={IconInbox} value={s.not_started} label="Chưa bắt đầu" />
        <StatCard Icon={IconOverview} value={s.in_progress} label="Đang thực hiện" />
        <StatCard Icon={IconClock} value={s.due_soon} label="Sắp đến hạn (≤3 ngày)" tone="danger" />
        <StatCard Icon={IconAlert} value={s.overdue} label="Quá hạn" tone="danger" />
        <StatCard Icon={IconInbox} value={s.pending_collab} label="Chờ phối hợp" />
        <StatCard Icon={IconInbox} value={s.pending_acceptance} label="Chờ nghiệm thu" />
        <StatCard Icon={IconGauge} value={s.completed} label="Hoàn thành" />
        <StatCard
          Icon={IconGauge}
          value={s.on_time_rate !== null ? `${s.on_time_rate}%` : "Chưa đủ dữ liệu"}
          label="Tỷ lệ hoàn thành đúng hạn"
        />
        <StatCard
          Icon={IconTask}
          value={`${s.accepted_workload_total}/${s.assigned_workload_total}`}
          label="Khối lượng nghiệm thu/giao"
        />
      </div>

      <section className="card overflow-hidden">
        <div className="flex items-center justify-between border-b border-rule px-5 py-3">
          <h3 className="text-sm font-semibold text-ink">Theo dõi theo người</h3>
          <span className="text-xs text-muted">Chỉ tính nhiệm vụ đang hoạt động (chưa hoàn thành/hủy)</span>
        </div>
        {data.people.length === 0 ? (
          <EmptyState title="Chưa có nhiệm vụ nào đang hoạt động trong phạm vi này" />
        ) : (
          <div className="overflow-x-auto">
            <table className="tabular min-w-full text-sm">
              <thead>
                <tr className="border-b border-rule-2">
                  {[
                    "Họ tên", "Đơn vị / Chức vụ", "Nhiệm vụ gần đến hạn nhất", "Người giao", "Ngày giao",
                    "Hạn hoàn thành", "Tiến độ", "Trạng thái", "Còn lại/Quá hạn", "Vướng mắc", "",
                  ].map((h) => (
                    <th key={h} className="eyebrow px-4 py-2.5 text-left align-bottom">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.people.map((p) => {
                  const t = p.nearest_task;
                  return (
                    <tr key={p.user_id} className="border-b border-rule transition-colors last:border-0 hover:bg-paper-2">
                      <td className="px-4 py-3">
                        <div className="font-medium text-ink">{p.full_name || `#${p.user_id}`}</div>
                        <div className="text-xs text-muted">{p.active_task_count} nhiệm vụ đang phụ trách</div>
                      </td>
                      <td className="px-4 py-3 text-ink-2">
                        {p.unit_name || "—"}
                        {p.position_name && <div className="text-xs text-muted">{p.position_name}</div>}
                      </td>
                      <td className="px-4 py-3">
                        {t ? (
                          <Link to={`/cong-viec/danh-sach/${t.id}`} className="link font-medium">
                            {t.code} — {t.name}
                          </Link>
                        ) : "—"}
                      </td>
                      <td className="px-4 py-3 text-ink-2">{t?.assigner_id ? `#${t.assigner_id}` : "—"}</td>
                      <td className="px-4 py-3 text-ink-2">{t ? formatDate(t.assigned_date) : "—"}</td>
                      <td className="px-4 py-3 text-ink-2">{t ? formatDate(t.deadline) : "—"}</td>
                      <td className="px-4 py-3">
                        {t ? (
                          <div className="flex items-center gap-2">
                            <div className="h-1.5 w-16 overflow-hidden rounded-full bg-[color:var(--color-paper-3)]">
                              <div
                                className="h-full rounded-full"
                                style={{ width: `${t.progress_percent}%`, backgroundImage: "var(--gradient-brand-h)" }}
                              />
                            </div>
                            <span className="text-xs text-muted">{t.progress_percent}%</span>
                          </div>
                        ) : "—"}
                      </td>
                      <td className="px-4 py-3">
                        {t ? (
                          <span className={`badge ${TASK_STATUS_BADGE[t.status] || "badge-neutral"}`}>
                            {TASK_STATUS_LABELS[t.status] || t.status}
                          </span>
                        ) : "—"}
                      </td>
                      <td className="px-4 py-3">{t ? <DaysLeftBadge days={t.days_left} /> : "—"}</td>
                      <td className="px-4 py-3">
                        {t?.is_blocked ? (
                          <span className="badge badge-danger" title={t.blocker_reason || ""}>Có vướng mắc</span>
                        ) : (
                          <span className="text-muted">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          to={`/cong-viec/danh-sach?person_id=${p.user_id}`}
                          className="inline-flex items-center gap-1 text-xs font-medium text-accent-text hover:underline"
                        >
                          Xem tất cả <IconArrowRight size={12} />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
