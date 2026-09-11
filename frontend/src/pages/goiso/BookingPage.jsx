import { useEffect, useRef, useState } from "react";
import { goisoPublicApi, goisoErr } from "../../lib/goisoQueueApi";
import { QRCodeImg } from "../../components/goiso/QRCodeImg";
import { CreditFooter } from "../../components/goiso/CreditFooter";

const WD = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
const pad = (n) => String(n).padStart(2, "0");

function Chip({ active, disabled, onClick, children }) {
  return (
    <button
      type="button"
      disabled={disabled}
      aria-pressed={active}
      onClick={onClick}
      className={
        "rounded-[0.6rem] border px-3.5 py-2 text-sm " +
        (disabled ? "cursor-not-allowed opacity-40 " : "") +
        (active ? "border-brand-600 bg-brand-600 text-white" : "border-slate-300 bg-white")
      }
    >
      {children}
    </button>
  );
}

export default function BookingPage() {
  const [branches, setBranches] = useState(null);
  const [err, setErr] = useState("");
  const [branch, setBranch] = useState(null);
  const [prefix, setPrefix] = useState(null);
  const [date, setDate] = useState(null);
  const [slots, setSlots] = useState(null);
  const [slot, setSlot] = useState(null);
  const [form, setForm] = useState({ name: "", cccd: "", phone: "" });
  const [done, setDone] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [tsKey, setTsKey] = useState("");
  const tsRef = useRef(null);
  const tsWidgetId = useRef(null);
  const formSectionRef = useRef(null);
  const doneSectionRef = useRef(null);

  useEffect(() => {
    goisoPublicApi
      .bookingBranches()
      .then(setBranches)
      .catch((e) => setErr(goisoErr(e)));
    goisoPublicApi.turnstileKey().then(setTsKey).catch(() => {});
  }, []);

  // nạp script Turnstile khi có site key
  useEffect(() => {
    if (!tsKey) return;
    if (document.querySelector('script[data-turnstile]')) return;
    const s = document.createElement("script");
    s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
    s.async = true;
    s.defer = true;
    s.dataset.turnstile = "1";
    document.head.appendChild(s);
  }, [tsKey]);

  const onBranch = (b) => {
    setBranch(b);
    setPrefix(null);
    setDate(null);
    setSlot(null);
    setSlots(null);
    setDone(null);
    setErr("");
  };

  const onService = (p) => {
    setPrefix(p);
    setDate(null);
    setSlot(null);
    setSlots(null);
  };

  const days = branch?.open_days_ahead ?? 3;
  const dateOptions = Array.from({ length: days + 1 }, (_, i) => {
    const now = new Date();
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + i);
    const iso = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    return { iso, label: i === 0 ? "Hôm nay" : `${WD[d.getDay()]} ${d.getDate()}/${d.getMonth() + 1}` };
  });

  const onDate = async (iso) => {
    setDate(iso);
    setSlot(null);
    setErr("");
    try {
      const s = await goisoPublicApi.bookingSlots(branch.code, iso, prefix);
      setSlots(s);
    } catch (e) {
      setErr(goisoErr(e));
    }
  };

  const onSlot = (s) => {
    setSlot(s.start);
    setTimeout(() => {
      formSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      if (tsKey && window.turnstile && tsWidgetId.current === null && tsRef.current) {
        tsWidgetId.current = window.turnstile.render(tsRef.current, { sitekey: tsKey });
      }
    }, 0);
  };

  const onBook = async () => {
    setErr("");
    setSubmitting(true);
    try {
      const turnstile_token = tsKey && window.turnstile ? window.turnstile.getResponse(tsWidgetId.current ?? undefined) : "";
      const r = await goisoPublicApi.bookingBook(branch.code, {
        prefix,
        slot_date: date,
        slot_start: slot,
        citizen_name: form.name,
        cccd: form.cccd,
        phone: form.phone,
        turnstile_token,
      });
      setDone(r);
      setTimeout(() => doneSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 0);
    } catch (e) {
      setErr(goisoErr(e));
      if (tsKey && window.turnstile) window.turnstile.reset(tsWidgetId.current ?? undefined);
    } finally {
      setSubmitting(false);
    }
  };

  const input = "mb-3 w-full rounded-lg border border-slate-300 px-3 py-2";

  return (
    <div className="min-h-screen bg-[#f1f5f9] pb-16 text-slate-800">
      <header className="bg-brand-600 px-6 py-5 text-white">
        <div className="mx-auto max-w-2xl">
          <div className="text-sm font-semibold opacity-90">HỆ THỐNG MỘT CỬA</div>
          <div className="text-2xl font-extrabold">Đặt lịch hẹn online</div>
        </div>
      </header>

      <main className="mx-auto max-w-2xl space-y-5 p-5">
        {err && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{err}</div>}

        {!done && (
          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-1 font-bold">1. Chọn chi nhánh</div>
            <select
              className={input + " mt-2"}
              value={branch?.code || ""}
              onChange={(e) => onBranch(branches.find((b) => b.code === e.target.value) || null)}
            >
              <option value="">— chọn chi nhánh —</option>
              {branches?.map((b) => (
                <option key={b.code} value={b.code}>{b.name}</option>
              ))}
            </select>
            {branch && <p className="mt-2 text-sm text-slate-500">{branch.address}</p>}
            {branches && !branches.length && <p className="mt-2 text-sm text-slate-500">Hiện chưa có chi nhánh nào mở đặt lịch online.</p>}
          </section>
        )}

        {!done && branch && (
          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-2 font-bold">2. Chọn thủ tục</div>
            <div className="flex flex-wrap gap-2">
              {branch.services.map((s) => (
                <Chip key={s.prefix} active={prefix === s.prefix} onClick={() => onService(s.prefix)}>{s.short || s.name}</Chip>
              ))}
            </div>
          </section>
        )}

        {!done && prefix && (
          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-2 font-bold">3. Chọn ngày</div>
            <div className="flex flex-wrap gap-2">
              {dateOptions.map((d) => (
                <Chip key={d.iso} active={date === d.iso} onClick={() => onDate(d.iso)}>{d.label}</Chip>
              ))}
            </div>
          </section>
        )}

        {!done && date && slots && (
          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-2 font-bold">4. Chọn khung giờ</div>
            <div className="flex flex-wrap gap-2">
              {slots.map((s) => (
                <Chip key={s.start} active={slot === s.start} disabled={s.full} onClick={() => onSlot(s)}>
                  {s.start}
                  <span className="block text-[10px] font-normal">{s.full ? "hết chỗ" : "còn " + s.remaining}</span>
                </Chip>
              ))}
            </div>
            {slots.filter((s) => !s.full).length === 0 && <p className="mt-2 text-sm text-slate-500">Không còn khung giờ trống cho ngày này.</p>}
          </section>
        )}

        {!done && slot && (
          <section ref={formSectionRef} className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-3 font-bold">5. Thông tin người hẹn</div>
            <label className="mb-1 block text-sm font-semibold">Họ và tên</label>
            <input className={input} value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
            <label className="mb-1 block text-sm font-semibold">Số CCCD/CMND</label>
            <input inputMode="numeric" className={input} value={form.cccd} onChange={(e) => setForm((f) => ({ ...f, cccd: e.target.value }))} />
            <label className="mb-1 block text-sm font-semibold">Số điện thoại</label>
            <input inputMode="numeric" className={input} value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />
            {tsKey && <div ref={tsRef} className="cf-turnstile my-3" />}
            <button
              type="button"
              disabled={submitting}
              onClick={onBook}
              className="w-full rounded-lg bg-brand-600 py-3 font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {submitting ? "Đang gửi…" : "Xác nhận đặt lịch"}
            </button>
          </section>
        )}

        {done && (
          <section ref={doneSectionRef} className="rounded-2xl border border-emerald-300 bg-white p-6 text-center">
            <div className="text-lg font-bold text-emerald-600">✓ Đặt lịch thành công</div>
            <div className="mt-1 text-sm text-slate-500">Mã lịch hẹn của quý khách</div>
            <div className="my-2 font-mono text-4xl font-extrabold tracking-widest">{done.code}</div>
            <div className="text-sm text-slate-600">
              {done.branch_name}<br />
              {done.service_short} · {done.slot_date} lúc <b>{done.slot_start}–{done.slot_end}</b>
            </div>
            <div className="my-4 flex justify-center">
              <QRCodeImg value={`${location.origin}/lich-hen/${done.token}`} />
            </div>
            <p className="text-sm text-slate-500">Đến kiosk tại sảnh chi nhánh, nhập mã này (hoặc quét QR) trong khung giờ hẹn để lấy số thứ tự.</p>
            <a href={`/lich-hen/${done.token}`} target="_blank" rel="noreferrer" className="mt-3 inline-block text-sm text-brand-600 underline">
              Xem / huỷ lịch hẹn
            </a>
            <div>
              <button type="button" onClick={() => window.location.reload()} className="mt-4 text-sm text-slate-500 underline">
                Đặt lịch khác
              </button>
            </div>
          </section>
        )}
      </main>
      <CreditFooter />
    </div>
  );
}
