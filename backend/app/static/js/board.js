/* Bảng chờ online công khai: chỉ hiển thị trạng thái hàng đợi, KHÔNG phát tiếng. */
import { connectStream } from './common.js?v=6';

const $ = (s) => document.querySelector(s);
const WEEKDAYS = ['Chủ nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];

// Lọc theo khu: window.__SCREEN_COUNTERS__ là danh sách tên quầy (= id trong snapshot).
const screenCounters = Array.isArray(window.__SCREEN_COUNTERS__) ? window.__SCREEN_COUNTERS__ : [];
const inScreen = (c) => !screenCounters.length || screenCounters.includes(c.id) || screenCounters.includes(c.no);

// ?fs=1 -> chạm một lần để bật toàn màn hình trên màn hình phụ (Chrome/Edge + HTTPS).
const fsTarget = new URLSearchParams(location.search).get('fs');
if (fsTarget != null) {
  const hint = document.createElement('div');
  hint.textContent = 'Chạm để hiển thị toàn màn hình';
  hint.style.cssText = 'position:fixed;left:50%;bottom:14px;transform:translateX(-50%);background:#0b5fa5;color:#fff;padding:6px 14px;border-radius:999px;font-size:13px;z-index:60;cursor:pointer';
  const goFs = async () => {
    const el = document.documentElement;
    let scr = null;
    if (window.getScreenDetails) {
      try {
        const det = await window.getScreenDetails();
        const idx = parseInt(fsTarget, 10);
        scr = (Number.isInteger(idx) && det.screens[idx]) || det.screens.find(s => !s.isPrimary) || det.currentScreen || null;
      } catch (_) {}
    }
    try { await el.requestFullscreen(scr ? { screen: scr } : undefined); } catch (_) { try { await el.requestFullscreen(); } catch (_) {} }
    hint.remove();
  };
  hint.addEventListener('click', goFs);
  addEventListener('DOMContentLoaded', () => document.body.appendChild(hint));
}

/* -------------------------------------------------- đồng hồ */
function tickClock() {
  const d = new Date();
  $('#clock').textContent = d.toLocaleTimeString('vi-VN', { hour12: false });
  $('#date').textContent = `${WEEKDAYS[d.getDay()]}, ${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`;
}
setInterval(tickClock, 1000);
tickClock();

/* -------------------------------------------------- render */
function statusBadge(s) {
  if (s === 'active') return '<span class="text-emerald-600">● Đang phục vụ</span>';
  if (s === 'paused') return '<span class="text-amber-500">● Tạm dừng</span>';
  return '<span class="text-slate-400">● Ngoài giờ / nghỉ</span>';
}

function renderGrid(counters) {
  const list = counters.filter(inScreen);
  $('#grid').innerHTML = list.map(c => `
    <div class="rounded-xl bg-white border-2 border-slate-200 p-3 flex flex-col ${c.status === 'active' ? 'card-serving' : ''} ${c.status === 'offline' ? 'opacity-45' : ''}">
      <div class="flex items-center justify-between">
        <div class="text-lg font-extrabold">QUẦY ${c.no}</div>
        <div class="text-xs font-semibold">${statusBadge(c.status)}</div>
      </div>
      <div class="text-xs text-slate-500 truncate" style="border-left:4px solid ${c.service_color};padding-left:6px;margin-top:3px;">${c.service_short || ''}</div>
      <div class="flex-1 flex items-center justify-center py-2">
        <div class="font-mono font-extrabold tnum leading-none" style="font-size: clamp(2rem, 7vw, 3.5rem); color:${c.current_no ? c.service_color : '#cbd5e1'};">
          ${c.current_no || '—'}
        </div>
      </div>
    </div>`).join('') || '<div class="text-slate-400 col-span-full">Chưa có quầy nào hoạt động.</div>';
}

function renderTicker(recent) {
  if (screenCounters.length) recent = recent.filter(r => screenCounters.includes(r.counter_id) || screenCounters.includes(r.counter_no));
  $('#ticker').innerHTML = recent.map(r => `
    <span class="shrink-0 rounded-lg bg-slate-100 px-2.5 py-1 text-base font-semibold tnum font-mono flex items-center gap-1.5">
      <b style="color:${r.service_color}">${r.full_no}</b>
      <span class="text-slate-400">›</span> Q${r.counter_no}
    </span>`).join('') || '<span class="text-slate-400">—</span>';
}

function renderWaiting(waiting, total, counters) {
  let list = waiting;
  if (screenCounters.length) {
    const allow = new Set();
    counters.filter(inScreen).forEach(c => (c.prefixes || []).forEach(p => allow.add(p)));
    list = waiting.filter(w => allow.has(w.prefix));
  }
  $('#waiting').innerHTML = list.map(w => `
    <span class="flex items-center gap-2">
      <span class="inline-block w-3 h-3 rounded-full" style="background:${w.color}"></span>
      ${w.prefix}: <b class="tnum font-mono text-xl">${w.count}</b>
    </span>`).join('') || '<span class="opacity-70">Không có</span>';
  $('#total').textContent = total;
}

function applySnapshot(s) {
  renderGrid(s.counters);
  renderTicker(s.recent);
  renderWaiting(s.waiting, s.today_total, s.counters);
}

/* -------------------------------------------------- luồng SSE (chỉ đọc trạng thái) */
// Khôi phục từ bộ nhớ đệm trình duyệt -> tải lại để nối luồng ngay, không cần F5.
window.addEventListener('pageshow', (e) => { if (e.persisted) location.reload(); });

// Watchdog: mất kết nối liên tục quá 60s thì tự tải lại.
let downSince = 0;
setInterval(() => {
  if (downSince && Date.now() - downSince > 60000) location.reload();
}, 10000);

connectStream((ev) => {
  if (ev.type === '_disconnected') {
    if (!downSince) downSince = Date.now();
    $('#conn').classList.remove('hidden');
    return;
  }
  downSince = 0;
  if (ev.type === 'snapshot') {
    $('#conn').classList.add('hidden');
    applySnapshot(ev);
  }
  // bỏ qua 'call': bảng online không phát tiếng, snapshot kèm theo đã đủ cập nhật
});

// tự tải lại lúc 0h05 để sang ngày mới
setInterval(() => {
  const d = new Date();
  if (d.getHours() === 0 && d.getMinutes() === 5) location.reload();
}, 60000);
