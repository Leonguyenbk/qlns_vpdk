import { useEffect, useRef, useState } from "react";
import { useDashboard } from "../hooks/useEmployees";
import { useAuth } from "../auth/AuthContext";
import { LoadingState, ErrorState } from "../components/ui/DataStates";
import { EMPLOYEE_STATUS_LABELS } from "../lib/constants";
import { formatDate } from "../lib/format";
import {
  IconArrowRight,
  IconChevronDown,
  IconPeople,
  IconOrg,
  IconPosition,
  IconRefresh,
} from "../components/ui/icons";

function greeting() {
  const h = new Date().getHours();
  if (h < 11) return "Chào buổi sáng";
  if (h < 14) return "Chào buổi trưa";
  if (h < 18) return "Chào buổi chiều";
  return "Chào buổi tối";
}

function StatCard({ Icon, value, label }) {
  return (
    <div className="card flex items-center gap-4 p-4">
      <span className="grid h-11 w-11 shrink-0 place-items-center rounded-[10px] bg-[color:var(--color-accent-quiet)] text-accent">
        <Icon size={20} />
      </span>
      <span className="min-w-0">
        <span className="tabular block text-2xl font-bold leading-none tracking-tight text-ink">
          {value}
        </span>
        <span className="mt-1 block truncate text-sm text-[#64748b]">{label}</span>
      </span>
    </div>
  );
}

function UnitNode({ node, depth, max, expanded, toggle }) {
  const hasKids = node.children && node.children.length > 0;
  const isOpen = expanded.has(node.id);
  return (
    <li>
      <div
        className="flex items-center gap-2 py-2 text-sm"
        style={{ paddingLeft: depth * 18 }}
      >
        {hasKids ? (
          <button
            type="button"
            onClick={() => toggle(node.id)}
            aria-expanded={isOpen}
            aria-label={isOpen ? "Thu gọn" : "Xem chi tiết"}
            className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-muted transition-colors hover:bg-paper-3 hover:text-ink"
          >
            <IconChevronDown size={15} className={isOpen ? "" : "-rotate-90"} />
          </button>
        ) : (
          <span className="h-5 w-5 shrink-0" />
        )}
        <span
          className={`min-w-0 flex-1 truncate ${
            depth === 0 ? "font-medium text-ink" : "text-ink-2"
          }`}
        >
          {node.name}
        </span>
        <span className="tabular shrink-0 font-semibold text-ink">{node.count}</span>
      </div>
      {depth === 0 && (
        <div className="ml-7 mb-1 h-1.5 overflow-hidden rounded-full bg-[color:var(--color-paper-3)]">
          <div
            className="h-full rounded-full"
            style={{
              width: `${Math.max(2, (node.count / max) * 100)}%`,
              backgroundImage: "var(--gradient-brand-h)",
            }}
          />
        </div>
      )}
      {hasKids && isOpen && (
        <ul>
          {node.children.map((c) => (
            <UnitNode
              key={c.id}
              node={c}
              depth={depth + 1}
              max={Math.max(1, ...node.children.map((x) => x.count))}
              expanded={expanded}
              toggle={toggle}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

function UnitBreakdown({ tree }) {
  const [expanded, setExpanded] = useState(() => new Set());
  const toggle = (id) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  const max = Math.max(1, ...tree.map((n) => n.count));
  return (
    <section className="card p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-ink">Nhân sự theo đơn vị</h3>
        <button
          type="button"
          onClick={() =>
            setExpanded((prev) =>
              prev.size ? new Set() : new Set(tree.filter((n) => n.children?.length).map((n) => n.id))
            )
          }
          className="text-xs font-medium text-accent-text hover:underline"
        >
          {expanded.size ? "Thu gọn tất cả" : "Mở tất cả"}
        </button>
      </div>
      <ul className="mt-2 divide-y divide-rule">
        {tree.length === 0 && <li className="py-2.5 text-sm text-muted">Chưa có dữ liệu</li>}
        {tree.map((n) => (
          <UnitNode key={n.id} node={n} depth={0} max={max} expanded={expanded} toggle={toggle} />
        ))}
      </ul>
    </section>
  );
}

function DistList({ title, rows }) {
  const max = Math.max(1, ...rows.map((r) => r.count));
  return (
    <section className="card p-5">
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      <ul className="mt-3 divide-y divide-rule">
        {rows.length === 0 && <li className="py-2.5 text-sm text-muted">Chưa có dữ liệu</li>}
        {rows.map((r) => (
          <li key={r.key} className="py-2.5">
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="min-w-0 truncate text-ink-2">{r.label}</span>
              <span className="tabular shrink-0 font-medium text-ink">{r.count}</span>
            </div>
            <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-[color:var(--color-paper-3)]">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${Math.max(2, (r.count / max) * 100)}%`,
                  backgroundImage: "var(--gradient-brand-h)",
                }}
              />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useDashboard();
  const { user } = useAuth();
  const rootRef = useRef(null);

  useEffect(() => {
    const el = rootRef.current;
    if (!el) return;
    el.querySelectorAll(".reveal").forEach((n, i) =>
      setTimeout(() => n.classList.add("is-in"), 60 * i)
    );
  }, [data]);

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const byStatus = Object.entries(data.by_status).map(([k, v]) => ({
    key: k,
    label: EMPLOYEE_STATUS_LABELS[k] || k,
    count: v,
  }));

  return (
    <div ref={rootRef} className="space-y-5">
      {/* Welcome */}
      <section className="card relative overflow-hidden p-6">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-10 -top-10 h-44 w-56 opacity-[0.09] [clip-path:polygon(30%_0,100%_0,100%_100%,0_60%)]"
          style={{ backgroundImage: "var(--gradient-brand)" }}
        />
        <div className="relative">
          <h1 className="text-xl font-bold tracking-tight text-ink">
            {greeting()}, {user?.full_name || "bạn"}
          </h1>
          <p className="mt-1 text-sm text-[#64748b]">
            Đây là tổng quan hoạt động nhân sự trong phạm vi đơn vị của bạn hôm nay.
          </p>
        </div>
      </section>

      {/* Stat cards */}
      <div className="reveal grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard Icon={IconPeople} value={data.total_working} label="Nhân sự đang làm việc" />
        <StatCard
          Icon={IconOrg}
          value={data.units_with_staff ?? data.by_unit.length}
          label="Đơn vị có nhân sự"
        />
        <StatCard
          Icon={IconRefresh}
          value={data.recent_transfers.length}
          label="Chuyển đơn vị gần đây"
        />
        <StatCard
          Icon={IconPosition}
          value={Object.keys(data.by_status).length}
          label="Nhóm trạng thái"
        />
      </div>

      <div className="reveal grid gap-4 lg:grid-cols-2">
        <UnitBreakdown tree={data.by_unit} />
        <DistList title="Nhân sự theo trạng thái" rows={byStatus} />
      </div>

      <section className="reveal card p-5">
        <h3 className="text-sm font-semibold text-ink">Chuyển đơn vị gần đây</h3>
        {data.recent_transfers.length === 0 ? (
          <p className="mt-3 text-sm text-muted">Chưa có lượt chuyển đơn vị nào</p>
        ) : (
          <ul className="mt-3 divide-y divide-rule text-sm">
            {data.recent_transfers.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center gap-x-2 gap-y-1 py-2.5">
                <IconArrowRight size={14} className="text-accent" />
                <span className="text-ink-2">{a.unit?.path || a.unit?.name}</span>
                <span className="text-muted">·</span>
                <span className="text-ink-2">{a.position?.name}</span>
                <span className="ml-auto text-xs text-muted">{formatDate(a.start_date)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
