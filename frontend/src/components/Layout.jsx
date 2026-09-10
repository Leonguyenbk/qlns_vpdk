import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import clsx from "clsx";
import { useAuth } from "../auth/AuthContext";
import { PERMISSIONS } from "../lib/constants";
import { Avatar } from "./ui/primitives";
import { CommandPalette } from "./CommandPalette";
import {
  IconOverview,
  IconPeople,
  IconOrg,
  IconPosition,
  IconKey,
  IconShield,
  IconLog,
  IconMenu,
  IconClose,
  IconLogout,
  IconChevronLeft,
  IconChevronRight,
  IconChevronDown,
  IconSearch,
} from "./ui/icons";

/* Menu + routing unchanged — only grouped for the sidebar. Each item keeps its
 * permission gate (`anyOf`); groups with no visible item are dropped. */
const NAV_GROUPS = [
  {
    title: null,
    items: [{ to: "/", label: "Tổng quan", Icon: IconOverview, exact: true }],
  },
  {
    title: "Quản lý",
    items: [
      { to: "/employees", label: "Nhân sự", Icon: IconPeople, anyOf: [PERMISSIONS.EMPLOYEE_VIEW] },
      { to: "/units", label: "Cơ cấu đơn vị", Icon: IconOrg, anyOf: [PERMISSIONS.UNIT_VIEW] },
      { to: "/positions", label: "Chức vụ", Icon: IconPosition, anyOf: [PERMISSIONS.POSITION_VIEW] },
    ],
  },
  {
    title: "Hệ thống",
    items: [
      { to: "/users", label: "Tài khoản", Icon: IconKey, anyOf: [PERMISSIONS.USER_VIEW] },
      { to: "/roles", label: "Vai trò & quyền", Icon: IconShield, anyOf: [PERMISSIONS.ROLE_VIEW] },
      { to: "/audit-logs", label: "Nhật ký hệ thống", Icon: IconLog, anyOf: [PERMISSIONS.AUDIT_VIEW] },
    ],
  },
];

const CRUMBS = {
  "": "Tổng quan",
  employees: "Nhân sự",
  units: "Cơ cấu đơn vị",
  positions: "Chức vụ",
  users: "Tài khoản",
  roles: "Vai trò & quyền",
  "audit-logs": "Nhật ký hệ thống",
  new: "Thêm mới",
  edit: "Chỉnh sửa",
  transfer: "Chuyển đơn vị",
  history: "Lịch sử",
};

const COLLAPSE_KEY = "qlns:sidebar_collapsed";

function SidebarItem({ item, collapsed, onNavigate }) {
  const { Icon, label, to, exact } = item;
  return (
    <NavLink
      to={to}
      end={exact}
      onClick={onNavigate}
      className={({ isActive }) =>
        clsx(
          "group/item relative mx-2.5 my-1 flex h-11 items-center gap-3 rounded-[10px] px-3 text-sm transition-all duration-150",
          collapsed && "justify-center px-0",
          isActive
            ? "font-semibold text-white shadow-[var(--shadow-active)]"
            : "font-medium text-[#475569] hover:translate-x-0.5 hover:bg-[#f1f5f9] hover:text-accent-text"
        )
      }
      style={({ isActive }) =>
        isActive ? { backgroundImage: "var(--gradient-brand-h)" } : undefined
      }
    >
      {({ isActive }) => (
        <>
          <Icon
            size={19}
            className={clsx(
              "shrink-0 transition-colors",
              isActive ? "text-white" : "text-[#64748b] group-hover/item:text-[#6366f1]"
            )}
          />
          {!collapsed && <span className="truncate">{label}</span>}
          {collapsed && (
            <span
              role="tooltip"
              className="pointer-events-none absolute left-full ml-3 whitespace-nowrap rounded-md bg-graphite px-2 py-1 text-xs font-medium text-graphite-ink opacity-0 shadow-[var(--shadow-pop)] transition-opacity delay-100 duration-150 group-hover/item:opacity-100"
            >
              {label}
            </span>
          )}
        </>
      )}
    </NavLink>
  );
}

function UserMenu({ user, onLogout, collapsed }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const roles = user?.roles?.map((r) => r.name).join(" · ") || "Người dùng";

  useEffect(() => {
    if (!open) return;
    const onDoc = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex items-center gap-2.5 rounded-xl border border-transparent px-1.5 py-1 transition-colors hover:bg-[#f1f5f9]"
      >
        <span className="inline-flex rounded-md ring-2 ring-[rgba(99,102,241,0.18)]">
          <Avatar name={user?.full_name} size={34} />
        </span>
        {!collapsed && (
          <span className="hidden text-left leading-tight sm:block">
            <span className="block max-w-[11rem] truncate text-sm font-medium text-[#334155]">
              {user?.full_name}
            </span>
            <span className="block max-w-[11rem] truncate text-xs text-[#94a3b8]">{roles}</span>
          </span>
        )}
        <IconChevronDown size={15} className="hidden text-[#94a3b8] sm:block" />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-60 overflow-hidden rounded-xl border border-rule bg-paper shadow-[var(--shadow-pop)]"
          style={{ zIndex: "var(--z-header)" }}
        >
          <div className="border-b border-rule px-4 py-3">
            <p className="truncate text-sm font-medium text-ink">{user?.full_name}</p>
            <p className="truncate text-xs text-muted">{roles}</p>
          </div>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setOpen(false);
              onLogout();
            }}
            className="flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-sm text-ink-2 transition-colors hover:bg-[#f1f5f9] hover:text-accent-text"
          >
            <IconLogout size={16} />
            Đăng xuất
          </button>
        </div>
      )}
    </div>
  );
}

export function Layout() {
  const { user, logout, hasAnyPermission } = useAuth();
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem(COLLAPSE_KEY) === "1";
    } catch {
      return false;
    }
  });
  const [mobileOpen, setMobileOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    try {
      localStorage.setItem(COLLAPSE_KEY, collapsed ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, [collapsed]);

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const visibleGroups = NAV_GROUPS.map((g) => ({
    ...g,
    items: g.items.filter((it) => !it.anyOf || hasAnyPermission(it.anyOf)),
  })).filter((g) => g.items.length > 0);

  const paletteItems = visibleGroups.flatMap((g) =>
    g.items.map((it) => ({ to: it.to, label: it.label, icon: <it.Icon size={16} /> }))
  );

  const crumbs = location.pathname
    .split("/")
    .filter(Boolean)
    .map((seg) => (/^\d+$/.test(seg) ? "Chi tiết" : CRUMBS[seg] || null))
    .filter(Boolean);

  const onLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const railWidth = collapsed ? "md:w-[76px]" : "md:w-64";

  return (
    <div className="flex min-h-screen bg-canvas text-ink-2">
      {/* ── Sidebar ── */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 flex w-[270px] flex-col bg-paper shadow-[var(--shadow-sidebar)]",
          "border-r border-rule transition-[width,transform] duration-[250ms] ease-[cubic-bezier(0.4,0,0.2,1)]",
          "md:static md:translate-x-0",
          railWidth,
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
        style={{ zIndex: "var(--z-rail)" }}
      >
        {/* Brand */}
        <div className="flex h-16 items-center gap-3 px-4">
          <span
            className="grid h-9 w-9 shrink-0 place-items-center rounded-[10px] text-sm font-bold text-white"
            style={{ backgroundImage: "var(--gradient-brand)" }}
          >
            NS
          </span>
          {!collapsed && (
            <span className="min-w-0">
              <span className="block truncate text-[0.9rem] font-bold leading-tight text-ink">
                Quản lý nhân sự
              </span>
              <span className="block truncate text-[11px] text-[#94a3b8]">
                Văn phòng Đăng ký Đất đai
              </span>
            </span>
          )}
          <button
            className="ml-auto rounded-lg p-1.5 text-[#64748b] hover:bg-[#f1f5f9] md:hidden"
            onClick={() => setMobileOpen(false)}
            aria-label="Đóng menu"
          >
            <IconClose size={18} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto overflow-x-hidden py-2">
          {visibleGroups.map((group, gi) => (
            <div key={group.title || "root"} className={gi > 0 ? "mt-3" : ""}>
              {group.title &&
                (collapsed ? (
                  <div className="mx-4 my-2 border-t border-rule" />
                ) : (
                  <p className="px-6 pb-1.5 pt-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#94a3b8]">
                    {group.title}
                  </p>
                ))}
              {group.items.map((item) => (
                <SidebarItem
                  key={item.to}
                  item={item}
                  collapsed={collapsed}
                  onNavigate={() => setMobileOpen(false)}
                />
              ))}
            </div>
          ))}
        </nav>

        {/* Collapse toggle — desktop only */}
        <button
          className={clsx(
            "hidden items-center gap-2 border-t border-rule px-4 py-3 text-sm text-[#64748b] transition-colors hover:bg-[#f1f5f9] hover:text-accent-text md:flex",
            collapsed && "justify-center px-0"
          )}
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? "Mở rộng thanh bên" : "Thu gọn thanh bên"}
        >
          {collapsed ? <IconChevronRight size={18} /> : <IconChevronLeft size={18} />}
          {!collapsed && <span>Thu gọn</span>}
        </button>
      </aside>

      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-[color:var(--color-scrim)] md:hidden"
          style={{ zIndex: "var(--z-overlay)" }}
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* ── Content column ── */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header
          className="sticky top-0 flex h-16 items-center gap-3 border-b border-rule px-4 backdrop-blur-[12px] md:px-6"
          style={{ zIndex: "var(--z-header)", background: "var(--color-paper-blur)" }}
        >
          <button
            className="rounded-lg border border-rule bg-[#f8fafc] p-2 text-[#64748b] transition-colors hover:bg-[#eef2ff] hover:text-accent-text md:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Mở menu"
          >
            <IconMenu size={18} />
          </button>

          {/* Breadcrumb */}
          <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-1.5 text-sm">
            <Link to="/" className="shrink-0 text-[#94a3b8] transition-colors hover:text-accent-text">
              Dashboard
            </Link>
            {crumbs.map((c, i) => (
              <span key={i} className="flex min-w-0 items-center gap-1.5">
                <span className="text-[#cbd5e1]">/</span>
                <span
                  className={clsx(
                    "truncate",
                    i === crumbs.length - 1 ? "font-medium text-[#334155]" : "text-[#94a3b8]"
                  )}
                >
                  {c}
                </span>
              </span>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2.5">
            <button
              type="button"
              onClick={() => setPaletteOpen(true)}
              className="flex h-9 items-center gap-2 rounded-lg border border-rule bg-[#f8fafc] px-2.5 text-sm text-[#64748b] transition-colors hover:bg-[#eef2ff] hover:text-accent-text"
              aria-label="Tìm kiếm / đi tới trang"
            >
              <IconSearch size={16} />
              <span className="hidden lg:inline">Đi tới trang…</span>
              <kbd className="ml-1 hidden rounded border border-rule bg-paper px-1.5 text-[11px] font-medium text-[#94a3b8] lg:inline">
                Ctrl K
              </kbd>
            </button>

            <UserMenu user={user} onLogout={onLogout} collapsed={false} />
          </div>
        </header>

        <main className="flex-1 bg-canvas p-6 md:p-8">
          <div className="mx-auto w-full max-w-[100rem]">
            <Outlet />
          </div>
        </main>
      </div>

      <CommandPalette open={paletteOpen} setOpen={setPaletteOpen} items={paletteItems} />
    </div>
  );
}
