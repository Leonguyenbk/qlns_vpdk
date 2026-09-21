import { NavLink, useLocation } from "react-router-dom";
import { useNews } from "../components/newsContext";
import clsx from "clsx";

const TABS = [
  { to: "/", label: "Thông báo", exact: true },
  { to: "/tin-tuc", label: "Tin tức", exact: false },
];

export default function NewsTabBar() {
  const { pathname } = useLocation();
  const { newCount, setNewCount } = useNews();

  return (
    <div className="mb-6 flex flex-wrap gap-1 border-b border-rule">
      {TABS.map((t) => {
        const isActive = t.exact
          ? pathname === t.to
          : pathname.startsWith(t.to);
        return (
          <NavLink
            key={t.to}
            to={t.to}
            end={t.exact}
            onClick={() => {
              if (t.to === "/tin-tuc") setNewCount(0);
            }} // Click vào thì ẩn badge
            className={clsx(
              "-mb-px rounded-t-lg border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
              isActive
                ? "border-[color:var(--color-accent)] text-accent-text"
                : "border-transparent text-muted hover:text-ink-2",
            )}
          >
            <span className="relative">
              {t.label}
              {t.to === "/tin-tuc" && newCount > 0 && (
                <span className="absolute -right-4 -top-2 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white">
                  {newCount}
                </span>
              )}
            </span>
          </NavLink>
        );
      })}
    </div>
  );
}
