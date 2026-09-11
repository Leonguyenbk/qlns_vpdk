import { useEffect } from "react";
import { useAuth } from "../auth/AuthContext";

/* Đăng xuất dứt điểm: AuthContext.logout() gọi /api/auth/logout (server xoá
 * cookie JWT) + xoá tokenStore, rồi tải lại /login với trạng thái sạch. */
export default function LogoutPage() {
  const { logout } = useAuth();
  useEffect(() => {
    logout().finally(() => window.location.replace("/login"));
  }, [logout]);

  return (
    <div className="grid min-h-screen place-items-center bg-canvas text-sm text-muted">
      Đang đăng xuất…
    </div>
  );
}
