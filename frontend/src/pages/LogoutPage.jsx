import { useEffect } from "react";
import { useAuth } from "../auth/AuthContext";

/* Đăng xuất DỨT ĐIỂM cho cả SPA lẫn trang Jinja gọi số:
 * - AuthContext.logout() gọi /api/auth/logout (server xoá cookie JWT) + xoá tokenStore.
 * Sau đó về /login với trạng thái sạch -> không còn vòng lặp chuyển hướng. */
export default function LogoutPage() {
  const { logout } = useAuth();
  useEffect(() => {
    try {
      Object.keys(sessionStorage)
        .filter((k) => k.startsWith("login_bounce:"))
        .forEach((k) => sessionStorage.removeItem(k));
    } catch {
      /* ignore */
    }
    logout().finally(() => window.location.replace("/login"));
  }, [logout]);

  return (
    <div className="grid min-h-screen place-items-center bg-canvas text-sm text-muted">
      Đang đăng xuất…
    </div>
  );
}
