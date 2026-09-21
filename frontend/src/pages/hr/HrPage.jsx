import { Navigate, NavLink, Outlet, useLocation } from "react-router-dom";
import clsx from "clsx";
import { useAuth } from "../../auth/AuthContext";
import { MODULE_PERMS, PERMISSIONS } from "../../lib/constants";
import { PageHeader } from "../../components/ui/primitives";

/* Danh mục tab của trang Nhân sự DUY NHẤT — cùng khuôn mẫu với trang Công việc
 * (WorkPage): thêm mục mới chỉ cần 1 dòng ở đây + 1 route con trong App.jsx.
 * `end` cho tab Tổng quan để nó không sáng theo mọi trang con. */
const TABS = [
  { to: "/nhan-su", label: "Tổng quan nhân sự", anyOf: MODULE_PERMS.NHANSU, end: true },
  { to: "/nhan-su/nhan-vien", label: "Danh sách nhân sự", anyOf: [PERMISSIONS.EMPLOYEE_VIEW] },
  { to: "/nhan-su/co-cau", label: "Cơ cấu đơn vị", anyOf: [PERMISSIONS.UNIT_VIEW] },
  { to: "/nhan-su/chuc-vu", label: "Chức vụ", anyOf: [PERMISSIONS.POSITION_VIEW] },
];

/* Đường cũ /employees/... (đã lưu link/bookmark) -> /nhan-su/nhan-vien/... */
export function LegacyEmployeeRedirect() {
  const { pathname, search } = useLocation();
  return <Navigate to={pathname.replace(/^\/employees/, "/nhan-su/nhan-vien") + search} replace />;
}

export default function HrPage() {
  const { hasAnyPermission } = useAuth();
  const tabs = TABS.filter((t) => hasAnyPermission(t.anyOf));

  return (
    <div>
      <PageHeader title="Nhân sự" />
      {tabs.length === 0 ? (
        <p className="text-sm text-muted">Bạn chưa được cấp quyền mục nào trong Nhân sự.</p>
      ) : (
        <>
          <div className="mb-6 flex flex-wrap gap-1 border-b border-rule">
            {tabs.map((t) => (
              <NavLink
                key={t.to}
                to={t.to}
                end={t.end}
                className={({ isActive }) =>
                  clsx(
                    "-mb-px rounded-t-lg border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "border-[color:var(--color-accent)] text-accent-text"
                      : "border-transparent text-muted hover:text-ink-2"
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
