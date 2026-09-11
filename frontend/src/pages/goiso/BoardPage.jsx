import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { branchApi } from "../../lib/goisoQueueApi";
import { useGoisoStream } from "../../lib/goisoStream";
import { CreditFooter } from "../../components/goiso/CreditFooter";

const WEEKDAYS = ["Chủ nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"];

function useClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return now;
}

function statusLabel(s) {
  if (s === "active") return { text: "● Đang phục vụ", cls: "text-emerald-600" };
  if (s === "paused") return { text: "● Tạm dừng", cls: "text-amber-500" };
  return { text: "● Ngoài giờ / nghỉ", cls: "text-slate-400" };
}

/* /b/:code/cho — bảng chờ online công khai. KHÔNG phát tiếng. */
export default function BoardPage() {
  const { code } = useParams();
  const [params] = useSearchParams();
  const screenId = params.get("screen") || "";
  const now = useClock();
  const [snapshot, setSnapshot] = useState(null);
  const [screens, setScreens] = useState(null);
  const [screenErr, setScreenErr] = useState(false);
  const [disconnected, setDisconnected] = useState(false);
  const downSinceRef = useRef(0);

  const api = useMemo(() => branchApi(code), [code]);

  useEffect(() => {
    let alive = true;
    api
      .screens()
      .then((list) => alive && setScreens(list))
      .catch(() => alive && setScreens([]));
    return () => {
      alive = false;
    };
  }, [api]);

  useEffect(() => {
    if (screens === null) return;
    if (!screenId) {
      setScreenErr(false);
      return;
    }
    const found = screens.find((s) => s.id === screenId);
    setScreenErr(!found);
  }, [screens, screenId]);

  useGoisoStream(code, (ev) => {
    if (ev.type === "_disconnected") {
      if (!downSinceRef.current) downSinceRef.current = Date.now();
      setDisconnected(true);
      return;
    }
    downSinceRef.current = 0;
    if (ev.type === "snapshot") {
      setDisconnected(false);
      setSnapshot(ev);
    }
  });

  // watchdog: mất kết nối > 60s -> tự tải lại
  useEffect(() => {
    const t = setInterval(() => {
      if (downSinceRef.current && Date.now() - downSinceRef.current > 60000) window.location.reload();
    }, 10000);
    return () => clearInterval(t);
  }, []);
  // 0h05 -> tải lại sang ngày mới
  useEffect(() => {
    const t = setInterval(() => {
      const d = new Date();
      if (d.getHours() === 0 && d.getMinutes() === 5) window.location.reload();
    }, 60000);
    return () => clearInterval(t);
  }, []);

  const screenCounters = useMemo(() => {
    if (!screenId || !screens) return [];
    const sc = screens.find((s) => s.id === screenId);
    return sc?.counters || [];
  }, [screens, screenId]);
  const inScreen = (c) => !screenCounters.length || screenCounters.includes(c.id) || screenCounters.includes(c.no);

  if (screenErr) {
    return <div className="grid min-h-screen place-items-center text-slate-500">Màn hình không tồn tại.</div>;
  }

  const counters = (snapshot?.counters || []).filter(inScreen);
  let recent = snapshot?.recent || [];
  if (screenCounters.length) recent = recent.filter((r) => screenCounters.includes(r.counter_id) || screenCounters.includes(r.counter_no));
  let waiting = snapshot?.waiting || [];
  if (screenCounters.length) {
    const allow = new Set();
    counters.forEach((c) => (c.prefixes || []).forEach((p) => allow.add(p)));
    waiting = waiting.filter((w) => allow.has(w.prefix));
  }
  const screenName = screens?.find((s) => s.id === screenId)?.name;

  return (
    <div className="flex min-h-screen flex-col bg-[#f1f5f9]">
      <header className="flex shrink-0 items-center gap-4 bg-brand-600 px-5 py-3 text-white">
        <div className="min-w-0 leading-tight">
          <div className="truncate text-sm font-semibold opacity-90 md:text-base">VĂN PHÒNG ĐĂNG KÝ ĐẤT ĐAI</div>
          <div className="truncate text-lg font-extrabold md:text-2xl">
            Chi nhánh {code}
            {screenName ? ` · ${screenName}` : ""}
          </div>
        </div>
        <div className="ml-auto shrink-0 text-right leading-tight">
          <div className="tabular font-mono text-2xl font-extrabold md:text-3xl">
            {now.toLocaleTimeString("vi-VN", { hour12: false })}
          </div>
          <div className="text-xs font-medium opacity-90 md:text-sm">
            {WEEKDAYS[now.getDay()]}, {now.getDate()}/{now.getMonth() + 1}/{now.getFullYear()}
          </div>
        </div>
      </header>

      <main className="min-h-0 flex-1 p-4">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Đang phục vụ</div>
        <div className="grid auto-rows-fr gap-3" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 260px), 1fr))" }}>
          {counters.map((c) => {
            const st = statusLabel(c.status);
            return (
              <div
                key={c.id}
                className={
                  "flex flex-col rounded-xl border-2 border-slate-200 bg-white p-3 " +
                  (c.status === "active" ? "border-brand-600" : "") +
                  (c.status === "offline" ? " opacity-45" : "")
                }
              >
                <div className="flex items-center justify-between">
                  <div className="text-lg font-extrabold">QUẦY {c.no}</div>
                  <div className={"text-xs font-semibold " + st.cls}>{st.text}</div>
                </div>
                <div
                  className="mt-0.5 truncate text-xs text-slate-500"
                  style={{ borderLeft: `4px solid ${c.service_color}`, paddingLeft: 6 }}
                >
                  {c.service_short || ""}
                </div>
                <div className="flex flex-1 items-center justify-center py-2">
                  <div
                    className="tabular font-mono font-extrabold leading-none"
                    style={{ fontSize: "clamp(2rem, 7vw, 3.5rem)", color: c.current_no ? c.service_color : "#cbd5e1" }}
                  >
                    {c.current_no || "—"}
                  </div>
                </div>
              </div>
            );
          })}
          {!counters.length && <div className="col-span-full text-slate-400">Chưa có quầy nào hoạt động.</div>}
        </div>
      </main>

      <div className="flex shrink-0 items-center gap-3 overflow-hidden border-t border-slate-200 bg-white px-5 py-2.5">
        <span className="shrink-0 text-xs font-semibold uppercase tracking-wider text-slate-500">Đã gọi gần đây</span>
        <div className="flex flex-nowrap gap-2 overflow-hidden">
          {recent.length ? (
            recent.map((r, i) => (
              <span key={i} className="tabular flex shrink-0 items-center gap-1.5 rounded-lg bg-slate-100 px-2.5 py-1 font-mono text-base font-semibold">
                <b style={{ color: r.service_color }}>{r.full_no}</b>
                <span className="text-slate-400">›</span> Q{r.counter_no}
              </span>
            ))
          ) : (
            <span className="text-slate-400">—</span>
          )}
        </div>
      </div>

      <footer className="flex shrink-0 flex-wrap items-center gap-5 bg-brand-700 px-5 py-3 text-white" style={{ paddingBottom: "3.6rem" }}>
        <span className="text-xs font-semibold uppercase tracking-wider opacity-80">Đang chờ</span>
        <div className="flex flex-wrap gap-4 text-base font-semibold">
          {waiting.length ? (
            waiting.map((w) => (
              <span key={w.prefix} className="flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full" style={{ background: w.color }} />
                {w.prefix}: <b className="tabular font-mono text-xl">{w.count}</b>
              </span>
            ))
          ) : (
            <span className="opacity-70">Không có</span>
          )}
        </div>
        <div className="ml-auto text-sm md:text-base">
          Tổng lượt hôm nay: <b className="tabular font-mono text-xl">{snapshot?.today_total ?? 0}</b>
        </div>
        {disconnected && (
          <span className="rounded-full bg-red-500 px-3 py-1 text-xs font-semibold">Mất kết nối máy chủ…</span>
        )}
      </footer>
      <CreditFooter />
    </div>
  );
}
