import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { branchApi } from "../../lib/goisoQueueApi";
import { useGoisoStream } from "../../lib/goisoStream";
import { chime, speak, speakVi, ttsUrl, buildCallSentence, viVoiceName } from "../../lib/goisoVoice";
import { CreditFooter } from "../../components/goiso/CreditFooter";

const WEEKDAYS = ["Chủ nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"];

async function pickTargetScreen(fsTarget) {
  if (fsTarget == null || !window.getScreenDetails) return null;
  try {
    const det = await window.getScreenDetails();
    const idx = parseInt(fsTarget, 10);
    if (Number.isInteger(idx) && det.screens[idx]) return det.screens[idx];
    return det.screens.find((s) => !s.isPrimary) || det.currentScreen || null;
  } catch {
    return null;
  }
}
async function goFullscreen(fsTarget) {
  const el = document.documentElement;
  if (!el.requestFullscreen) return;
  const scr = await pickTargetScreen(fsTarget);
  try {
    await el.requestFullscreen(scr ? { screen: scr } : undefined);
  } catch {
    try {
      await el.requestFullscreen();
    } catch {
      /* ignore */
    }
  }
}

function statusLabel(s) {
  if (s === "active") return { text: "● Đang phục vụ", cls: "text-emerald-600" };
  if (s === "paused") return { text: "● Tạm dừng", cls: "text-amber-500" };
  return { text: "● Ngoài giờ / nghỉ", cls: "text-slate-400" };
}

/* /b/:code/display — màn hình TV đầy đủ: lưới quầy + spotlight + đọc số. */
export default function DisplayPage() {
  const { code } = useParams();
  const [params] = useSearchParams();
  const fsTarget = params.has("fs") ? params.get("fs") : null;
  const screenId = params.get("screen") || "";
  const onlyCounters = (params.get("counters") || "").split(",").map((s) => s.trim()).filter(Boolean);
  const autoplay = params.get("autoplay") === "1";

  const api = useMemo(() => branchApi(code), [code]);
  const [gateOpen, setGateOpen] = useState(autoplay && fsTarget == null);
  const [audioState, setAudioState] = useState({ text: "🔇 Chưa bật tiếng — chạm màn hình", ok: false });
  const [cfg, setCfg] = useState({
    voice_rate: 0.95, voice_repeat: 2,
    voice_template: "Xin mời số thứ tự {so}, đến quầy số {quay}", spotlight_seconds: 20,
  });
  const [now, setNow] = useState(new Date());
  const [snapshot, setSnapshot] = useState(null);
  const [screens, setScreens] = useState(null);
  const [screenErr, setScreenErr] = useState(false);
  const [spotlight, setSpotlight] = useState(null); // {full_no, service_color, counter_no, service_name}
  const [pulseId, setPulseId] = useState(null);
  const [dim, setDim] = useState(false);
  const [disconnected, setDisconnected] = useState(false);
  const [needsVoice, setNeedsVoice] = useState(false);
  const [testMsg, setTestMsg] = useState({ text: "", ok: null });

  const audioReadyRef = useRef(gateOpen);
  const downSinceRef = useRef(0);
  const lastCallKeyRef = useRef(null);
  const spotlightTimerRef = useRef(null);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    let alive = true;
    api.screens().then((l) => alive && setScreens(l)).catch(() => alive && setScreens([]));
    return () => {
      alive = false;
    };
  }, [api]);

  useEffect(() => {
    if (screens === null || !screenId) return;
    setScreenErr(!screens.find((s) => s.id === screenId));
  }, [screens, screenId]);

  const loadCfg = () => api.configPublic().then((d) => setCfg((c) => ({ ...c, ...d.extra }))).catch(() => {});

  useEffect(() => {
    loadCfg();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!gateOpen) return undefined;
    const chk = () => setNeedsVoice((cfg.tts_mode || "server") === "browser" && !viVoiceName());
    chk();
    const t = setInterval(chk, 4000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gateOpen, cfg.tts_mode]);

  const openGate = () => {
    audioReadyRef.current = true;
    chime();
    setAudioState({ text: "🔊 Đã bật tiếng", ok: true });
    goFullscreen(fsTarget);
    setGateOpen(true);
    loadCfg();
  };

  useEffect(() => {
    if (autoplay && fsTarget == null) setAudioState({ text: "🔊 Đã bật tiếng (autoplay)", ok: true });
    // chỉ chạy 1 lần lúc mở trang
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Nhấn phím bất kỳ cũng mở được cổng (kiosk có remote/bàn phím, không chỉ chạm màn hình).
  useEffect(() => {
    if (gateOpen) return undefined;
    const onKey = () => openGate();
    window.addEventListener("keydown", onKey, { once: true });
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gateOpen]);

  const onTestVoice = () => {
    audioReadyRef.current = true;
    setAudioState({ text: "🔊 Đã bật tiếng", ok: true });
    loadCfg();
    setGateOpen(true);
    setTestMsg({ text: "Đang tải âm thanh…", ok: null });
    chime();
    const mode = cfg.tts_mode || "server";
    if (mode !== "server") {
      setTestMsg({ text: "Chế độ giọng trình duyệt (" + (viVoiceName() || "không có giọng Việt") + ")", ok: null });
      speak("Kiểm tra âm thanh, một hai ba", { rate: 0.95, repeat: 1 });
      return;
    }
    const a = new Audio(ttsUrl(code, "Kiểm tra âm thanh. Xin mời số thứ tự A một, đến quầy số một.", cfg.tts_voice || ""));
    a.addEventListener("playing", () => setTestMsg({ text: "✓ Máy chủ đọc OK", ok: true }));
    a.addEventListener("error", () => setTestMsg({ text: "✗ Lỗi tải âm thanh máy chủ", ok: false }));
    a.play()
      .then(() => setTestMsg({ text: "✓ Đang phát giọng máy chủ", ok: true }))
      .catch((e) => setTestMsg({ text: "✗ Trình duyệt chặn phát: " + e.name, ok: false }));
  };

  useEffect(() => {
    const onShow = (e) => {
      if (e.persisted) window.location.reload();
    };
    window.addEventListener("pageshow", onShow);
    return () => window.removeEventListener("pageshow", onShow);
  }, []);
  useEffect(() => {
    const t = setInterval(() => {
      if (downSinceRef.current && Date.now() - downSinceRef.current > 60000) window.location.reload();
    }, 10000);
    return () => clearInterval(t);
  }, []);
  useEffect(() => {
    const t = setInterval(() => {
      const d = new Date();
      if (d.getHours() === 0 && d.getMinutes() === 5) window.location.reload();
    }, 60000);
    return () => clearInterval(t);
  }, []);

  const screenCounters = useMemo(() => {
    if (!screenId || !screens) return [];
    return screens.find((s) => s.id === screenId)?.counters || [];
  }, [screens, screenId]);
  const inScreen = (c) => !screenCounters.length || screenCounters.includes(c.id) || screenCounters.includes(c.no);

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
    } else if (ev.type === "call") {
      if (screenCounters.length && !screenCounters.includes(ev.counter_id) && !screenCounters.includes(ev.counter_no)) return;
      const key = ev.id + "|" + (ev.is_recall ? "t" + Date.now() : "n");
      if (key === lastCallKeyRef.current) return;
      lastCallKeyRef.current = key;

      setSpotlight(ev);
      setDim(false);
      clearTimeout(spotlightTimerRef.current);
      spotlightTimerRef.current = setTimeout(() => setDim(true), (cfg.spotlight_seconds || 20) * 1000);

      setPulseId(null);
      requestAnimationFrame(() => setPulseId(ev.counter_id));

      if (!audioReadyRef.current) {
        setAudioState({ text: "🔇 Có lượt gọi nhưng CHƯA BẬT TIẾNG — chạm vào màn hình", ok: false });
      } else {
        chime();
        const text = buildCallSentence(cfg.voice_template, ev.full_no, ev.counter_no);
        setTimeout(
          () => speakVi(code, text, { rate: cfg.voice_rate, repeat: cfg.voice_repeat, mode: cfg.tts_mode || "server", voice: cfg.tts_voice || "" }),
          650
        );
      }
    }
  });

  if (screenErr) {
    return <div className="grid min-h-screen place-items-center text-slate-500">Màn hình không tồn tại.</div>;
  }

  let counters = (snapshot?.counters || []).filter(inScreen);
  if (onlyCounters.length) counters = counters.filter((c) => onlyCounters.includes(c.no) || onlyCounters.includes(c.id));
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
    <div className="flex h-screen select-none flex-col">
      <style>{`
        @keyframes goisoPulse { 0%{box-shadow:0 0 0 0 rgba(79,70,229,.55)} 70%{box-shadow:0 0 0 22px rgba(79,70,229,0)} 100%{box-shadow:0 0 0 0 rgba(79,70,229,0)} }
        @keyframes goisoSlideIn { from{opacity:0;transform:translateY(18px)} to{opacity:1;transform:translateY(0)} }
        .goiso-pulse { animation: goisoPulse 1.1s cubic-bezier(.22,1,.36,1) 3; }
        .goiso-slidein { animation: goisoSlideIn .42s cubic-bezier(.22,1,.36,1); }
      `}</style>

      <header className="flex shrink-0 items-center gap-4 bg-brand-600 px-6 py-3 text-white">
        <div className="leading-tight">
          <div className="text-lg font-semibold tracking-wide md:text-xl">VĂN PHÒNG ĐĂNG KÝ ĐẤT ĐAI</div>
          <div className="text-2xl font-extrabold md:text-3xl">
            Chi nhánh {code}
            {screenName ? ` · ${screenName}` : ""}
          </div>
        </div>
        <div className="ml-auto text-right leading-tight">
          <div className="tabular font-mono text-4xl font-extrabold md:text-5xl">{now.toLocaleTimeString("vi-VN", { hour12: false })}</div>
          <div className="text-base font-medium opacity-90 md:text-lg">
            {WEEKDAYS[now.getDay()]}, ngày {now.getDate()}/{now.getMonth() + 1}/{now.getFullYear()}
          </div>
        </div>
      </header>

      <main className="grid min-h-0 flex-1 gap-4 p-4" style={{ gridTemplateColumns: "38fr 62fr" }}>
        <section
          className="relative flex flex-col items-center justify-center overflow-hidden rounded-2xl border-2 p-6 text-center"
          style={{ borderColor: spotlight ? spotlight.service_color : "rgba(79,70,229,.2)", background: "#fff", opacity: dim ? 0.55 : 1 }}
        >
          <div className="text-2xl font-semibold uppercase tracking-wider text-brand-700">Mời quý khách</div>
          {!spotlight ? (
            <div className="mt-8 text-4xl font-semibold text-slate-400">Chưa có lượt gọi</div>
          ) : (
            <div key={spotlight.id + (spotlight.is_recall ? "-r" : "")} className="goiso-slidein flex flex-col items-center">
              <div
                className="tabular mt-2 font-mono font-extrabold leading-none"
                style={{ fontSize: "clamp(5rem, 16vw, 14rem)", color: spotlight.service_color || "#4f46e5" }}
              >
                {spotlight.full_no}
              </div>
              <div className="mt-4 text-3xl font-semibold text-slate-500">xin mời đến</div>
              <div className="mt-1 font-extrabold text-ink" style={{ fontSize: "clamp(3rem, 8vw, 6.5rem)" }}>
                QUẦY {spotlight.counter_no}
              </div>
              <div className="mt-4 max-w-3xl text-2xl font-semibold md:text-3xl">{spotlight.service_name || ""}</div>
            </div>
          )}
        </section>

        <section className="min-h-0 overflow-hidden">
          <div className="grid h-full auto-rows-fr gap-4" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 340px), 1fr))" }}>
            {counters.map((c) => {
              const st = statusLabel(c.status);
              return (
                <div
                  key={c.id}
                  className={
                    "flex flex-col rounded-2xl border-2 border-slate-200 bg-white p-4 " +
                    (c.status === "active" ? "border-brand-600 " : "") +
                    (c.status === "offline" ? "opacity-45 " : "") +
                    (pulseId === c.id ? "goiso-pulse" : "")
                  }
                >
                  <div className="flex items-center justify-between">
                    <div className="text-2xl font-extrabold">QUẦY {c.no}</div>
                    <div className={"text-sm font-semibold " + st.cls}>{st.text}</div>
                  </div>
                  <div className="mt-1 truncate text-sm text-slate-500" style={{ borderLeft: `4px solid ${c.service_color}`, paddingLeft: 6 }}>
                    {c.service_short || ""}
                  </div>
                  <div className="flex flex-1 items-center justify-center">
                    <div
                      className="tabular font-mono font-extrabold leading-none"
                      style={{ fontSize: "clamp(2.5rem, 6vw, 5rem)", color: c.current_no ? c.service_color : "#cbd5e1" }}
                    >
                      {c.current_no || "—"}
                    </div>
                  </div>
                  <div className="h-5 truncate text-center text-sm text-slate-400">{c.staff_name ? "CB: " + c.staff_name : ""}</div>
                </div>
              );
            })}
          </div>
        </section>
      </main>

      <div className="flex shrink-0 items-center gap-4 overflow-hidden border-t border-slate-200 bg-white px-6 py-3">
        <span className="shrink-0 text-sm font-semibold uppercase tracking-wider text-slate-500">Đã gọi gần đây</span>
        <div className="flex flex-nowrap gap-3 overflow-hidden">
          {recent.length ? (
            recent.map((r, i) => (
              <span key={i} className="tabular flex shrink-0 items-center gap-2 rounded-lg bg-slate-100 px-3 py-1.5 font-mono text-lg font-semibold">
                <b style={{ color: r.service_color }}>{r.full_no}</b>
                <span className="text-slate-400">›</span> Q{r.counter_no}
              </span>
            ))
          ) : (
            <span className="text-slate-400">—</span>
          )}
        </div>
      </div>

      <footer className="flex shrink-0 flex-wrap items-center gap-6 bg-brand-700 px-6 py-3 text-white" style={{ paddingBottom: "3.6rem" }}>
        <span className="text-sm font-semibold uppercase tracking-wider opacity-80">Đang chờ</span>
        <div className="flex flex-wrap gap-4 text-lg font-semibold">
          {waiting.length ? (
            waiting.map((w) => (
              <span key={w.prefix} className="flex items-center gap-2">
                <span className="inline-block h-3 w-3 rounded-full" style={{ background: w.color }} />
                {w.prefix}: <b className="tabular font-mono text-2xl">{w.count}</b>
              </span>
            ))
          ) : (
            <span className="opacity-70">Không có</span>
          )}
        </div>
        <div className="ml-auto text-lg">
          Tổng lượt hôm nay: <b className="tabular font-mono text-2xl">{snapshot?.today_total ?? 0}</b>
        </div>
        <span className="rounded-full px-3 py-1 text-sm font-semibold" style={{ background: audioState.ok ? "#16a34a" : "#dc2626" }}>
          {audioState.text}
        </span>
        <button type="button" onClick={onTestVoice} className="rounded-full bg-white/15 px-3 py-1 text-sm font-semibold hover:bg-white/25">
          🔊 Thử tiếng
        </button>
        {testMsg.text && (
          <span className="text-sm opacity-90" style={{ color: testMsg.ok === false ? "#fecaca" : testMsg.ok ? "#bbf7d0" : undefined }}>
            {testMsg.text}
          </span>
        )}
        {disconnected && <span className="rounded-full bg-red-500 px-3 py-1 text-sm font-semibold">Mất kết nối máy chủ…</span>}
        {needsVoice && <span className="rounded-full bg-amber-500 px-3 py-1 text-sm font-semibold">Chưa có giọng đọc tiếng Việt — chỉ phát chuông</span>}
      </footer>

      {!gateOpen && (
        <div
          className="fixed inset-0 z-50 flex cursor-pointer flex-col items-center justify-center gap-6 bg-brand-600 text-white"
          onClick={openGate}
          onKeyDown={openGate}
          role="button"
          tabIndex={0}
        >
          <div className="text-3xl font-bold">Chi nhánh {code}</div>
          <div className="text-xl opacity-90">
            {fsTarget != null ? "Chạm để hiển thị toàn màn hình ở màn hình phụ" : "Chạm hoặc nhấn phím bất kỳ để bắt đầu"}
          </div>
          <div className="text-6xl">🔊</div>
          <div className="text-sm opacity-70">Bật âm thanh &amp; toàn màn hình</div>
        </div>
      )}
      <CreditFooter />
    </div>
  );
}
