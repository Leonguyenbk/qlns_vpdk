import { useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { useGoisoBranchMutations, useGoisoBranches } from "../../../hooks/useGoiso";
import { goisoErrorMessage } from "../../../lib/goisoApi";
import { LoadingState, ErrorState, EmptyState } from "../../../components/ui/DataStates";
import { Table } from "../../../components/ui/Table";
import { Modal } from "../../../components/ui/Modal";
import { Badge, Button, FormField, TextInput } from "../../../components/ui/primitives";
import { IconPlus, IconKey, IconOrg } from "../../../components/ui/icons";

const EMPTY_FORM = { code: "", name: "", full_name: "", address: "" };

export default function BranchesPage() {
  const { data: branches, isLoading, isError, error, refetch } = useGoisoBranches();
  const { create, update, remove, regenKey, regenDisplayToken } = useGoisoBranchMutations();
  const [modal, setModal] = useState(null); // { mode: "create" | "edit", branch? }
  const [form, setForm] = useState(EMPTY_FORM);
  const [formErr, setFormErr] = useState("");

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setFormErr("");
    setModal({ mode: "create" });
  };
  const openEdit = (b) => {
    setForm({ code: b.code, name: b.name, full_name: b.full_name, address: b.address || "" });
    setFormErr("");
    setModal({ mode: "edit", branch: b });
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setFormErr("");
    try {
      if (modal.mode === "create") {
        await create.mutateAsync(form);
        toast.success(`Đã tạo chi nhánh "${form.code}"`);
      } else {
        await update.mutateAsync({
          code: modal.branch.code,
          body: { name: form.name, full_name: form.full_name, address: form.address },
        });
        toast.success("Đã lưu");
      }
      setModal(null);
    } catch (err) {
      setFormErr(goisoErrorMessage(err));
    }
  };

  const toggleActive = async (b) => {
    try {
      await update.mutateAsync({ code: b.code, body: { active: b.active ? 0 : 1 } });
    } catch (err) {
      toast.error(goisoErrorMessage(err));
    }
  };

  const onDelete = async (b) => {
    if (!window.confirm(`Xoá hẳn chi nhánh "${b.name}" và toàn bộ dữ liệu hàng đợi? Không thể hoàn tác.`))
      return;
    try {
      await remove.mutateAsync(b.code);
      toast.success("Đã xoá");
    } catch (err) {
      toast.error(goisoErrorMessage(err));
    }
  };

  const onRegen = async (b, field) => {
    const fn = field === "api_key" ? regenKey : regenDisplayToken;
    try {
      const r = await fn.mutateAsync(b.code);
      await navigator.clipboard?.writeText(r.value).catch(() => {});
      toast.success(`Đã tạo khoá mới (đã sao chép): ${r.value}`);
    } catch (err) {
      toast.error(goisoErrorMessage(err));
    }
  };

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const columns = [
    { key: "name", header: "Chi nhánh", render: (b) => (
        <div>
          <div className="font-medium text-ink">{b.name}</div>
          <div className="text-xs text-muted">{b.full_name}</div>
        </div>
      ) },
    { key: "code", header: "Mã (URL)", render: (b) => <span className="mono">/b/{b.code}</span> },
    { key: "address", header: "Địa chỉ" },
    { key: "active", header: "Trạng thái", render: (b) => (
        <button onClick={() => toggleActive(b)}>
          <Badge className={b.active ? "badge-ok" : "badge-neutral"}>
            {b.active ? "Đang hoạt động" : "Tạm ngừng"}
          </Badge>
        </button>
      ) },
    { key: "actions", header: "", align: "right", render: (b) => (
        <div className="flex justify-end gap-1.5">
          <Link to={`/admin/goiso/branches/${b.code}`} className="btn btn-secondary px-2.5 py-1 text-xs">
            <IconOrg size={13} /> Cấu hình
          </Link>
          <Button variant="secondary" className="px-2.5 py-1 text-xs" onClick={() => openEdit(b)}>
            Sửa
          </Button>
          <Button variant="secondary" className="px-2.5 py-1 text-xs" onClick={() => onRegen(b, "api_key")}
            title="Tạo lại khoá kiosk (X-Branch-Key)">
            <IconKey size={13} /> Khoá kiosk
          </Button>
          <Button variant="danger" className="px-2.5 py-1 text-xs" onClick={() => onDelete(b)}>
            Xoá
          </Button>
        </div>
      ) },
  ];

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-muted">{branches.length} chi nhánh</p>
        <Button onClick={openCreate}>
          <IconPlus size={15} /> Thêm chi nhánh
        </Button>
      </div>
      {!branches.length ? (
        <EmptyState title="Chưa có chi nhánh nào" action={<Button onClick={openCreate}>Thêm chi nhánh</Button>} />
      ) : (
        <div className="card p-0">
          <Table columns={columns} rows={branches} rowKey="code" />
        </div>
      )}

      <Modal
        open={!!modal}
        onClose={() => setModal(null)}
        title={modal?.mode === "create" ? "Thêm chi nhánh" : `Sửa chi nhánh — ${modal?.branch?.name}`}
        footer={
          <>
            <Button variant="secondary" onClick={() => setModal(null)}>Huỷ</Button>
            <Button onClick={onSubmit}>{modal?.mode === "create" ? "Tạo" : "Lưu"}</Button>
          </>
        }
      >
        <form onSubmit={onSubmit} className="space-y-4">
          {modal?.mode === "create" && (
            <FormField label="Mã chi nhánh (dùng trong URL /b/<mã>)" required hint="chữ thường, số, gạch ngang">
              <TextInput value={form.code} onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))} required />
            </FormField>
          )}
          <FormField label="Tên ngắn" required>
            <TextInput value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
          </FormField>
          <FormField label="Tên đầy đủ" required>
            <TextInput value={form.full_name} onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} required />
          </FormField>
          <FormField label="Địa chỉ">
            <TextInput value={form.address} onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))} />
          </FormField>
          {formErr && <p className="text-sm text-danger">{formErr}</p>}
        </form>
      </Modal>
    </div>
  );
}
