import { useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { usePeriods, useCriteriaSets, useKpiAdminMutations } from "../../../hooks/useKpi";
import { apiErrorMessage } from "../../../lib/api";
import { formatDate } from "../../../lib/format";
import { Button, FormField, TextInput, Select } from "../../../components/ui/primitives";
import { Table } from "../../../components/ui/Table";
import { LoadingState, ErrorState, EmptyState } from "../../../components/ui/DataStates";

const PERIOD_STATUS_LABELS = { OPEN: "Đang mở", LOCKED: "Đã khoá", REOPENED: "Đã mở lại (có ghi chú)" };
const PERIOD_STATUS_BADGE = { OPEN: "badge-ok", LOCKED: "badge-danger", REOPENED: "badge-warn" };

export default function PeriodsPage() {
  const { data: periods, isLoading, isError, error, refetch } = usePeriods();
  const { data: criteriaSets } = useCriteriaSets();
  const m = useKpiAdminMutations();
  const [form, setForm] = useState({ code: "", period_type: "QUARTER", start_date: "", end_date: "", criteria_set_id: "" });

  const wrap = (p, ok) => p.then(() => toast.success(ok)).catch((err) => toast.error(apiErrorMessage(err)));

  const onCreate = (e) => {
    e.preventDefault();
    if (!form.code || !form.start_date || !form.end_date) return toast.error("Nhập đủ mã kỳ, ngày bắt đầu/kết thúc.");
    wrap(
      m.createPeriod.mutateAsync({ ...form, criteria_set_id: form.criteria_set_id ? Number(form.criteria_set_id) : null }),
      "Tạo kỳ đánh giá thành công",
    ).then(() => setForm({ code: "", period_type: "QUARTER", start_date: "", end_date: "", criteria_set_id: "" }));
  };

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const columns = [
    { key: "code", header: "Mã kỳ", render: (p) => <span className="font-medium text-ink">{p.code}</span> },
    { key: "type", header: "Loại kỳ", render: (p) => ({ MONTH: "Tháng", QUARTER: "Quý", YEAR: "Năm" }[p.period_type] || p.period_type) },
    { key: "range", header: "Khoảng thời gian", render: (p) => `${formatDate(p.start_date)} — ${formatDate(p.end_date)}` },
    {
      key: "status", header: "Trạng thái",
      render: (p) => <span className={`badge ${PERIOD_STATUS_BADGE[p.status] || "badge-neutral"}`}>{PERIOD_STATUS_LABELS[p.status] || p.status}</span>,
    },
    { key: "criteria_set", header: "Bộ tiêu chí", render: (p) => p.criteria_set_id ? `#${p.criteria_set_id}` : "Chưa gắn" },
    {
      key: "actions", header: "", align: "right",
      render: (p) => (
        <div className="flex justify-end gap-1">
          <Link to={`/admin/kpi/ky-danh-gia/${p.id}`} className="btn btn-ghost px-2 py-1 text-xs">Xem điểm</Link>
          {p.status === "OPEN" && (
            <Button variant="ghost" className="px-2 py-1 text-xs text-danger"
                    onClick={() => wrap(m.lockPeriod.mutateAsync(p.id), "Đã khoá kỳ đánh giá")}>
              Khoá kỳ
            </Button>
          )}
          {p.status === "LOCKED" && (
            <Button variant="ghost" className="px-2 py-1 text-xs"
                    onClick={() => {
                      const reason = window.prompt("Lý do mở lại kỳ:");
                      if (reason) wrap(m.reopenPeriod.mutateAsync({ periodId: p.id, body: { reason } }), "Đã mở lại kỳ đánh giá");
                    }}>
              Mở lại
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-5">
      <form onSubmit={onCreate} className="card grid gap-3 p-4 sm:grid-cols-3 lg:grid-cols-6">
        <FormField label="Mã kỳ" required><TextInput placeholder="2026-Q1" value={form.code} onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))} /></FormField>
        <FormField label="Loại kỳ">
          <Select value={form.period_type} onChange={(e) => setForm((f) => ({ ...f, period_type: e.target.value }))}>
            <option value="MONTH">Tháng</option><option value="QUARTER">Quý</option><option value="YEAR">Năm</option>
          </Select>
        </FormField>
        <FormField label="Ngày bắt đầu" required><TextInput type="date" value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} /></FormField>
        <FormField label="Ngày kết thúc" required><TextInput type="date" value={form.end_date} onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))} /></FormField>
        <FormField label="Bộ tiêu chí áp dụng">
          <Select value={form.criteria_set_id} onChange={(e) => setForm((f) => ({ ...f, criteria_set_id: e.target.value }))}>
            <option value="">— Chưa chọn —</option>
            {criteriaSets?.map((c) => <option key={c.id} value={c.id}>#{c.id} {c.name} ({c.status})</option>)}
          </Select>
        </FormField>
        <div className="flex items-end"><Button type="submit" disabled={m.createPeriod.isPending}>+ Tạo kỳ</Button></div>
      </form>

      <div className="card overflow-hidden">
        {periods.length === 0 ? <EmptyState title="Chưa có kỳ đánh giá nào" /> : <Table columns={columns} rows={periods} rowKey="id" />}
      </div>
    </div>
  );
}
