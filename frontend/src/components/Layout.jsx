import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import clsx from "clsx";
import { useAuth } from "../auth/AuthContext";
import { PERMISSIONS } from "../lib/constants";
import { Avatar } from "./ui/primitives";

const NAV = [
  { to: "/", label: "Tổng quan", icon: "🏠", exact: true },
  { to: "/employees", label: "Nhân sự", icon: "👥", anyOf: [PERMISSIONS.EMPLOYEE_VIEW] },
  { to: "/units", label: "Cơ cấu đơn vị", icon: "🏢", anyOf: [PERMISSIONS.UNIT_VIEW] },
  { to: "/positions", label: "Chức vụ", icon: "🎖️", anyOf: [PERMISSIONS.POSITION_VIEW] },
  { to: "/users", label: "Tài khoản", icon: "🔑", anyOf: [PERMISSIONS.USER_VIEW] },
  { to: "/roles", label: "Vai trò & quyền", icon: "🛡️", anyOf: [PERMISSIONS.ROLE_VIEW] },
  { to: "/audit-logs", label: "Nhật ký hệ thống", icon: "📜", anyOf: [PERMISSIONS.AUDIT_VIEW] },
];

export function Layout() {
  const { user, logout, hasAnyPermission } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  const visibleNav = NAV.filter((n) => !n.anyOf || hasAnyPermission(n.anyOf));

  const onLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="flex min-h-screen bg-slate-100">
      {/* Sidebar */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-40 flex flex-col bg-brand-800 text-brand-50 transition-all",
          collapsed ? "w-16" : "w-64",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
          "md:static md:translate-x-0"
        )}
      >
        <div className="flex h-16 items-center gap-2 px-4 font-semibold">
          <span className="text-2xl">🗂️</span>
          {!collapsed && <span>Quản lý nhân sự</span>}
        </div>
        <nav className="flex-1 space-y-1 px-2 py-4">
          {visibleNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
                  isActive ? "bg-brand-600 text-white" : "text-brand-100 hover:bg-brand-700"
                )
              }
            >
              <span className="text-lg">{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>
        <button
          className="hidden border-t border-brand-700 px-4 py-3 text-left text-xs text-brand-200 hover:bg-brand-700 md:block"
          onClick={() => setCollapsed((c) => !c)}
        >
          {collapsed ? "➡️ Mở rộng" : "⬅️ Thu gọn"}
        </button>
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-30 bg-slate-900/40 md:hidden" onClick={() => setMobileOpen(false)} />
      )}

      {/* Nội dung */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 shadow-sm">
          <button className="text-2xl md:hidden" onClick={() => setMobileOpen(true)} aria-label="Mở menu">
            ☰
          </button>
          <div className="hidden text-sm text-slate-500 md:block">Hệ thống quản lý nhân sự – Giai đoạn 1</div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-sm font-medium text-slate-800">{user?.full_name}</div>
              <div className="text-xs text-slate-500">
                {user?.roles?.map((r) => r.name).join(", ") || "—"}
              </div>
            </div>
            <Avatar name={user?.full_name} size={36} />
            <button className="btn-secondary px-3 py-1.5 text-xs" onClick={onLogout}>
              Đăng xuất
            </button>
          </div>
        </header>
        <main className="flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
