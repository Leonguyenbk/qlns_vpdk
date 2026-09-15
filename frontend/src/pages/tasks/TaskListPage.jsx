import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { useCan } from "../../components/Can";
import { useTasks } from "../../hooks/useTasks";
import { useUnits } from "../../hooks/useUnits";
import { useCatalogGroups } from "../../hooks/useKpi";
import { PageHeader, Button, Select, TextInput } from "../../components/ui/primitives";
import { Table, Pagination } from "../../components/ui/Table";
import { LoadingState, ErrorState, EmptyState } from "../../components/ui/DataStates";
import { formatDate } from "../../lib/format";
import {
  PERMISSIONS,
  TASK_STATUS_LABELS,
  TASK_STATUS_BADGE,
  TASK_PRIORITY_LABELS,
} from "../../lib/constants";

const STATUS_ORDER = [
  "DRAFT", "ASSIGNED", "IN_PROGRESS", "PENDING_COLLAB", "PAUSED",
  "NEEDS_REVISION", "PENDING_ACCEPTANCE", "COMPLETED", "CANCELLED",
];

const MODE_CONFIG = {
  all: { title: "Danh sách nhiệm vụ", subtitle: "Toàn bộ nhiệm vụ trong phạm vi đơn vị được phân quyền." },
  mine: { title: "Công việc của tôi", subtitle: "Nhiệm vụ bạn chủ trì hoặc phối hợp thực hiện." },
  assigned: { title: "Việc tôi đã giao", subtitle: "Nhiệm vụ do bạn giao hoặc phê duyệt giao." },
};

const TASK_COLUMNS = [
  {
    key: "task", header: "Nhiệm vụ",
    render: (t) => (
      <>
        <Link to={`/cong-viec/danh-sach/${t.id}`} className="link font-medium">{t.code}</Link>
        <div className="max-w-xs truncate text-xs text-muted">{t.name}</div>
      </>
    ),
  },
  { key: "priority", header: "Ưu tiên", render: (t) => TASK_PRIORITY_LABELS[t.priority] || t.priority },
  {
    key: "status", header: "Trạng thái",
    render: (t) => (
      <>
        <span className={`badge ${TASK_STATUS_BADGE[t.status] || "badge-neutral"}`}>
          {TASK_STATUS_LABELS[t.status] || t.status}
        </span>
        {t.is_overdue && <span className="badge badge-danger ml-1">Quá hạn</span>}
      </>
    ),
  },
  { key: "progress", header: "Tiến độ", render: (t) => `${t.progress_percent}%` },
  { key: "assigned_date", header: "Ngày giao", render: (t) => formatDate(t.assigned_date) },
  { key: "deadline", header: "Hạn hoàn thành", render: (t) => formatDate(t.effective_deadline) },
  {
    key: "blocked", header: "Vướng mắc",
    render: (t) => (t.is_blocked ? <span className="badge badge-danger">Vướng mắc</span> : <span className="text-muted">—</span>),
  },
];

export default function TaskListPage({ mode = "all" }) {
  const { user } = useAuth();
  const { canAny } = useCan();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [view, setView] = useState("table");
  const [filters, setFilters] = useState({
    status: "", priority: "", business_group_code: "",
    unit_id: "", overdue: "", due_soon: "", search: "",
    person_id: searchParams.get("person_id") || "",
    page: 1, page_size: 20,
  });

  useEffect(() => {
    const pid = searchParams.get("person_id");
    if (pid) setFilters((f) => ({ ...f, person_id: pid, page: 1 }));
  }, [searchParams]);

  const canViewAll = canAny([PERMISSIONS.TASK_VIEW_ALL]);
  const { data: units } = useUnits({ only_active: true });
  const { data: groups } = useCatalogGroups();

  const params = useMemo(() => {
    const p = { ...filters, page_size: view === "board" ? 200 : filters.page_size };
    if (mode === "mine") p.person_id = user?.id;
    if (mode === "assigned") p.assigner_id = user?.id;
    Object.keys(p).forEach((k) => (p[k] === "" || p[k] === undefined) && delete p[k]);
    return p;
  }, [filters, view, mode, user]);

  const { data, isLoading, isError, error, refetch, isFetching } = useTasks(params);
  const setFilter = (patch) => setFilters((f) => ({ ...f, ...patch, page: 1 }));
  const cfg = MODE_CONFIG[mode];

  const boardColumns = useMemo(() => {
    if (!data) return [];
    const byStatus = {};
    for (const t of data.items) {
      (byStatus[t.status] ||= []).push(t);
    }
    return STATUS_ORDER.filter((s) => byStatus[s]?.length).map((s) => ({ status: s, items: byStatus[s] }));
  }, [data]);

  return (
    <div>
      <PageHeader
        title={cfg.title}
        subtitle={cfg.subtitle}
        actions={
          <>
            <div className="flex overflow-hidden rounded-lg border border-rule">
              <button
                className={`px-3 py-1.5 text-sm ${view === "table" ? "bg-[color:var(--color-accent-quiet)] text-accent-text" : "text-muted"}`}
                onClick={() => setView("table")}
              >
                Bảng
              </button>
              <button
                className={`px-3 py-1.5 text-sm ${view === "board" ? "bg-[color:var(--color-accent-quiet)] text-accent-text" : "text-muted"}`}
                onClick={() => setView("board")}
              >
                Theo trạng thái
              </button>
            </div>
            {canAny([PERMISSIONS.TASK_CREATE]) && (
              <Button onClick={() => navigate("/cong-viec/danh-sach/moi")}>+ Giao việc</Button>
            )}
          </>
        }
      />

      <div className="card mb-4 grid gap-3 p-4 md:grid-cols-3 xl:grid-cols-6">
        <TextInput placeholder="Tìm theo mã, tên nhiệm vụ…" value={filters.search}
                   onChange={(e) => setFilter({ search: e.target.value })} />
        {mode === "all" && canViewAll && (
          <Select value={filters.unit_id} onChange={(e) => setFilter({ unit_id: e.target.value })}>
            <option value="">Tất cả đơn vị</option>
            {units?.map((u) => <option key={u.id} value={u.id}>{u.path || u.name}</option>)}
          </Select>
        )}
        <Select value={filters.status} onChange={(e) => setFilter({ status: e.target.value })}>
          <option value="">Tất cả trạng thái</option>
          {Object.entries(TASK_STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </Select>
        <Select value={filters.priority} onChange={(e) => setFilter({ priority: e.target.value })}>
          <option value="">Mọi mức ưu tiên</option>
          {Object.entries(TASK_PRIORITY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </Select>
        <Select value={filters.business_group_code} onChange={(e) => setFilter({ business_group_code: e.target.value })}>
          <option value="">Mọi nhóm nghiệp vụ</option>
          {groups?.map((g) => <option key={g.code} value={g.code}>{g.code} — {g.name}</option>)}
        </Select>
        <Select
          value={filters.overdue ? "overdue" : filters.due_soon ? "due_soon" : ""}
          onChange={(e) => setFilter({
            overdue: e.target.value === "overdue" ? "1" : "",
            due_soon: e.target.value === "due_soon" ? "1" : "",
          })}
        >
          <option value="">Mọi hạn hoàn thành</option>
          <option value="overdue">Chỉ quá hạn</option>
          <option value="due_soon">Sắp đến hạn (≤3 ngày)</option>
        </Select>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : data.items.length === 0 ? (
          <EmptyState title="Không có nhiệm vụ nào phù hợp bộ lọc" />
        ) : view === "table" ? (
          <>
            {isFetching && <div className="px-4 py-1 text-xs text-muted">Đang cập nhật...</div>}
            <Table columns={TASK_COLUMNS} rows={data.items} rowKey="id" />
          </>
        ) : (
          <div className="grid gap-3 overflow-x-auto p-4" style={{ gridTemplateColumns: `repeat(${boardColumns.length}, minmax(240px, 1fr))` }}>
            {boardColumns.map((col) => (
              <div key={col.status} className="min-w-[240px] rounded-lg bg-[color:var(--color-paper-2)] p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className={`badge ${TASK_STATUS_BADGE[col.status] || "badge-neutral"}`}>
                    {TASK_STATUS_LABELS[col.status]}
                  </span>
                  <span className="text-xs text-muted">{col.items.length}</span>
                </div>
                <div className="space-y-2">
                  {col.items.map((t) => (
                    <Link
                      key={t.id}
                      to={`/cong-viec/danh-sach/${t.id}`}
                      className="card block p-3 text-sm hover:border-accent"
                    >
                      <div className="font-medium text-ink">{t.code}</div>
                      <div className="truncate text-xs text-muted">{t.name}</div>
                      <div className="mt-1 flex items-center justify-between text-xs">
                        <span>{t.progress_percent}%</span>
                        {t.is_overdue && <span className="badge badge-danger">Quá hạn</span>}
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
        {view === "table" && data?.pagination && (
          <Pagination pagination={data.pagination} onChange={(page) => setFilters((f) => ({ ...f, page }))} />
        )}
      </div>
    </div>
  );
}
