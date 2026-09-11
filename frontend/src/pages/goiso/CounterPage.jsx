import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import { branchApi, goisoErr } from "../../lib/goisoQueueApi";
import { fmtTime, elapsed } from "../../lib/goisoVoice";

function lsKey(code) {
  return "goiso.counter." + code;
}

export default function CounterPage() {
  const { code } = useParams();
  const { user } = useAuth();
  const api = useMemo(() => branchApi(code), [code]);

  const [counters, setCounters] = useState([]);
  const [counterId, setCounterId] = useState(null); // vào ca chưa
  const [selected, setSelected] = useState("");
  const [setupErr, setSetupErr] = useState("");
  const [view, setView] = useState(null);
  const [err, setErr] = useState("");
  const [connLost, setConnLost] = useState(false);
  const [busy, setBusy] = useState(false);
  const [specific, setSpecific] = useState("");
  const [nowTick, setNowTick] = useState(0);

  const pollRef = useRef(null);

  // khôi phục phiên đã lưu
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(lsKey(code)) || "null");
      if (saved?.counter_id) setCounterId(saved.counter_id);
    } catch {
      /* ignore */
    }
  }, [code]);

  // danh sách quầy cho màn "Vào ca"
  useEffect(() => {
    if (counterId) return;
    api
      .counters()
      .then((list) => {
        setCounters(list);
        if (list.length) setSelected(list[0].id);
      })
      .catch((e) => setSetupErr(goisoErr(e)));
  }, [api, counterId]);

  const backToSetup = useCallback(
    (msg) => {
      try {
        localStorage.removeItem(lsKey(code));
      } catch {
        /* ignore */
      }
      clearInterval(pollRef.current);
      setCounterId(null);
      setView(null);
      if (msg) setSetupErr(msg);
    },
    [code]
  );

  const refresh = useCallback(async () => {
    if (!counterId) return;
    try {
      const v = await api.counter(counterId).view();
      setView(v);
      setConnLost(false);
    } catch {
      setConnLost(true);
    }
  }, [api, counterId]);

  useEffect(() => {
    if (!counterId) return undefined;
    refresh();
    pollRef.current = setInterval(() => {
      if (!document.hidden) refresh();
    }, 3000);
    return () => clearInterval(pollRef.current);
  }, [counterId, refresh]);

  // đồng hồ đầu trang + đếm giờ phục vụ
  useEffect(() => {
    const t = setInterval(() => setNowTick((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, []);

  const onLogin = async () => {
    if (!selected) return;
    try {
      await api.counter(selected).login();
      localStorage.setItem(lsKey(code), JSON.stringify({ counter_id: selected }));
      setCounterId(selected);
      setSetupErr("");
    } catch (e) {
      setSetupErr(goisoErr(e));
    }
  };

  const onSwitch = async () => {
    if (counterId && window.confirm("Kết thúc ca tại quầy này?")) {
      try {
        await api.counter(counterId).status("offline");
      } catch {
        /* ignore */
      }
    }
    try {
      localStorage.removeItem(lsKey(code));
    } catch {
      /* ignore */
    }
    window.location.reload();
  };

  const act = async (fn) => {
    if (busy) return;
    setBusy(true);
    try {
      const v = await fn();
      if (v && Array.isArray(v.waiting)) setView(v);
      else await refresh();
      setErr("");
    } catch (e) {
      const m = goisoErr(e);
      if (/PIN|đăng nhập|Vào ca/i.test(m)) {
        backToSetup("Phiên quầy đã hết hạn, vui lòng Vào ca lại.");
      } else {
        setErr(m);
        setTimeout(() => setErr(""), 4000);
      }
    } finally {
      setBusy(false);
    }
  };

  const c = api.counter(counterId || "");
  const onNext = () => act(() => c.next());
  const onRecall = () => act(() => c.recall());
  const onDone = () => act(() => c.done());
  const onMissed = () => act(() => c.missed());
  const onPause = () => act(() => c.status(view?.status === "paused" ? "active" : "paused"));
  const onCallSpecific = (e) => {
    e.preventDefault();
    const v = specific.trim();
    if (!v) return;
    act(() => c.call(v).then((r) => (setSpecific(""), r)));
  };

  useEffect(() => {
    if (!counterId) return undefined;
    const onKey = (e) => {
      if (e.target.tagName === "INPUT") return;
      if (e.code === "Space") {
        e.preventDefault();
        onNext();
      } else if (e.key.toLowerCase() === "r") onRecall();
      else if (e.key.toLowerCase() === "d") onDone();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [counterId, view, busy]);

  const clock = new Date().toLocaleTimeString("vi-VN", { hour12: false });

  if (!counterId) {
    return (
      <div className="flex min-h-screen flex-col" style={{ paddingBottom: "3.4rem" }}>
        <Header code={code} user={user} clock={clock} connLost={false} onSwitch={null} />
        <div className="flex flex-1 items-center justify-center p-6">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h1 className="mb-1 text-xl font-bold">Vào ca — {user?.full_name}</h1>
            <p className="mb-4 text-sm text-slate-500">Chọn quầy bạn đang ngồi.</p>
            <label className="mb-1 block text-sm font-semibold">Quầy</label>
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="mb-4 w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              {counters.map((c2) => (
                <option key={c2.id} value={c2.id}>
                  {c2.id} — {c2.prefix}
                </option>
              ))}
            </select>
            <button onClick={onLogin} className="w-full rounded-xl bg-brand-600 py-3 text-lg font-semibold text-white hover:bg-brand-700">
              Vào ca
            </button>
            {setupErr && <p className="mt-2 text-sm text-red-600">{setupErr}</p>}
          </div>
        </div>
      </div>
    );
  }

  const cur = view?.current;

  return (
    <div className="flex min-h-screen flex-col" style={{ paddingBottom: "3.4rem" }}>
      <Header code={code} user={user} clock={clock} connLost={connLost} onSwitch={onSwitch} />

      <main className="grid flex-1 gap-4 p-4" style={{ gridTemplateColumns: "1.6fr 1fr" }}>
        <section className="flex flex-col gap-4">
          <div className="flex flex-1 flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-6 text-center">
            <div className="text-sm font-semibold uppercase tracking-wider text-slate-500">Đang phục vụ</div>
            <div
              className="tabular my-2 font-mono font-extrabold leading-none"
              style={{ fontSize: "clamp(4rem, 12vw, 9rem)", color: cur ? cur.service_color : "#94a3b8" }}
            >
              {cur ? cur.full_no : "—"}
            </div>
            <div className="text-xl font-semibold text-slate-600">{cur?.service_short || ""}</div>
            <div className="mt-1 text-lg text-slate-500">{cur?.fullname || ""}</div>
            <div className="mt-3 text-sm text-slate-400">
              Thời gian phục vụ: <span className="tabular font-mono">{cur ? elapsed(cur.since) : "0:00"}</span>
            </div>
          </div>

          <button onClick={onNext} disabled={busy} className="rounded-xl bg-brand-600 py-8 text-3xl font-bold text-white shadow-sm hover:bg-brand-700 disabled:opacity-60">
            GỌI TIẾP <span className="text-base font-normal opacity-70">(phím cách)</span>
          </button>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <button onClick={onRecall} disabled={busy} className="rounded-xl border border-slate-300 bg-white py-4 hover:bg-slate-50">🔊 Gọi lại</button>
            <button onClick={onDone} disabled={busy} className="rounded-xl bg-emerald-600 py-4 text-white hover:bg-emerald-700">✓ Hoàn thành</button>
            <button onClick={onMissed} disabled={busy} className="rounded-xl bg-amber-500 py-4 text-white hover:bg-amber-600">⤺ Vắng</button>
            <button onClick={onPause} disabled={busy} className={"rounded-xl border border-slate-300 py-4 hover:bg-slate-50 " + (view?.status === "paused" ? "bg-amber-100" : "bg-white")}>
              {view?.status === "paused" ? "▶ Tiếp tục" : "⏸ Tạm dừng"}
            </button>
          </div>

          <form onSubmit={onCallSpecific} className="flex gap-2">
            <input
              value={specific}
              onChange={(e) => setSpecific(e.target.value)}
              placeholder="Gọi số cụ thể, VD: A-25"
              className="flex-1 rounded-lg border border-slate-300 px-3 py-3 font-mono uppercase"
            />
            <button className="rounded-lg bg-slate-800 px-5 text-white hover:bg-slate-900">Gọi</button>
          </form>
          {err && <p className="text-sm text-red-600">{err}</p>}
        </section>

        <section className="flex min-h-0 flex-col gap-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="flex items-baseline justify-between">
              <div className="font-bold">Quầy {counterId.replace(/\D/g, "") || counterId}</div>
              <div className="text-sm text-slate-500">CB: {user?.full_name}</div>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2 text-center">
              <div className="rounded-lg bg-slate-50 py-2">
                <div className="tabular text-2xl font-extrabold">{view?.waiting_count ?? 0}</div>
                <div className="text-xs text-slate-500">đang chờ</div>
              </div>
              <div className="rounded-lg bg-slate-50 py-2">
                <div className="tabular text-2xl font-extrabold">{view?.done_today ?? 0}</div>
                <div className="text-xs text-slate-500">đã xử lý</div>
              </div>
            </div>
          </div>

          <div className="flex min-h-0 flex-1 flex-col rounded-2xl border border-slate-200 bg-white p-4">
            <div className="mb-2 font-bold">Hàng chờ</div>
            <div className="flex-1 space-y-1 overflow-y-auto pr-1">
              {view?.waiting?.length ? (
                view.waiting.map((w, i) => (
                  <div key={i} className={"flex items-center gap-2 rounded-lg px-3 py-2 " + (i === 0 ? "border border-brand-600/30 bg-brand-50" : "bg-slate-50")}>
                    <span className="tabular font-mono text-lg font-bold">{w.full_no}</span>
                    {w.source === "online" && <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-700">HẸN</span>}
                    {w.fullname && <span className="truncate text-sm text-slate-500">{w.fullname}</span>}
                    <span className="ml-auto text-xs text-slate-400">{fmtTime(w.time_issue)}</span>
                  </div>
                ))
              ) : (
                <div className="text-sm text-slate-400">Không còn số chờ.</div>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="mb-2 font-bold">Lịch sử gần đây</div>
            <div className="max-h-40 space-y-1 overflow-y-auto text-sm">
              {view?.history?.length ? (
                view.history.map((h, i) => (
                  <div key={i} className="flex justify-between">
                    <span className="tabular font-mono">{h.full_no}</span>
                    <span className={h.status === "done" ? "text-emerald-600" : h.status === "missed" ? "text-amber-600" : "text-brand-600"}>
                      {h.status === "done" ? "xong" : h.status === "missed" ? "vắng" : "đang gọi"}
                    </span>
                    <span className="text-slate-400">{fmtTime(h.time_start)}</span>
                  </div>
                ))
              ) : (
                <div className="text-slate-400">—</div>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function Header({ code, user, clock, connLost, onSwitch }) {
  return (
    <header className="flex items-center gap-4 bg-brand-600 px-5 py-3 text-white">
      <div className="text-lg font-extrabold">Chi nhánh {code}</div>
      <div className="ml-auto flex items-center gap-3 text-sm">
        <span className="opacity-90">CB: <b>{user?.full_name}</b></span>
        {connLost && <span className="rounded-full bg-red-500 px-3 py-1 font-semibold">Mất kết nối…</span>}
        <span className="tabular font-mono text-base font-bold">{clock}</span>
        {onSwitch && (
          <button onClick={onSwitch} className="rounded-lg bg-white/15 px-3 py-1.5 text-sm hover:bg-white/25">
            Đổi quầy
          </button>
        )}
        <a href={`/b/${code}/man-hinh`} className="rounded-lg bg-white/15 px-3 py-1.5 text-sm hover:bg-white/25">Màn hình</a>
        <a href="/logout" className="rounded-lg bg-white/15 px-3 py-1.5 text-sm hover:bg-white/25">Đăng xuất</a>
      </div>
    </header>
  );
}
