import { useState } from "react";
import { useGoisoBranches, useGoisoStats } from "../../../hooks/useGoiso";
import { LoadingState, ErrorState } from "../../../components/ui/DataStates";
import { Select } from "../../../components/ui/primitives";
import { Table } from "../../../components/ui/Table";

function fmtWait(sec) {
  if (!sec) return "—";
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}p${s ? ` ${s}s` : ""}`;
}

export default function StatsPage() {
  const [branch, setBranch] = useState("all");
  const { data: branches } = useGoisoBranches();
  const { data, isLoading, isError, error, refetch } = useGoisoStats(branch);

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const columns = [
    { key: "name", header: "Chi nhánh" },
    { key: "today_total", header: "Lượt hôm nay", align: "right" },
    { key: "avg_wait_seconds", header: "TB thời gian chờ", align: "right", render: (r) => fmtWait(r.avg_wait_seconds) },
    {
      key: "by_service",
      header: "Theo dịch vụ",
      render: (r) =>
        r.by_service?.length ? (
          <div className="flex flex-wrap gap-1.5">
            {r.by_service.map((s) => (
              <span key={s.prefix} className="badge badge-neutral">
                {s.prefix}: {s.issued} cấp · {s.done} xong · {s.waiting} chờ
              </span>
            ))}
          </div>
        ) : (
          <span className="text-muted">—</span>
        ),
    },
  ];

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <label className="text-sm font-medium text-ink-2">Chi nhánh:</label>
        <Select value={branch} onChange={(e) => setBranch(e.target.value)} className="max-w-xs">
          <option value="all">Tất cả chi nhánh</option>
          {branches?.map((b) => (
            <option key={b.code} value={b.code}>{b.name}</option>
          ))}
        </Select>
        <span className="ml-auto text-sm text-muted">Ngày {data.today}</span>
      </div>

      <div className="card p-0">
        <Table columns={columns} rows={data.branches} rowKey="code" />
      </div>

      {branch !== "all" && data.visitors?.length > 0 && (
        <div className="card mt-5 p-5">
          <h3 className="mb-3 text-sm font-semibold text-ink">Lượt khách 30 ngày gần nhất</h3>
          <div className="flex flex-wrap gap-2 text-xs">
            {data.visitors.map((v) => (
              <span key={v.date} className="badge badge-info">{v.date}: {v.count}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
