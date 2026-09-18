import { Navigate, NavLink, Outlet } from "react-router-dom";
import clsx from "clsx";
import { useAuth } from "../../auth/AuthContext";
import { PERMISSIONS } from "../../lib/constants";
import { PageHeader } from "../../components/ui/primitives";

/* Danh mục tab của trang Công việc DUY NHẤT (Giao việc + KPI) — cùng khuôn mẫu
 * với trang Quản trị (AdminPage): thêm mục mới chỉ cần 1 dòng ở đây + 1 route
 * con trong App.jsx. Tách khỏi "Quản lý" để trang nhân sự chỉ tập trung nhân sự. */
const TABS = [
  { to: "tong-quan", label: "Tổng quan điều hành", anyOf: [PERMISSIONS.TASK_VIEW_ALL] },
  { to: "cua-toi", label: "Công việc của tôi", anyOf: [PERMISSIONS.TASK_VIEW_OWN] },
  { to: "da-giao", label: "Việc tôi đã giao", anyOf: [PERMISSIONS.TASK_CREATE, PERMISSIONS.TASK_ASSIGN] },
  { to: "danh-sach", label: "Danh sách nhiệm vụ", anyOf: [PERMISSIONS.TASK_VIEW_ALL] },
  { to: "kpi", label: "KPI của tôi", anyOf: [PERMISSIONS.KPI_VIEW_OWN] },
];

/* /cong-viec trần -> tự vào tab đầu tiên mà tài khoản có quyền. */
export function WorkIndexRedirect() {
  const { hasAnyPermission } = useAuth();
  const first = TABS.find((t) => hasAnyPermission(t.anyOf));
  return <Navigate to={first ? first.to : "cua-toi"} replace />;
}

export default function WorkPage() {
  const { hasAnyPermission } = useAuth();
  const tabs = TABS.filter((t) => hasAnyPermission(t.anyOf));

  return (
    <div>
      <PageHeader title="Công việc" />
      {tabs.length === 0 ? (
        <p className="text-sm text-muted">Bạn chưa được cấp quyền mục nào trong Công việc.</p>
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
