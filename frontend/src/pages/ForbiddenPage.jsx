import { Link } from "react-router-dom";

export default function ForbiddenPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="text-6xl">🚫</div>
      <h1 className="mt-4 text-2xl font-semibold text-slate-800">Không có quyền truy cập</h1>
      <p className="mt-2 max-w-md text-slate-500">
        Tài khoản của bạn không được cấp quyền cho chức năng này. Vui lòng liên hệ quản trị viên.
      </p>
      <Link to="/" className="btn-primary mt-6">
        Về trang tổng quan
      </Link>
    </div>
  );
}
