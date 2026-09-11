import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { goisoPublicApi, goisoErr } from "../../lib/goisoQueueApi";
import { QRCodeImg } from "../../components/goiso/QRCodeImg";
import { CreditFooter } from "../../components/goiso/CreditFooter";
import { LoadingState } from "../../components/ui/DataStates";

const LABELS = {
  booked: ["Đang chờ đến hẹn", "bg-amber-100 text-amber-700"],
  checked_in: ["Đã check-in — đã có số", "bg-emerald-100 text-emerald-700"],
  cancelled: ["Đã huỷ", "bg-slate-200 text-slate-600"],
  expired: ["Đã hết hạn (quá giờ hẹn)", "bg-red-100 text-red-700"],
};

export default function BookingLookupPage() {
  const { token } = useParams();
  const [appt, setAppt] = useState(null);
  const [err, setErr] = useState("");
  const [cancelling, setCancelling] = useState(false);

  const load = () => {
    setErr("");
    goisoPublicApi
      .bookingAppt(token)
      .then(setAppt)
      .catch((e) => setErr(goisoErr(e, "Không tải được")));
  };

  useEffect(load, [token]);

  const onCancel = async () => {
    if (!window.confirm("Huỷ lịch hẹn này?")) return;
    setCancelling(true);
    try {
      await goisoPublicApi.bookingCancel(token);
      load();
    } catch (e) {
      window.alert(goisoErr(e, "Không huỷ được"));
    } finally {
      setCancelling(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f1f5f9] pb-16 text-slate-800">
      <main className="mx-auto max-w-md p-5">
        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6">
          {!appt && !err && <LoadingState label="Đang tải…" />}
          {err && <div className="text-sm text-red-600">{err}</div>}
          {appt && (
            <div>
              <div className="text-sm text-slate-500">Mã lịch hẹn</div>
              <div className="my-1 font-mono text-3xl font-extrabold tracking-widest">{appt.code}</div>
              {(() => {
                const [txt, cls] = LABELS[appt.status] || [appt.status, "bg-slate-200"];
                return <div className={"inline-block rounded px-2 py-1 text-xs font-semibold " + cls}>{txt}</div>;
              })()}
              <dl className="mt-4 space-y-1 text-sm">
                <Row label="Chi nhánh" value={appt.branch_name} strong />
                <Row label="Thủ tục" value={appt.service_short} />
                <Row label="Ngày hẹn" value={appt.slot_date} strong />
                <Row label="Khung giờ" value={`${appt.slot_start}–${appt.slot_end}`} strong />
                <Row label="Người hẹn" value={appt.citizen_name} />
                {appt.queue_no && <Row label="Số thứ tự" value={appt.queue_no} strong />}
              </dl>
              {appt.status === "booked" && (
                <>
                  <div className="my-4 flex justify-center">
                    <QRCodeImg value={typeof window !== "undefined" ? window.location.href : ""} />
                  </div>
                  <button
                    type="button"
                    disabled={cancelling}
                    onClick={onCancel}
                    className="w-full rounded-lg border border-red-300 py-2.5 text-sm font-semibold text-red-600 disabled:opacity-60"
                  >
                    Huỷ lịch hẹn
                  </button>
                </>
              )}
              <a href="/dat-lich" className="mt-3 block text-center text-sm text-brand-600 underline">
                Đặt lịch mới
              </a>
            </div>
          )}
        </div>
      </main>
      <CreditFooter />
    </div>
  );
}

function Row({ label, value, strong }) {
  return (
    <div className="flex justify-between">
      <dt className="text-slate-500">{label}</dt>
      <dd className={"text-right " + (strong ? "font-semibold" : "")}>{value}</dd>
    </div>
  );
}
