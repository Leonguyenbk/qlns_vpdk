import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { branchApi } from "../../lib/goisoQueueApi";
import { useGoisoStream } from "../../lib/goisoStream";
import { chime, speakVi, buildCallSentence, viVoiceName } from "../../lib/goisoVoice";

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

/* /b/:code/display/simple — màn hình rút gọn: chỉ số vừa gọi + quầy. */
export default function DisplaySimplePage() {
  const { code } = useParams();
  const [params] = useSearchParams();
  const fsTarget = params.has("fs") ? params.get("fs") : null;

  const api = useMemo(() => branchApi(code), [code]);
  const [gateOpen, setGateOpen] = useState(false);
  const [cfg, setCfg] = useState({ voice_rate: 0.95, voice_repeat: 2, voice_template: "Xin mời số thứ tự {so}, đến quầy số {quay}" });
  const [call, setCall] = useState(null);
  const [now, setNow] = useState(new Date());
  const [disconnected, setDisconnected] = useState(false);
  const [needsVoice, setNeedsVoice] = useState(false);
  const downSinceRef = useRef(0);
  const audioReadyRef = useRef(false);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const loadCfg = () => api.configPublic().then((d) => setCfg((c) => ({ ...c, ...d.extra }))).catch(() => {});

  const openGate = () => {
    audioReadyRef.current = true;
    chime();
    goFullscreen(fsTarget);
    setGateOpen(true);
    loadCfg();
  };

  useEffect(() => {
    if (!gateOpen) return undefined;
    const chk = () => setNeedsVoice((cfg.tts_mode || "server") === "browser" && !viVoiceName());
    chk();
    const t = setInterval(chk, 4000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gateOpen, cfg.tts_mode]);

  useEffect(() => {
    if (gateOpen) return undefined;
    const onKey = () => openGate();
    window.addEventListener("keydown", onKey, { once: true });
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gateOpen]);

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

  useGoisoStream(code, (ev) => {
    if (ev.type === "_disconnected") {
      if (!downSinceRef.current) downSinceRef.current = Date.now();
      setDisconnected(true);
      return;
    }
    downSinceRef.current = 0;
    if (ev.type === "snapshot") setDisconnected(false);
    else if (ev.type === "call") {
      setCall(ev);
      if (audioReadyRef.current) {
        chime();
        setTimeout(
          () =>
            speakVi(code, buildCallSentence(cfg.voice_template, ev.full_no, ev.counter_no), {
              rate: cfg.voice_rate,
              repeat: cfg.voice_repeat,
              mode: cfg.tts_mode || "server",
              voice: cfg.tts_voice || "",
            }),
          650
        );
      }
    }
  });

  return (
    <div className="relative flex h-screen select-none flex-col bg-white">
      <header className="shrink-0 bg-brand-600 px-6 py-4 text-center text-white">
        <div className="text-xl font-semibold">VĂN PHÒNG ĐĂNG KÝ ĐẤT ĐAI</div>
        <div className="text-3xl font-extrabold">Chi nhánh {code}</div>
      </header>
      <main className="flex flex-1 flex-col items-center justify-center text-center">
        <div className="text-3xl font-semibold uppercase tracking-widest text-slate-500 md:text-5xl">Mời số</div>
        <div
          className="tabular font-mono font-extrabold leading-none text-brand-600"
          style={{ fontSize: "clamp(6rem, 30vw, 26rem)" }}
        >
          {call?.full_no || "—"}
        </div>
        <div className="text-4xl font-extrabold md:text-7xl">{call ? `QUẦY ${call.counter_no}` : " "}</div>
        <div className="mt-4 max-w-5xl px-6 text-2xl font-semibold text-slate-600 md:text-4xl">{call?.service_name || ""}</div>
      </main>
      <footer className="shrink-0 bg-brand-700 px-6 py-3 text-right text-white" style={{ paddingBottom: "3.6rem" }}>
        {disconnected && <span className="mr-3 rounded-full bg-red-500 px-3 py-1 text-sm font-semibold">Mất kết nối…</span>}
        {needsVoice && <span className="mr-3 rounded-full bg-amber-500 px-3 py-1 text-sm font-semibold">Chưa có giọng đọc tiếng Việt</span>}
        <span className="tabular font-mono text-2xl font-bold">{now.toLocaleTimeString("vi-VN", { hour12: false })}</span>
      </footer>

      {!gateOpen && (
        <div
          className="fixed inset-0 z-50 flex cursor-pointer flex-col items-center justify-center gap-4 bg-brand-600 text-white"
          onClick={openGate}
          onKeyDown={openGate}
          role="button"
          tabIndex={0}
        >
          <div className="text-2xl font-bold">
            {fsTarget != null ? "Chạm để hiển thị toàn màn hình ở màn hình phụ" : "Chạm để bắt đầu"}
          </div>
          <div className="text-6xl">🔊</div>
        </div>
      )}
    </div>
  );
}
