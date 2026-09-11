import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { useGoisoBranchConfig, useGoisoBranchConfigMutation } from "../../../hooks/useGoiso";
import { goisoErrorMessage } from "../../../lib/goisoApi";
import { LoadingState, ErrorState } from "../../../components/ui/DataStates";
import { Button, FormField, TextInput, Select, Textarea } from "../../../components/ui/primitives";
import { IconChevronLeft, IconPlus, IconClose } from "../../../components/ui/icons";

const SUB_TABS = [
  { key: "services", label: "Dịch vụ" },
  { key: "counters", label: "Quầy" },
  { key: "screens", label: "Màn hình" },
  { key: "extra", label: "Cấu hình chung" },
  { key: "booking", label: "Đặt lịch online" },
];

/* dict {key: {...}} <-> [{_key, ...}] để sửa dạng bảng */
const dictToRows = (obj) => Object.entries(obj || {}).map(([_key, v]) => ({ _key, ...v }));
const rowsToDict = (rows) => {
  const out = {};
  for (const r of rows) {
    const { _key, ...rest } = r;
    if (_key?.trim()) out[_key.trim()] = rest;
  }
  return out;
};

function IconBtn({ onClick, title, children }) {
  return (
    <button type="button" onClick={onClick} title={title}
      className="rounded-md p-1.5 text-muted transition-colors hover:bg-[#f1f5f9] hover:text-danger">
      {children}
    </button>
  );
}

function ServicesEditor({ initial, onSave, saving }) {
  const [rows, setRows] = useState(() => dictToRows(initial));
  useEffect(() => setRows(dictToRows(initial)), [initial]);
  const set = (i, patch) => setRows((rs) => rs.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border border-rule">
        <table className="min-w-full text-sm">
          <thead><tr className="border-b border-rule bg-paper-2 text-left text-xs uppercase text-muted">
            <th className="p-2">Mã</th><th className="p-2">Tên đầy đủ</th><th className="p-2">Tên rút gọn</th>
            <th className="p-2">Màu</th><th className="p-2">Giới hạn/ngày</th><th className="p-2">Bật</th><th></th>
          </tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-b border-rule last:border-0">
                <td className="p-2 w-20"><TextInput value={r._key || ""} onChange={(e) => set(i, { _key: e.target.value.toUpperCase() })} /></td>
                <td className="p-2"><TextInput value={r.name || ""} onChange={(e) => set(i, { name: e.target.value })} /></td>
                <td className="p-2"><TextInput value={r.short || ""} onChange={(e) => set(i, { short: e.target.value })} /></td>
                <td className="p-2 w-24"><input type="color" className="h-9 w-full rounded border border-rule" value={r.color || "#4f46e5"} onChange={(e) => set(i, { color: e.target.value })} /></td>
                <td className="p-2 w-28"><TextInput type="number" min="0" value={r.daily_limit ?? 0} onChange={(e) => set(i, { daily_limit: Number(e.target.value) })} /></td>
                <td className="p-2 text-center"><input type="checkbox" checked={r.active !== false} onChange={(e) => set(i, { active: e.target.checked })} /></td>
                <td className="p-2"><IconBtn title="Xoá dịch vụ" onClick={() => setRows((rs) => rs.filter((_, idx) => idx !== i))}><IconClose size={14} /></IconBtn></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between">
        <Button variant="secondary" onClick={() => setRows((rs) => [...rs, { _key: "", name: "", short: "", color: "#4f46e5", daily_limit: 200, active: true }])}>
          <IconPlus size={14} /> Thêm dịch vụ
        </Button>
        <Button disabled={saving} onClick={() => onSave({ services: rowsToDict(rows) })}>Lưu dịch vụ</Button>
      </div>
    </div>
  );
}

function CountersEditor({ initial, onSave, saving }) {
  const [rows, setRows] = useState(() => dictToRows(initial));
  useEffect(() => setRows(dictToRows(initial)), [initial]);
  const set = (i, patch) => setRows((rs) => rs.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border border-rule">
        <table className="min-w-full text-sm">
          <thead><tr className="border-b border-rule bg-paper-2 text-left text-xs uppercase text-muted">
            <th className="p-2">Tên quầy</th><th className="p-2">Dịch vụ phục vụ (mã, cách nhau bởi dấu phẩy)</th>
            <th className="p-2">Thứ tự</th><th className="p-2">Bật</th><th></th>
          </tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-b border-rule last:border-0">
                <td className="p-2 w-48"><TextInput value={r._key || ""} onChange={(e) => set(i, { _key: e.target.value })} placeholder="Quầy số 01" /></td>
                <td className="p-2"><TextInput value={r.prefix || ""} onChange={(e) => set(i, { prefix: e.target.value.toUpperCase() })} placeholder="A,B" /></td>
                <td className="p-2 w-24"><TextInput type="number" value={r.display_order ?? 1} onChange={(e) => set(i, { display_order: Number(e.target.value) })} /></td>
                <td className="p-2 text-center"><input type="checkbox" checked={r.active !== false} onChange={(e) => set(i, { active: e.target.checked })} /></td>
                <td className="p-2"><IconBtn title="Xoá quầy" onClick={() => setRows((rs) => rs.filter((_, idx) => idx !== i))}><IconClose size={14} /></IconBtn></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between">
        <Button variant="secondary" onClick={() => setRows((rs) => [...rs, { _key: `Quầy số ${String(rs.length + 1).padStart(2, "0")}`, prefix: "A", display_order: rs.length + 1, active: true }])}>
          <IconPlus size={14} /> Thêm quầy
        </Button>
        <Button disabled={saving} onClick={() => onSave({ counters: rowsToDict(rows) })}>Lưu quầy</Button>
      </div>
    </div>
  );
}

function ScreensEditor({ initial, onSave, saving }) {
  const [rows, setRows] = useState(() => (initial || []).map((s) => ({ ...s, countersText: (s.counters || []).join(", ") })));
  useEffect(() => setRows((initial || []).map((s) => ({ ...s, countersText: (s.counters || []).join(", ") }))), [initial]);
  const set = (i, patch) => setRows((rs) => rs.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  const onSubmit = () =>
    onSave({
      screens: rows
        .filter((r) => r.name?.trim())
        .map((r) => ({
          id: r.id,
          name: r.name.trim(),
          counters: r.countersText.split(",").map((s) => s.trim()).filter(Boolean),
        })),
    });
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted">
        Mỗi màn hình chỉ hiện các quầy được liệt kê (để trống danh sách quầy = màn hình mặc định, hiện tất cả).
      </p>
      <div className="overflow-x-auto rounded-lg border border-rule">
        <table className="min-w-full text-sm">
          <thead><tr className="border-b border-rule bg-paper-2 text-left text-xs uppercase text-muted">
            <th className="p-2">Tên màn hình (khu)</th><th className="p-2">Quầy hiển thị</th><th></th>
          </tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-b border-rule last:border-0">
                <td className="p-2 w-56"><TextInput value={r.name || ""} onChange={(e) => set(i, { name: e.target.value })} placeholder="Khu A" /></td>
                <td className="p-2"><TextInput value={r.countersText || ""} onChange={(e) => set(i, { countersText: e.target.value })} placeholder="Quầy số 01, Quầy số 02" /></td>
                <td className="p-2"><IconBtn title="Xoá màn hình" onClick={() => setRows((rs) => rs.filter((_, idx) => idx !== i))}><IconClose size={14} /></IconBtn></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between">
        <Button variant="secondary" onClick={() => setRows((rs) => [...rs, { name: "", countersText: "" }])}>
          <IconPlus size={14} /> Thêm màn hình
        </Button>
        <Button disabled={saving} onClick={onSubmit}>Lưu màn hình</Button>
      </div>
    </div>
  );
}

function ExtraEditor({ initial, onSave, saving }) {
  const [v, setV] = useState(initial || {});
  useEffect(() => setV(initial || {}), [initial]);
  const set = (k) => (e) => setV((x) => ({ ...x, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <FormField label="Tên cơ quan (hiện trên màn hình)">
        <TextInput value={v.ten_co_quan || ""} onChange={set("ten_co_quan")} />
      </FormField>
      <FormField label="Giọng đọc số (TTS)">
        <Select value={v.tts_voice || "vi-VN-HoaiMyNeural"} onChange={set("tts_voice")}>
          <option value="vi-VN-HoaiMyNeural">Nữ — Hoài My</option>
          <option value="vi-VN-NamMinhNeural">Nam — Nam Minh</option>
        </Select>
      </FormField>
      <FormField label="Câu đọc số" hint="Dùng {so} và {quay}">
        <TextInput value={v.voice_template || ""} onChange={set("voice_template")} />
      </FormField>
      <FormField label="Số lần đọc lặp lại">
        <TextInput type="number" min="1" max="5" value={v.voice_repeat ?? 2} onChange={set("voice_repeat")} />
      </FormField>
      <label className="flex items-center gap-2 text-sm text-ink-2">
        <input type="checkbox" checked={!!v.lock_time_enabled} onChange={set("lock_time_enabled")} /> Khoá ngoài giờ làm việc
      </label>
      <label className="flex items-center gap-2 text-sm text-ink-2">
        <input type="checkbox" checked={!!v.allow_saturday} onChange={set("allow_saturday")} /> Mở cửa thứ Bảy
      </label>
      <label className="flex items-center gap-2 text-sm text-ink-2">
        <input type="checkbox" checked={!!v.allow_sunday} onChange={set("allow_sunday")} /> Mở cửa Chủ nhật
      </label>
      <label className="flex items-center gap-2 text-sm text-ink-2">
        <input type="checkbox" checked={!!v.qr_enabled} onChange={set("qr_enabled")} /> Hiện mã QR
      </label>
      <FormField label="Link QR (nếu bật)" className="sm:col-span-2">
        <TextInput value={v.link_qr || ""} onChange={set("link_qr")} />
      </FormField>
      <FormField label="Thông báo khi khoá giờ" className="sm:col-span-2">
        <Textarea value={v.lock_message || ""} onChange={set("lock_message")} />
      </FormField>
      <FormField label="Dòng ghi công (footer)" className="sm:col-span-2">
        <Textarea value={v.footer_credit || ""} onChange={set("footer_credit")} />
      </FormField>
      <div className="sm:col-span-2">
        <Button disabled={saving} onClick={() => onSave({ extra: v })}>Lưu cấu hình chung</Button>
      </div>
    </div>
  );
}

function BookingEditor({ initial, onSave, saving }) {
  const [v, setV] = useState(initial || {});
  useEffect(() => setV(initial || {}), [initial]);
  const set = (k) => (e) => setV((x) => ({ ...x, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <label className="flex items-center gap-2 text-sm text-ink-2 sm:col-span-2">
        <input type="checkbox" checked={!!v.enabled} onChange={set("enabled")} />
        <span className="font-medium">Bật đặt lịch hẹn online cho chi nhánh này</span>
      </label>
      <FormField label="Mở lịch trước (ngày)">
        <TextInput type="number" min="0" value={v.open_days_ahead ?? 3} onChange={set("open_days_ahead")} />
      </FormField>
      <FormField label="Độ dài mỗi khung giờ (phút)">
        <TextInput type="number" min="5" value={v.slot_minutes ?? 30} onChange={set("slot_minutes")} />
      </FormField>
      <FormField label="Số lịch hẹn đang chờ tối đa / 1 CCCD">
        <TextInput type="number" min="1" value={v.max_active_per_cccd ?? 1} onChange={set("max_active_per_cccd")} />
      </FormField>
      <FormField label="Cho phép check-in trễ (phút)">
        <TextInput type="number" min="0" value={v.checkin_grace_minutes ?? 15} onChange={set("checkin_grace_minutes")} />
      </FormField>
      <label className="flex items-center gap-2 text-sm text-ink-2 sm:col-span-2">
        <input type="checkbox" checked={v.turnstile !== false} onChange={set("turnstile")} /> Bật xác thực chống spam (Cloudflare Turnstile)
      </label>
      <div className="sm:col-span-2">
        <Button disabled={saving} onClick={() => onSave({ booking: v })}>Lưu cấu hình đặt lịch</Button>
      </div>
    </div>
  );
}

export default function BranchConfigPage() {
  const { code } = useParams();
  const { data, isLoading, isError, error, refetch } = useGoisoBranchConfig(code);
  const mutation = useGoisoBranchConfigMutation(code);
  const [tab, setTab] = useState("services");

  const save = async (patch) => {
    try {
      await mutation.mutateAsync(patch);
      toast.success("Đã lưu");
    } catch (err) {
      toast.error(goisoErrorMessage(err));
    }
  };

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <div>
      <Link to="/admin/goiso/branches" className="mb-3 inline-flex items-center gap-1 text-sm text-muted hover:text-ink-2">
        <IconChevronLeft size={15} /> Danh sách chi nhánh
      </Link>
      <h2 className="mb-4 text-lg font-bold text-ink">{data.branch.full_name}</h2>

      <div className="mb-5 flex flex-wrap gap-1 border-b border-rule">
        {SUB_TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={
              "-mb-px rounded-t-lg border-b-2 px-4 py-2 text-sm font-medium transition-colors " +
              (tab === t.key ? "border-[color:var(--color-accent)] text-accent-text" : "border-transparent text-muted hover:text-ink-2")
            }>
            {t.label}
          </button>
        ))}
      </div>

      <div className="card p-5">
        {tab === "services" && <ServicesEditor initial={data.services} onSave={save} saving={mutation.isPending} />}
        {tab === "counters" && <CountersEditor initial={data.counters} onSave={save} saving={mutation.isPending} />}
        {tab === "screens" && <ScreensEditor initial={data.screens} onSave={save} saving={mutation.isPending} />}
        {tab === "extra" && <ExtraEditor initial={data.extra} onSave={save} saving={mutation.isPending} />}
        {tab === "booking" && <BookingEditor initial={data.booking} onSave={save} saving={mutation.isPending} />}
      </div>
    </div>
  );
}
