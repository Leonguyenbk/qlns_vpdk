import { useDashboard } from "../hooks/useEmployees";
import { PageHeader, Card, Badge } from "../components/ui/primitives";
import { LoadingState, ErrorState } from "../components/ui/DataStates";
import { EMPLOYEE_STATUS_LABELS } from "../lib/constants";
import { formatDate } from "../lib/format";

export default function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useDashboard();

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <div>
      <PageHeader title="Tổng quan" subtitle="Số liệu nhân sự theo phạm vi đơn vị của bạn" />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="text-sm text-slate-500">Nhân sự đang làm việc</p>
          <p className="mt-2 text-3xl font-semibold text-brand-700">{data.total_working}</p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Số đơn vị có nhân sự</p>
          <p className="mt-2 text-3xl font-semibold text-brand-700">{data.by_unit.length}</p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Chuyển đơn vị gần đây</p>
          <p className="mt-2 text-3xl font-semibold text-brand-700">
            {data.recent_transfers.length}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Nhóm trạng thái</p>
          <p className="mt-2 text-3xl font-semibold text-brand-700">
            {Object.keys(data.by_status).length}
          </p>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <h3 className="mb-3 font-semibold text-slate-800">Nhân sự theo đơn vị</h3>
          <ul className="divide-y divide-slate-100">
            {data.by_unit.length === 0 && <li className="py-2 text-sm text-slate-400">Chưa có dữ liệu</li>}
            {data.by_unit.map((u) => (
              <li key={u.unit_id} className="flex items-center justify-between py-2 text-sm">
                <span className="text-slate-700">{u.unit_name}</span>
                <Badge>{u.count}</Badge>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <h3 className="mb-3 font-semibold text-slate-800">Nhân sự theo trạng thái</h3>
          <ul className="divide-y divide-slate-100">
            {Object.entries(data.by_status).map(([k, v]) => (
              <li key={k} className="flex items-center justify-between py-2 text-sm">
                <span className="text-slate-700">{EMPLOYEE_STATUS_LABELS[k] || k}</span>
                <Badge>{v}</Badge>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card className="mt-6">
        <h3 className="mb-3 font-semibold text-slate-800">Chuyển đơn vị gần đây</h3>
        {data.recent_transfers.length === 0 ? (
          <p className="text-sm text-slate-400">Chưa có lượt chuyển đơn vị nào</p>
        ) : (
          <ul className="divide-y divide-slate-100 text-sm">
            {data.recent_transfers.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                <span className="text-slate-700">
                  → {a.unit?.name} · {a.position?.name}
                </span>
                <span className="text-slate-400">{formatDate(a.start_date)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
