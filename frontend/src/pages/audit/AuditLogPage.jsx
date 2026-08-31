import { useState } from "react";
import { useAuditLogs } from "../../hooks/useAudit";
import { formatDateTime } from "../../lib/format";
import { PageHeader, Card, Badge, TextInput } from "../../components/ui/primitives";
import { Table, Pagination } from "../../components/ui/Table";
import { LoadingState, ErrorState, EmptyState } from "../../components/ui/DataStates";

export default function AuditLogPage() {
  const [filters, setFilters] = useState({ action: "", entity_type: "", page: 1, page_size: 20 });
  const params = { ...filters };
  Object.keys(params).forEach((k) => params[k] === "" && delete params[k]);
  const { data, isLoading, isError, error, refetch } = useAuditLogs(params);

  const columns = [
    { key: "created_at", header: "Thời gian", render: (r) => formatDateTime(r.created_at) },
    { key: "action", header: "Hành động", render: (r) => <Badge>{r.action}</Badge> },
    {
      key: "entity",
      header: "Đối tượng",
      render: (r) => `${r.entity_type}${r.entity_id ? ` #${r.entity_id}` : ""}`,
    },
    { key: "user_id", header: "Người thực hiện", render: (r) => (r.user_id ? `#${r.user_id}` : "hệ thống") },
    { key: "ip_address", header: "IP", render: (r) => r.ip_address || "—" },
    {
      key: "changes",
      header: "Thay đổi",
      render: (r) => (
        <details className="text-xs">
          <summary className="cursor-pointer text-brand-600">Xem</summary>
          <pre className="mt-1 max-w-md overflow-x-auto rounded bg-slate-50 p-2">
            {JSON.stringify({ old: r.old_values, new: r.new_values }, null, 2)}
          </pre>
        </details>
      ),
    },
  ];

  return (
    <div>
      <PageHeader title="Nhật ký hệ thống" subtitle="Toàn bộ thao tác quan trọng được ghi lại" />
      <div className="card mb-4 grid gap-3 p-4 md:grid-cols-3">
        <TextInput
          placeholder="Lọc theo action (vd: employee.transfer.after)"
          value={filters.action}
          onChange={(e) => setFilters((f) => ({ ...f, action: e.target.value, page: 1 }))}
        />
        <TextInput
          placeholder="Lọc theo entity_type (vd: employee)"
          value={filters.entity_type}
          onChange={(e) => setFilters((f) => ({ ...f, entity_type: e.target.value, page: 1 }))}
        />
      </div>
      <Card className="overflow-hidden p-0">
        {isLoading ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : data.items.length === 0 ? (
          <EmptyState title="Không có bản ghi nhật ký" />
        ) : (
          <>
            <Table columns={columns} rows={data.items} />
            <Pagination
              pagination={data.pagination}
              onChange={(page) => setFilters((f) => ({ ...f, page }))}
            />
          </>
        )}
      </Card>
    </div>
  );
}
