import { useState } from "react";
import toast from "react-hot-toast";
import { useCatalogGroups, useProducts, useKpiAdminMutations } from "../../../hooks/useKpi";
import { apiErrorMessage } from "../../../lib/api";
import { formatDate, todayISO } from "../../../lib/format";
import { CATALOG_STATUS_LABELS } from "../../../lib/constants";
import { Button, FormField, TextInput, Select } from "../../../components/ui/primitives";
import { LoadingState, ErrorState, EmptyState } from "../../../components/ui/DataStates";

function ConversionForm({ product }) {
  const m = useKpiAdminMutations();
  const [form, setForm] = useState({ kn_value: "", cap_value: "", effective_from: todayISO(), status: "DRAFT" });
  const set = (patch) => setForm((f) => ({ ...f, ...patch }));

  const onSubmit = () => {
    m.createConversion.mutateAsync({
      productId: product.id,
      body: {
        kn_value: form.kn_value ? Number(form.kn_value) : null,
        cap_value: form.cap_value ? Number(form.cap_value) : null,
        effective_from: form.effective_from, status: form.status,
      },
    }).then(() => toast.success("Cấu hình hệ số quy đổi thành công"))
      .catch((err) => toast.error(apiErrorMessage(err)));
  };

  return (
    <div className="mt-2 grid gap-2 border-t border-rule pt-2 sm:grid-cols-5">
      <TextInput type="number" step="0.001" placeholder="Kn (bỏ trống = không quy đổi)" value={form.kn_value} onChange={(e) => set({ kn_value: e.target.value })} />
      <TextInput type="number" step="0.01" placeholder="CAP (bỏ trống = không giới hạn)" value={form.cap_value} onChange={(e) => set({ cap_value: e.target.value })} />
      <TextInput type="date" value={form.effective_from} onChange={(e) => set({ effective_from: e.target.value })} />
      <Select value={form.status} onChange={(e) => set({ status: e.target.value })}>
        <option value="DRAFT">Dự thảo</option><option value="PILOT">Thí điểm</option><option value="OFFICIAL">Chính thức</option>
      </Select>
      <Button variant="secondary" disabled={m.createConversion.isPending} onClick={onSubmit}>Lưu quy đổi</Button>
    </div>
  );
}

export default function ProductsPage() {
  const { data: groups, isLoading: gLoading } = useCatalogGroups();
  const { data: products, isLoading, isError, error, refetch } = useProducts({});
  const m = useKpiAdminMutations();
  const [form, setForm] = useState({ group_code: "", code: "", name: "", unit_of_measure: "", status: "DRAFT" });
  const set = (patch) => setForm((f) => ({ ...f, ...patch }));

  const onCreate = (e) => {
    e.preventDefault();
    if (!form.group_code || !form.code || !form.name) return toast.error("Nhập đủ nhóm, mã và tên sản phẩm.");
    m.createProduct.mutateAsync(form)
      .then(() => { toast.success("Thêm sản phẩm thành công"); setForm({ group_code: "", code: "", name: "", unit_of_measure: "", status: "DRAFT" }); })
      .catch((err) => toast.error(apiErrorMessage(err)));
  };

  if (isLoading || gLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <div className="space-y-5">
      <section className="card p-4">
        <h3 className="mb-2 text-sm font-semibold text-ink">18 nhóm sản phẩm/công việc (Phụ lục II tài liệu dự thảo)</h3>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {groups.map((g) => (
            <div key={g.code} className="rounded-lg border border-rule p-2 text-sm">
              <span className="font-medium text-ink">{g.code}</span> — {g.name}
            </div>
          ))}
        </div>
      </section>

      <form onSubmit={onCreate} className="card grid gap-3 p-4 sm:grid-cols-5">
        <FormField label="Nhóm" required>
          <Select value={form.group_code} onChange={(e) => set({ group_code: e.target.value })}>
            <option value="">— Chọn nhóm —</option>
            {groups.map((g) => <option key={g.code} value={g.code}>{g.code} — {g.name}</option>)}
          </Select>
        </FormField>
        <FormField label="Mã sản phẩm" required><TextInput placeholder="N1.001" value={form.code} onChange={(e) => set({ code: e.target.value })} /></FormField>
        <FormField label="Tên sản phẩm" required><TextInput value={form.name} onChange={(e) => set({ name: e.target.value })} /></FormField>
        <FormField label="Đơn vị tính"><TextInput placeholder="hồ sơ" value={form.unit_of_measure} onChange={(e) => set({ unit_of_measure: e.target.value })} /></FormField>
        <div className="flex items-end"><Button type="submit" disabled={m.createProduct.isPending}>+ Thêm sản phẩm</Button></div>
      </form>

      <section className="space-y-3">
        {products.length === 0 ? (
          <EmptyState title="Chưa có sản phẩm nào trong danh mục" description="Thêm sản phẩm ở biểu mẫu phía trên." />
        ) : (
          products.map((p) => (
            <div key={p.id} className="card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium text-ink">{p.code}</span> — {p.name}
                  <span className="ml-2 badge badge-neutral">{CATALOG_STATUS_LABELS[p.status] || p.status}</span>
                </div>
                <span className="text-xs text-muted">{p.unit_of_measure || "—"}</span>
              </div>
              {p.current_conversion ? (
                <p className="mt-1 text-xs text-muted">
                  Kn = {p.current_conversion.kn_value ?? "chưa cấu hình"} · CAP = {p.current_conversion.cap_value ?? "không giới hạn"} ·
                  hiệu lực từ {formatDate(p.current_conversion.effective_from)}
                </p>
              ) : (
                <p className="mt-1 text-xs text-warn-text">Chưa cấu hình hệ số quy đổi — mặc định không quy đổi, không giới hạn.</p>
              )}
              <ConversionForm product={p} />
            </div>
          ))
        )}
      </section>
    </div>
  );
}
