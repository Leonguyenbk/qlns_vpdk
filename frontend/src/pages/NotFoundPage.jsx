import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="text-6xl">🧭</div>
      <h1 className="mt-4 text-2xl font-semibold text-slate-800">Không tìm thấy trang</h1>
      <p className="mt-2 text-slate-500">Đường dẫn bạn truy cập không tồn tại hoặc đã bị di chuyển.</p>
      <Link to="/" className="btn-primary mt-6">
        Về trang tổng quan
      </Link>
    </div>
  );
}
