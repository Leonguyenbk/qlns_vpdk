import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useGoisoDevices, useGoisoKioskReleaseMutation } from "../../../hooks/useGoiso";
import { goisoErrorMessage } from "../../../lib/goisoApi";
import { LoadingState, ErrorState, EmptyState } from "../../../components/ui/DataStates";
import { Table } from "../../../components/ui/Table";
import { Button, FormField, TextInput, Textarea, Badge } from "../../../components/ui/primitives";

function relTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso.replace(" ", "T"));
  if (Number.isNaN(d.getTime())) return iso;
  const mins = Math.round((Date.now() - d.getTime()) / 60000);
  if (mins < 1) return "vừa xong";
  if (mins < 60) return `${mins} phút trước`;
  if (mins < 1440) return `${Math.round(mins / 60)} giờ trước`;
  return `${Math.round(mins / 1440)} ngày trước`;
}

export default function DevicesPage() {
  const { data, isLoading, isError, error, refetch } = useGoisoDevices();
  const setRelease = useGoisoKioskReleaseMutation();
  const [form, setForm] = useState(null);

  useEffect(() => {
    if (data?.release) setForm(data.release);
  }, [data]);

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));

  const onSave = async (e) => {
    e.preventDefault();
    try {
      await setRelease.mutateAsync(form);
      toast.success("Đã cập nhật bản kiosk mới nhất");
    } catch (err) {
      toast.error(goisoErrorMessage(err));
    }
  };

  const columns = [
    { key: "device_id", header: "Thiết bị", render: (d) => <span className="mono text-xs">{d.device_id}</span> },
    { key: "branch_code", header: "Chi nhánh" },
    { key: "name", header: "Tên máy" },
    { key: "version", header: "Phiên bản" },
    { key: "printer", header: "Máy in" },
    { key: "status", header: "Trạng thái", render: (d) => (
        <Badge className={d.status === "online" ? "badge-ok" : "badge-neutral"}>{d.status}</Badge>
      ) },
    { key: "last_seen", header: "Lần cuối", render: (d) => relTime(d.last_seen) },
  ];

  return (
    <div className="space-y-6">
      <div className="card p-0">
        {!data.devices?.length ? (
          <EmptyState title="Chưa có kiosk nào gửi heartbeat" />
        ) : (
          <Table columns={columns} rows={data.devices} rowKey="device_id" />
        )}
      </div>

      <div className="card p-5">
        <h3 className="mb-4 text-sm font-semibold text-ink">Bản kiosk mới nhất (auto-update)</h3>
        {form && (
          <form onSubmit={onSave} className="grid gap-4 sm:grid-cols-2">
            <FormField label="Phiên bản"><TextInput value={form.version || ""} onChange={set("version")} /></FormField>
            <FormField label="SHA-256"><TextInput value={form.sha256 || ""} onChange={set("sha256")} /></FormField>
            <FormField label="Link tải" className="sm:col-span-2">
              <TextInput value={form.download_url || ""} onChange={set("download_url")} />
            </FormField>
            <FormField label="Phiên bản tối thiểu còn hỗ trợ">
              <TextInput value={form.min_supported_version || ""} onChange={set("min_supported_version")} />
            </FormField>
            <label className="flex items-center gap-2 self-end pb-2 text-sm text-ink-2">
              <input type="checkbox" checked={!!form.mandatory} onChange={set("mandatory")} /> Bắt buộc cập nhật
            </label>
            <FormField label="Ghi chú phát hành" className="sm:col-span-2">
              <Textarea value={form.release_notes || ""} onChange={set("release_notes")} />
            </FormField>
            <div className="sm:col-span-2">
              <Button type="submit" disabled={setRelease.isPending}>Lưu</Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
