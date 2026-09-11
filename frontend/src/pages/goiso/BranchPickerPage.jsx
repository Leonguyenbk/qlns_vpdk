import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../../auth/AuthContext";
import { goisoPublicApi } from "../../lib/goisoQueueApi";
import { LoadingState, ErrorState } from "../../components/ui/DataStates";
import { CreditFooter } from "../../components/goiso/CreditFooter";

/* /cho — chọn 1 trong các chi nhánh để xem bảng chờ. Công khai, không cần đăng nhập. */
export default function BranchPickerPage() {
  const { isAuthenticated, hasAnyPermission } = useAuth();
  const { data: branches, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["goiso", "public-branches"],
    queryFn: goisoPublicApi.branches,
  });

  return (
    <div className="min-h-screen bg-[#f1f5f9] pb-16">
      <header className="bg-brand-600 px-6 py-5 text-white">
        <div className="mx-auto flex max-w-5xl items-center gap-4">
          <div>
            <div className="text-sm font-semibold opacity-90 tracking-wide">
              VĂN PHÒNG ĐĂNG KÝ ĐẤT ĐAI
            </div>
            <div className="text-2xl font-extrabold">Chọn chi nhánh để xem hàng chờ</div>
          </div>
          <nav className="ml-auto flex items-center gap-2 text-sm">
            <a href="/dat-lich" className="rounded-lg bg-white/15 px-3 py-1.5 hover:bg-white/25">
              Đặt lịch hẹn
            </a>
            {isAuthenticated && (
              <a href="/" className="rounded-lg bg-white/15 px-3 py-1.5 hover:bg-white/25">
                Cổng ứng dụng
              </a>
            )}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl p-6">
        {isLoading && <LoadingState />}
        {isError && <ErrorState error={error} onRetry={refetch} />}
        {branches && !branches.length && <p className="text-slate-500">Chưa có chi nhánh nào đang hoạt động.</p>}
        {branches && branches.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {branches.map((b) => (
              <div key={b.code} className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5">
                <div className="text-lg font-bold leading-tight">{b.name}</div>
                <div className="mb-4 line-clamp-2 text-sm text-slate-500">{b.full_name}</div>
                <a
                  href={`/b/${b.code}/cho`}
                  className="rounded-lg bg-brand-600 px-4 py-2.5 text-center font-semibold text-white hover:bg-brand-700"
                >
                  Xem hàng chờ
                </a>
                {hasAnyPermission?.(["goiso.counter", "goiso.admin"]) && (
                  <div className="mt-2 flex flex-wrap gap-2 text-sm">
                    <a href={`/b/${b.code}/counter`} className="rounded-lg border border-slate-300 px-3 py-1.5">
                      Bàn gọi số
                    </a>
                    <a href={`/b/${b.code}/man-hinh`} className="rounded-lg border border-slate-300 px-3 py-1.5">
                      Màn hình TV
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
      <CreditFooter />
    </div>
  );
}
