import { useState } from "react";
import toast from "react-hot-toast";
import { useRoles, usePermissions, useRoleMutations } from "../../hooks/useRoles";
import { useCan } from "../../components/Can";
import { PERMISSIONS } from "../../lib/constants";
import { apiErrorMessage } from "../../lib/api";
import { PageHeader, Button, Badge, Card, FormField, TextInput } from "../../components/ui/primitives";
import { LoadingState, ErrorState } from "../../components/ui/DataStates";
import { Modal, ConfirmDialog } from "../../components/ui/Modal";

function RoleEditor({ role, permissions, onClose }) {
  const { create, update } = useRoleMutations();
  const isNew = role === "new";
  const [form, setForm] = useState(
    isNew
      ? { code: "", name: "", description: "", permissions: [] }
      : { ...role, permissions: role.permissions || [] }
  );
  const locked = !isNew && role.code === "SYSTEM_ADMIN";

  const toggle = (code) =>
    setForm((f) => ({
      ...f,
      permissions: f.permissions.includes(code)
        ? f.permissions.filter((c) => c !== code)
        : [...f.permissions, code],
    }));

  const save = async () => {
    try {
      if (isNew) {
        await create.mutateAsync(form);
        toast.success("Tạo vai trò thành công");
      } else {
        await update.mutateAsync({
          id: role.id,
          body: { name: form.name, description: form.description, permissions: form.permissions },
        });
        toast.success("Cập nhật vai trò thành công");
      }
      onClose();
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <Modal
      open
      onClose={onClose}
      size="lg"
      title={isNew ? "Thêm vai trò" : `Vai trò: ${role.name}`}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Hủy
          </Button>
          <Button onClick={save} disabled={locked || create.isPending || update.isPending}>
            Lưu
          </Button>
        </>
      }
    >
      {locked && (
        <p className="mb-3 rounded bg-amber-50 px-3 py-2 text-xs text-amber-700">
          Vai trò Quản trị hệ thống được bảo vệ, không thể chỉnh sửa quyền.
        </p>
      )}
      <div className="grid gap-3">
        {isNew && (
          <FormField label="Mã vai trò" required>
            <TextInput value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          </FormField>
        )}
        <FormField label="Tên vai trò" required>
          <TextInput
            value={form.name}
            disabled={locked}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </FormField>
        <FormField label="Mô tả">
          <TextInput
            value={form.description || ""}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </FormField>
        <div>
          <p className="label">Quyền ({form.permissions.length})</p>
          <div className="grid max-h-64 grid-cols-1 gap-1 overflow-y-auto rounded-lg border border-slate-200 p-2 sm:grid-cols-2">
            {permissions?.map((p) => (
              <label key={p.code} className="flex items-start gap-2 rounded px-2 py-1 text-sm hover:bg-slate-50">
                <input
                  type="checkbox"
                  disabled={locked}
                  checked={form.permissions.includes(p.code)}
                  onChange={() => toggle(p.code)}
                />
                <span>
                  <span className="font-mono text-xs text-slate-700">{p.code}</span>
                  <span className="block text-xs text-slate-400">{p.description}</span>
                </span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
}

export default function RolesPage() {
  const { can } = useCan();
  const canManage = can(PERMISSIONS.ROLE_MANAGE);
  const { data: roles, isLoading, isError, error, refetch } = useRoles();
  const { data: permissions } = usePermissions();
  const { remove } = useRoleMutations();
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const onDelete = async () => {
    try {
      await remove.mutateAsync(deleting.id);
      toast.success("Đã xóa vai trò");
      setDeleting(null);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <div>
      <PageHeader
        title="Vai trò & quyền"
        actions={canManage && <Button onClick={() => setEditing("new")}>+ Thêm vai trò</Button>}
      />
      <div className="grid gap-4 md:grid-cols-2">
        {roles.map((r) => (
          <Card key={r.id}>
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold text-slate-800">{r.name}</h3>
                <p className="font-mono text-xs text-slate-400">{r.code}</p>
              </div>
              {r.is_system && <Badge className="bg-slate-100 text-slate-500">Hệ thống</Badge>}
            </div>
            <p className="mt-1 text-sm text-slate-500">{r.description}</p>
            <p className="mt-2 text-xs text-slate-400">{r.permissions.length} quyền</p>
            {canManage && (
              <div className="mt-3 flex gap-2">
                <Button variant="secondary" className="text-xs" onClick={() => setEditing(r)}>
                  Chỉnh sửa
                </Button>
                {!r.is_system && (
                  <Button
                    variant="ghost"
                    className="text-xs text-red-600"
                    onClick={() => setDeleting(r)}
                  >
                    Xóa
                  </Button>
                )}
              </div>
            )}
          </Card>
        ))}
      </div>

      {editing && (
        <RoleEditor role={editing} permissions={permissions} onClose={() => setEditing(null)} />
      )}
      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={onDelete}
        loading={remove.isPending}
        title="Xóa vai trò"
        message={`Xóa vai trò "${deleting?.name}"? Không thể xóa nếu đang được gán cho tài khoản.`}
        confirmText="Xóa"
      />
    </div>
  );
}
