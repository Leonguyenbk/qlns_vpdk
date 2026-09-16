import { Navigate, NavLink, Outlet } from "react-router-dom";
import clsx from "clsx";
import { useAuth } from "../../auth/AuthContext";
import { PERMISSIONS } from "../../lib/constants";
import { PageHeader } from "../../components/ui/primitives";

/* Danh mục tab của trang quản trị DUY NHẤT. Thêm module mới sau này chỉ cần
 * thêm 1 dòng ở đây + 1 route con trong App.jsx — không tạo trang admin riêng. */
const TABS = [
  { to: "users", label: "Tài khoản", anyOf: [PERMISSIONS.USER_VIEW] },
  { to: "roles", label: "Vai trò & quyền", anyOf: [PERMISSIONS.ROLE_VIEW] },
  {
    to: "audit-logs",
    label: "Nhật ký hệ thống",
    anyOf: [PERMISSIONS.AUDIT_VIEW],
  },
  {
    to: "goiso/branches",
    label: "Gọi số · Chi nhánh",
    anyOf: [PERMISSIONS.GOISO_ADMIN],
  },
  {
    to: "goiso/stats",
    label: "Gọi số · Thống kê",
    anyOf: [PERMISSIONS.GOISO_ADMIN, PERMISSIONS.GOISO_VIEW],
  },
  {
    to: "goiso/devices",
    label: "Gọi số · Thiết bị",
    anyOf: [PERMISSIONS.GOISO_ADMIN],
  },
  {
    to: "kpi/ky-danh-gia",
    label: "KPI · Kỳ đánh giá",
    anyOf: [PERMISSIONS.KPI_PERIOD_MANAGE],
  },
  {
    to: "kpi/bo-tieu-chi",
    label: "KPI · Bộ tiêu chí",
    anyOf: [PERMISSIONS.KPI_CRITERIA_MANAGE],
  },
  {
    to: "kpi/danh-muc-san-pham",
    label: "KPI · Danh mục sản phẩm",
    anyOf: [PERMISSIONS.KPI_CRITERIA_MANAGE],
  },
];

/* /admin trần (không chọn tab) -> tự vào tab đầu tiên mà tài khoản có quyền,
 * để tài khoản chỉ có quyền gọi số (không có user.view) không bị chặn 403. */
export function AdminIndexRedirect() {
  const { hasAnyPermission } = useAuth();
  const first = TABS.find((t) => hasAnyPermission(t.anyOf));
  return <Navigate to={first ? first.to : "users"} replace />;
}

export default function AdminPage() {
  const { hasAnyPermission } = useAuth();
  const tabs = TABS.filter((t) => hasAnyPermission(t.anyOf));

  return (
    <div>
      <PageHeader
        eyebrow="Quản trị hệ thống"
        title="Quản trị"
        subtitle="Tài khoản, phân quyền, nhật ký và cấu hình gọi số — tất cả trong một trang."
      />
      {tabs.length === 0 ? (
        <p className="text-sm text-muted">
          Bạn chưa được cấp quyền quản trị mục nào.
        </p>
      ) : (
        <>
          <div className="mb-6 flex flex-wrap gap-1 border-b border-rule">
            {tabs.map((t) => (
              <NavLink
                key={t.to}
                to={t.to}
                className={({ isActive }) =>
                  clsx(
                    "-mb-px rounded-t-lg border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "border-[color:var(--color-accent)] text-accent-text"
                      : "border-transparent text-muted hover:text-ink-2",
                  )
                }
              >
                {t.label}
              </NavLink>
            ))}
          </div>
          <Outlet />
        </>
      )}
    </div>
  );
}
