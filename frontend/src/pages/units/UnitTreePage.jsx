import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import toast from "react-hot-toast";
import { useUnitTree, useUnits, useUnitMutations } from "../../hooks/useUnits";
import { useCan } from "../../components/Can";
import { PERMISSIONS, UNIT_TYPE_LABELS } from "../../lib/constants";
import { unitSchema } from "../../schemas";
import { apiErrorMessage } from "../../lib/api";
import { PageHeader, Button, Badge, Card, FormField, Select, TextInput } from "../../components/ui/primitives";
import { LoadingState, ErrorState } from "../../components/ui/DataStates";
import { Modal, ConfirmDialog } from "../../components/ui/Modal";

function TreeNode({ node, depth, onEdit, onDelete, canManage }) {
  const [open, setOpen] = useState(depth < 1);
  const hasChildren = node.children?.length > 0;
  return (
    <li>
      <div
        className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-slate-50"
        style={{ paddingLeft: depth * 18 + 8 }}
      >
        {hasChildren ? (
          <button className="w-5 text-slate-400" onClick={() => setOpen((o) => !o)}>
            {open ? "▾" : "▸"}
          </button>
        ) : (
          <span className="w-5" />
        )}
        <span className="font-medium text-slate-800">{node.name}</span>
        <span className="text-xs text-slate-400">{node.code}</span>
        <Badge className="bg-brand-50 text-brand-700">{UNIT_TYPE_LABELS[node.unit_type]}</Badge>
        {!node.is_active && <Badge className="bg-slate-100 text-slate-500">Ngừng hoạt động</Badge>}
        {canManage && (
          <span className="ml-auto flex gap-1">
            <Button variant="ghost" className="px-2 py-0.5 text-xs" onClick={() => onEdit(node)}>
              Sửa
            </Button>
            <Button
              variant="ghost"
              className="px-2 py-0.5 text-xs text-red-600"
              onClick={() => onDelete(node)}
            >
              Xóa
            </Button>
          </span>
        )}
      </div>
      {open && hasChildren && (
        <ul>
          {node.children.map((c) => (
            <TreeNode
              key={c.id}
              node={c}
              depth={depth + 1}
              onEdit={onEdit}
              onDelete={onDelete}
              canManage={canManage}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

export default function UnitTreePage() {
  const { can } = useCan();
  const canManage = can(PERMISSIONS.UNIT_MANAGE);
  const { data: tree, isLoading, isError, error, refetch } = useUnitTree();
  const { data: flat } = useUnits();
  const { create, update, remove } = useUnitMutations();
  const [editing, setEditing] = useState(null); // node | "new" | null
  const [deleting, setDeleting] = useState(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({ resolver: zodResolver(unitSchema) });

  const openCreate = () => {
    reset({ code: "", name: "", unit_type: "BRANCH", parent_id: "", address: "", phone: "", email: "", is_active: true });
    setEditing("new");
  };
  const openEdit = (node) => {
    reset({
      code: node.code,
      name: node.name,
      unit_type: node.unit_type,
      parent_id: node.parent_id || "",
      address: node.address || "",
      phone: node.phone || "",
      email: node.email || "",
      is_active: node.is_active,
    });
    setEditing(node);
  };

  const onSubmit = async (values) => {
    const body = { ...values, parent_id: values.parent_id ? Number(values.parent_id) : null };
    try {
      if (editing === "new") {
        await create.mutateAsync(body);
        toast.success("Tạo đơn vị thành công");
      } else {
        await update.mutateAsync({ id: editing.id, body });
        toast.success("Cập nhật đơn vị thành công");
      }
      setEditing(null);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const onDelete = async () => {
    try {
      const res = await remove.mutateAsync(deleting.id);
      toast.success(res.data.message || "Đã xử lý");
      setDeleting(null);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const parentOptions = useMemo(() => flat || [], [flat]);

  return (
    <div>
      <PageHeader
        title="Cơ cấu đơn vị"
        subtitle="Sơ đồ tổ chức dạng cây"
        actions={canManage && <Button onClick={openCreate}>+ Thêm đơn vị</Button>}
      />
      <Card className="p-3">
        {isLoading ? (
          <LoadingState />
        ) : isError ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : (
          <ul>
            {tree.map((n) => (
              <TreeNode
                key={n.id}
                node={n}
                depth={0}
                onEdit={openEdit}
                onDelete={setDeleting}
                canManage={canManage}
              />
            ))}
          </ul>
        )}
      </Card>

      <Modal
        open={!!editing}
        onClose={() => setEditing(null)}
        title={editing === "new" ? "Thêm đơn vị" : "Sửa đơn vị"}
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditing(null)}>
              Hủy
            </Button>
            <Button onClick={handleSubmit(onSubmit)} disabled={create.isPending || update.isPending}>
              Lưu
            </Button>
          </>
        }
      >
        <form className="grid gap-3" onSubmit={handleSubmit(onSubmit)}>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Mã đơn vị" required error={errors.code?.message}>
              <TextInput {...register("code")} error={errors.code} />
            </FormField>
            <FormField label="Loại" required error={errors.unit_type?.message}>
              <Select {...register("unit_type")}>
                {Object.entries(UNIT_TYPE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </Select>
            </FormField>
          </div>
          <FormField label="Tên đơn vị" required error={errors.name?.message}>
            <TextInput {...register("name")} error={errors.name} />
          </FormField>
          <FormField label="Đơn vị cấp trên" error={errors.parent_id?.message}>
            <Select {...register("parent_id")}>
              <option value="">-- Không có (cấp cao nhất) --</option>
              {parentOptions
                .filter((u) => editing === "new" || u.id !== editing?.id)
                .map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.code} – {u.name}
                  </option>
                ))}
            </Select>
          </FormField>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Điện thoại" error={errors.phone?.message}>
              <TextInput {...register("phone")} error={errors.phone} />
            </FormField>
            <FormField label="Email" error={errors.email?.message}>
              <TextInput {...register("email")} error={errors.email} />
            </FormField>
          </div>
          <FormField label="Địa chỉ" error={errors.address?.message}>
            <TextInput {...register("address")} />
          </FormField>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" {...register("is_active")} /> Đang hoạt động
          </label>
        </form>
      </Modal>

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={onDelete}
        loading={remove.isPending}
        title="Xóa / ngừng hoạt động đơn vị"
        message={`Nếu "${deleting?.name}" đã phát sinh dữ liệu, hệ thống sẽ chuyển sang trạng thái ngừng hoạt động thay vì xóa.`}
        confirmText="Tiếp tục"
      />
    </div>
  );
}
