/* Đọc số thứ tự bằng tiếng Việt + chuông báo — port từ goiso static/js/common.js
 * (không phụ thuộc DOM/khung, dùng được thẳng trong React). */
import { API_BASE_URL } from "./constants";

const ONES = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"];

// Đọc số nguyên 0..999 thành chữ (dùng cho số quầy)
export function docSo(n) {
  n = parseInt(n, 10);
  if (Number.isNaN(n)) return "";
  if (n < 10) return ONES[n];
  if (n < 20) {
    const d = n % 10;
    if (d === 0) return "mười";
    if (d === 5) return "mười lăm";
    return "mười " + ONES[d];
  }
  if (n < 100) {
    const c = Math.floor(n / 10),
      d = n % 10;
    let s = ONES[c] + " mươi";
    if (d === 1) s += " mốt";
    else if (d === 4) s += " tư";
    else if (d === 5) s += " lăm";
    else if (d > 0) s += " " + ONES[d];
    return s;
  }
  const tr = Math.floor(n / 100),
    rest = n % 100;
  let s = ONES[tr] + " trăm";
  if (rest === 0) return s;
  if (rest < 10) return s + " lẻ " + ONES[rest];
  return s + " " + docSo(rest);
}

// "A-025" -> "A không hai mươi lăm"
export function docSoThuTu(fullNo) {
  const m = String(fullNo).toUpperCase().match(/^([A-Z]+)[-\s]?0*(\d+)$/);
  if (!m) return String(fullNo);
  const letter = m[1].split("").join(" ");
  const s = String(parseInt(m[2], 10)).padStart(3, "0");
  const head = ONES[+s[0]];
  const tail = docSo(parseInt(s.slice(1), 10) || 0);
  return `${letter} ${head} ${tail}`;
}

export function buildCallSentence(template, fullNo, counterNo) {
  return (template || "Xin mời số thứ tự {so}, đến quầy số {quay}")
    .replace("{so}", docSoThuTu(fullNo))
    .replace("{quay}", docSo(counterNo));
}

let audioCtx = null;
export function chime() {
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
    const ctx = audioCtx;
    const now = ctx.currentTime;
    [880, 1174, 1568].forEach((f, i) => {
      const o = ctx.createOscillator(),
        gn = ctx.createGain();
      o.type = "sine";
      o.frequency.value = f;
      o.connect(gn);
      gn.connect(ctx.destination);
      const t = now + i * 0.16;
      gn.gain.setValueAtTime(0.0001, t);
      gn.gain.exponentialRampToValueAtTime(0.3, t + 0.02);
      gn.gain.exponentialRampToValueAtTime(0.0001, t + 0.34);
      o.start(t);
      o.stop(t + 0.36);
    });
  } catch {
    /* Web Audio không khả dụng — bỏ qua chuông */
  }
}

let viVoice = null;
function pickViVoice() {
  if (!("speechSynthesis" in window)) return;
  const voices = speechSynthesis.getVoices();
  viVoice =
    voices.find((v) => /vi[-_]VN/i.test(v.lang) || /vietnam/i.test(v.name)) ||
    voices.find((v) => v.lang && v.lang.toLowerCase().startsWith("vi")) ||
    null;
}
if (typeof window !== "undefined" && "speechSynthesis" in window) {
  pickViVoice();
  speechSynthesis.onvoiceschanged = pickViVoice;
  let tries = 0;
  const t = setInterval(() => {
    pickViVoice();
    if (viVoice || ++tries > 24) clearInterval(t);
  }, 500);
}

export function viVoiceName() {
  return viVoice ? viVoice.name || "vi-VN" : "";
}

export function speak(text, { rate = 0.95, repeat = 2, gap = 700 } = {}) {
  if (!("speechSynthesis" in window)) return;
  pickViVoice();
  speechSynthesis.cancel();
  let i = 0;
  const sayOnce = () => {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "vi-VN";
    if (viVoice) u.voice = viVoice;
    u.rate = rate;
    u.pitch = 1;
    u.onend = () => {
      i += 1;
      if (i < repeat) setTimeout(sayOnce, gap);
    };
    speechSynthesis.speak(u);
  };
  sayOnce();
}

/* Ghép base API '/api' -> gốc site để build URL phát trực tiếp (thẻ <audio>). */
const API_ROOT = API_BASE_URL.replace(/\/api\/?$/, "");

export function ttsUrl(branchCode, text, voice = "") {
  const q = new URLSearchParams({ text });
  if (voice) q.set("voice", voice);
  return `${API_ROOT}/api/b/${encodeURIComponent(branchCode)}/tts?${q.toString()}`;
}

let ttsAudio = null;
export function speakVi(branchCode, text, { rate = 1, repeat = 2, gap = 600, mode = "server", voice = "" } = {}) {
  if (mode !== "server") {
    speak(text, { rate: rate * 0.95, repeat, gap: gap + 100 });
    return;
  }
  try {
    if (ttsAudio) ttsAudio.pause();
  } catch {
    /* ignore */
  }
  const url = ttsUrl(branchCode, text, voice);
  let i = 0,
    fellBack = false;
  const fallback = () => {
    if (fellBack || i > 0) return;
    fellBack = true;
    speak(text, { rate: rate * 0.95, repeat, gap: gap + 100 });
  };
  const playOnce = () => {
    const a = new Audio(url);
    ttsAudio = a;
    a.playbackRate = Math.min(1.5, Math.max(0.6, rate));
    a.addEventListener("ended", () => {
      i += 1;
      if (i < repeat) setTimeout(playOnce, gap);
    });
    a.addEventListener("error", fallback);
    const p = a.play();
    if (p && p.catch) p.catch(fallback);
  };
  playOnce();
}

export function fmtTime(s) {
  if (!s) return "";
  const d = new Date(s.replace(" ", "T"));
  if (Number.isNaN(d.getTime())) return s.slice(11, 16);
  return d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
}

export function elapsed(s) {
  if (!s) return "";
  const d = new Date(s.replace(" ", "T"));
  const sec = Math.max(0, Math.floor((Date.now() - d.getTime()) / 1000));
  const m = Math.floor(sec / 60),
    ss = sec % 60;
  return `${m}:${String(ss).padStart(2, "0")}`;
}
