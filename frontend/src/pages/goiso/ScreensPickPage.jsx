import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { branchApi } from "../../lib/goisoQueueApi";
import { useQuery } from "@tanstack/react-query";
import { LoadingState, ErrorState } from "../../components/ui/DataStates";

async function openOnSecondary(url, setMsg) {
  const withFs = url + (url.includes("?") ? "&" : "?") + "fs=1&autoplay=1";
  let features = "popup=yes,noopener=no";
  try {
    if (window.getScreenDetails) {
      const det = await window.getScreenDetails();
      const s = det.screens.find((x) => !x.isPrimary);
      if (s) {
        const w = s.availWidth || s.width,
          h = s.availHeight || s.height;
        features = `popup=yes,left=${s.availLeft ?? s.left},top=${s.availTop ?? s.top},width=${w},height=${h}`;
      } else {
        setMsg({ text: "Chỉ thấy 1 màn hình. Cửa sổ hiển thị sẽ mở ở đây — kéo sang màn hình phụ rồi chạm để bật toàn màn hình.", err: true });
      }
    } else {
      setMsg({ text: "Trình duyệt không hỗ trợ chọn màn hình phụ (hãy dùng Chrome/Edge). Cửa sổ mở ra — kéo sang màn hình phụ rồi chạm để bật toàn màn hình.", err: true });
    }
  } catch {
    setMsg({ text: "Chưa được cấp quyền quản lý cửa sổ. Cửa sổ vẫn mở — kéo sang màn hình phụ rồi chạm để bật toàn màn hình.", err: true });
  }
  const win = window.open(withFs, "gosodisplay", features);
  if (!win) {
    setMsg({ text: "Trình duyệt chặn cửa sổ bật lên. Cho phép pop-up cho trang này rồi thử lại.", err: true });
    return;
  }
  setMsg((m) => m.text ? m : { text: "Đã mở cửa sổ hiển thị ở màn hình phụ. Chạm vào cửa sổ đó một lần để bật toàn màn hình + âm thanh.", err: false });
}

export default function ScreensPickPage() {
  const { code } = useParams();
  const { user } = useAuth();
  const api = useMemo(() => branchApi(code), [code]);
  const { data: screens, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["goiso", "screens", code],
    queryFn: api.screens,
  });
  const [msg, setMsg] = useState({ text: "", err: false });

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const others = [
    { title: "Màn hình đầy đủ", desc: "Tất cả quầy của chi nhánh", url: `/b/${code}/display` },
    { title: "Màn hình rút gọn", desc: "Chỉ hiện số vừa gọi + quầy", url: `/b/${code}/display/simple` },
  ];

  return (
    <div className="min-h-screen bg-[#f1f5f9]">
      <header className="flex items-center gap-4 bg-brand-600 px-5 py-3 text-white">
        <div className="text-lg font-extrabold">Chi nhánh {code}</div>
        <nav className="ml-auto flex items-center gap-3 text-sm">
          <span className="opacity-90">{user?.full_name}</span>
          <a href={`/b/${code}/counter`} className="rounded-lg bg-white/15 px-3 py-1.5 hover:bg-white/25">Bàn gọi số</a>
          <a href="/logout" className="rounded-lg bg-white/15 px-3 py-1.5 hover:bg-white/25">Đăng xuất</a>
        </nav>
      </header>

      <main className="mx-auto max-w-3xl p-6">
        <h1 className="mb-1 text-xl font-bold">Chọn màn hình hiển thị</h1>
        <p className="mb-1 text-sm text-slate-500">Mở đúng màn hình cho TV / màn hình phụ tại vị trí này.</p>
        <p className="mb-5 text-sm text-slate-500">
          <b>Màn hình phụ</b>: mở cửa sổ hiển thị sang màn hình thứ 2 rồi chạm một lần để bật toàn màn hình + âm thanh.
          Cần Chrome hoặc Edge; lần đầu trình duyệt hỏi quyền &quot;quản lý cửa sổ trên mọi màn hình&quot;, chọn <b>Cho phép</b>.
        </p>

        {screens?.length > 0 ? (
          <>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Màn hình theo khu</div>
            <div className="mb-6 grid gap-3 sm:grid-cols-2">
              {screens.map((s) => {
                const url = `/b/${code}/display?screen=${encodeURIComponent(s.id)}`;
                return (
                  <div key={s.id} className="rounded-2xl border border-slate-200 bg-white p-5">
                    <div className="text-lg font-bold">{s.name}</div>
                    <div className="mt-1 text-sm text-slate-500">{s.counters?.length ? s.counters.join(", ") : "Chưa gán quầy nào"}</div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <a href={url} target="_blank" rel="noreferrer" className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:border-brand-600">
                        Mở màn hình ↗
                      </a>
                      <button type="button" onClick={() => openOnSecondary(url, setMsg)} className="rounded-lg bg-brand-600 px-3 py-1.5 text-sm text-white hover:bg-brand-700">
                        ▶ Màn hình phụ (toàn màn hình)
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        ) : (
          <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            Chi nhánh chưa cấu hình màn hình theo khu. Quản trị viên vào <b>Quản trị → Gọi số → Chi nhánh → Cấu hình → Màn hình</b> để thêm.
            Trong lúc đó có thể dùng &quot;Màn hình đầy đủ&quot; bên dưới.
          </div>
        )}

        <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Khác</div>
        <div className="grid gap-3 sm:grid-cols-2">
          {others.map((o) => (
            <div key={o.url} className="rounded-2xl border border-slate-200 bg-white p-5">
              <div className="text-lg font-bold">{o.title}</div>
              <div className="mt-1 text-sm text-slate-500">{o.desc}</div>
              <div className="mt-3 flex flex-wrap gap-2">
                <a href={o.url} target="_blank" rel="noreferrer" className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:border-brand-600">
                  Mở màn hình ↗
                </a>
                <button type="button" onClick={() => openOnSecondary(o.url, setMsg)} className="rounded-lg bg-brand-600 px-3 py-1.5 text-sm text-white hover:bg-brand-700">
                  ▶ Màn hình phụ (toàn màn hình)
                </button>
              </div>
            </div>
          ))}
          <a href={`/b/${code}/cho`} target="_blank" rel="noreferrer" className="block rounded-2xl border border-slate-200 bg-white p-5 hover:border-brand-600">
            <div className="text-lg font-bold">Bảng chờ online</div>
            <div className="mt-1 text-sm text-slate-500">Link công khai cho người dân xem từ điện thoại (không cần đăng nhập)</div>
            <div className="mt-3 text-sm font-semibold text-brand-600">Mở trang ↗</div>
          </a>
        </div>

        {msg.text && <p className={"mt-4 text-sm " + (msg.err ? "text-red-600" : "text-emerald-600")}>{msg.text}</p>}
      </main>
    </div>
  );
}
