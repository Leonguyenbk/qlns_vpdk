import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { MODULE_PERMS } from "../lib/constants";
import { Avatar } from "../components/ui/primitives";
import {
  IconPeople,
  IconKey,
  IconArrowRight,
  IconLogout,
} from "../components/ui/icons";

function greeting() {
  const h = new Date().getHours();
  if (h < 11) return "Chào buổi sáng";
  if (h < 14) return "Chào buổi trưa";
  if (h < 18) return "Chào buổi chiều";
  return "Chào buổi tối";
}

/* Đích của module Gọi số theo quyền của tài khoản. Các trang này là route React
 * toàn màn hình riêng (không sidebar) — điều hướng bằng href là đủ. */
function goisoTarget(user, hasAny) {
  if (hasAny(["goiso.admin"])) return "/admin/goiso/branches";
  const code = user?.goiso_branch_code;
  if (hasAny(["goiso.counter"]) && code) return `/b/${code}/counter`;
  if (code) return `/b/${code}/cho`;
  return "/admin/goiso/branches";
}

function AppCard({ title, desc, Icon, tone, onOpen }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="card group flex w-full flex-col gap-4 p-6 text-left transition-transform hover:-translate-y-0.5"
    >
      <span
        className="grid h-14 w-14 place-items-center rounded-2xl text-white"
        style={{ backgroundImage: tone }}
      >
        <Icon size={26} />
      </span>
      <span className="min-w-0">
        <span className="block text-lg font-bold text-ink">{title}</span>
        <span className="mt-1 block text-sm text-[#64748b]">{desc}</span>
      </span>
      <span className="mt-1 inline-flex items-center gap-1 text-sm font-semibold text-accent-text">
        Mở <IconArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" />
      </span>
    </button>
  );
}

export default function PortalPage() {
  const { user, logout, hasAnyPermission } = useAuth();
  const unitName = user?.roles?.map((r) => r.name).join(" · ") || "Người dùng";

  const cards = [];
  if (hasAnyPermission(MODULE_PERMS.NHANSU)) {
    cards.push({
      key: "nhansu",
      title: "Quản lý nhân sự",
      desc: "Hồ sơ nhân sự, cơ cấu đơn vị, chức vụ, phân công công tác.",
      Icon: IconPeople,
      tone: "linear-gradient(135deg,#2563eb,#7c3aed)",
      onOpen: () => (window.location.href = "/nhan-su"),
    });
  }
  if (hasAnyPermission(MODULE_PERMS.GOISO)) {
    cards.push({
      key: "goiso",
      title: "Bốc số – Gọi số",
      desc: "Kiosk lấy số, bàn gọi số theo quầy, màn hình chờ, đặt lịch hẹn.",
      Icon: IconKey,
      tone: "linear-gradient(135deg,#0891b2,#2563eb)",
      onOpen: () => (window.location.href = goisoTarget(user, hasAnyPermission)),
    });
  }
  if (hasAnyPermission(MODULE_PERMS.ADMIN)) {
    cards.push({
      key: "admin",
      title: "Quản trị hệ thống",
      desc: "Tài khoản, vai trò & quyền, nhật ký thao tác.",
      Icon: IconKey,
      tone: "linear-gradient(135deg,#7c3aed,#db2777)",
      onOpen: () => (window.location.href = "/admin"),
    });
  }

  return (
    <div className="min-h-screen bg-canvas">
      <header className="flex h-16 items-center gap-3 border-b border-rule bg-paper px-5 md:px-8">
        <span
          className="grid h-9 w-9 place-items-center rounded-[10px] text-sm font-bold text-white"
          style={{ backgroundImage: "var(--gradient-brand)" }}
        >
          VP
        </span>
        <span className="text-sm font-bold text-ink">Cổng ứng dụng · VPĐK Đất đai</span>
        <div className="ml-auto flex items-center gap-3">
          <span className="hidden text-right leading-tight sm:block">
            <span className="block text-sm font-medium text-[#334155]">{user?.full_name}</span>
            <span className="block text-xs text-[#94a3b8]">{unitName}</span>
          </span>
          <Avatar name={user?.full_name} size={34} />
          <button
            type="button"
            onClick={() => logout().then(() => (window.location.href = "/login"))}
            className="inline-flex items-center gap-1.5 rounded-lg border border-rule px-2.5 py-1.5 text-sm text-ink-2 hover:bg-[#f1f5f9]"
          >
            <IconLogout size={15} /> Đăng xuất
          </button>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl px-5 py-10 md:px-8 md:py-14">
        <h1 className="text-2xl font-bold text-ink md:text-3xl">
          {greeting()}, {user?.full_name?.split(" ").slice(-1)[0] || "bạn"}
        </h1>
        <p className="mt-1.5 text-sm text-[#64748b]">Chọn ứng dụng để bắt đầu.</p>

        {cards.length === 0 ? (
          <div className="card mt-8 p-6 text-sm text-[#64748b]">
            Tài khoản của bạn chưa được cấp quyền vào ứng dụng nào. Liên hệ quản trị viên.
          </div>
        ) : (
          <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {cards.map((c) => (
              <AppCard key={c.key} {...c} />
            ))}
          </div>
        )}

        <div className="mt-10 flex flex-wrap gap-x-6 gap-y-2 text-sm">
          <a href="/cho" className="font-medium text-accent-text hover:underline">
            Xem hàng chờ các chi nhánh
          </a>
          <a href="/dat-lich" className="font-medium text-accent-text hover:underline">
            Đặt lịch hẹn online
          </a>
          <Link to="/doi-mat-khau" className="font-medium text-accent-text hover:underline">
            Đổi mật khẩu
          </Link>
        </div>
      </main>
    </div>
  );
}
