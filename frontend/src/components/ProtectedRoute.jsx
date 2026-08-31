import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Spinner } from "./ui/Spinner";

/**
 * Bảo vệ route: yêu cầu đăng nhập, tùy chọn yêu cầu permission.
 * Lưu ý: đây chỉ là lớp bảo vệ trải nghiệm; backend vẫn luôn kiểm tra quyền.
 */
export function ProtectedRoute({ children, permission, anyOf }) {
  const { isAuthenticated, loading, hasPermission, hasAnyPermission } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner label="Đang tải phiên đăng nhập..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (permission && !hasPermission(permission)) {
    return <Navigate to="/403" replace />;
  }
  if (anyOf && !hasAnyPermission(anyOf)) {
    return <Navigate to="/403" replace />;
  }

  return children;
}
