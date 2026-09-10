import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import toast from "react-hot-toast";
import { usePositions, usePositionMutations, usePositionLimits, usePositionLimitMutations } from "../../hooks/usePositions";
import { useUnits } from "../../hooks/useUnits";
import { useCan } from "../../components/Can";
import { PERMISSIONS } from "../../lib/constants";
import { positionSchema } from "../../schemas";
import { apiErrorMessage } from "../../lib/api";
import { PageHeader, Button, Badge, Card, FormField, Select, TextInput, Textarea } from "../../components/ui/primitives";
import { Table } from "../../components/ui/Table";
import { LoadingState, ErrorState, EmptyState } from "../../components/ui/DataStates";
import { Modal, ConfirmDialog } from "../../components/ui/Modal";

function LimitsPanel({ canManage }) {
  const { data: units } = useUnits();
  const { data: positions } = usePositions();
  const [unitId, setUnitId] = useState("");
  const { data: limits, isLoading } = usePositionLimits(unitId);
  const { create, update } = usePositionLimitMutations(unitId);
  const [form, setForm] = useState({ position_id: "", max_holders: "" });

  const add = async () => {
    try {
      await create.mutateAsync({
        position_id: Number(form.position_id),
        max_holders: form.max_holders === "" ? null : Number(form.max_holders),
      });
      toast.success("Đã thêm giới hạn chức vụ");
      setForm({ position_id: "", max_holders: "" });
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <Card>
      <h3 className="mb-3 font-semibold text-slate-800">Giới hạn chức vụ theo đơn vị</h3>
      <FormField label="Chọn đơn vị">
        <Select value={unitId} onChange={(e) => setUnitId(e.target.value)}>
          <option value="">-- Chọn đơn vị --</option>
          {units?.map((u) => (
            <option key={u.id} value={u.id}>
              {u.code} – {u.name}
            </option>
          ))}
        </Select>
      </FormField>

      {unitId && (
        <div className="mt-4">
          {isLoading ? (
            <LoadingState />
          ) : !limits?.length ? (
            <EmptyState title="Chưa cấu hình giới hạn cho đơn vị này" />
          ) : (
            <ul className="divide-y divide-slate-100 text-sm">
              {limits.map((l) => (
                <li key={l.id} className="flex items-center justify-between py-2">
                  <span>{l.position?.name}</span>
                  <span className="flex items-center gap-2">
                    <Badge>
                      {l.max_holders == null ? "Không giới hạn" : `Tối đa ${l.max_holders}`}
                    </Badge>
                    {canManage && (
                      <input
                        type="number"
                        min="1"
                        defaultValue={l.max_holders ?? ""}
                        className="input w-24 py-1"
                        placeholder="∞"
                        onBlur={async (e) => {
                          const v = e.target.value === "" ? null : Number(e.target.value);
                          try {
                            await update.mutateAsync({ id: l.id, body: { max_holders: v } });
                            toast.success("Đã cập nhật giới hạn");
                          } catch (err) {
                            toast.error(apiErrorMessage(err));
                          }
                        }}
                      />
                    )}
                  </span>
                </li>
              ))}
            </ul>
          )}

          {canManage && (
            <div className="mt-4 flex flex-wrap items-end gap-2">
              <FormField label="Chức vụ">
                <Select
                  value={form.position_id}
                  onChange={(e) => setForm((f) => ({ ...f, position_id: e.target.value }))}
                >
                  <option value="">-- Chọn --</option>
                  {positions?.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Số lượng tối đa (bỏ trống = ∞)">
                <TextInput
                  type="number"
                  min="1"
                  value={form.max_holders}
                  onChange={(e) => setForm((f) => ({ ...f, max_holders: e.target.value }))}
                />
              </FormField>
              <Button onClick={add} disabled={!form.position_id || create.isPending}>
                Thêm
              </Button>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

export default function PositionsPage() {
  const { can } = useCan();
  const canManage = can(PERMISSIONS.POSITION_MANAGE);
  const { data, isLoading, isError, error, refetch } = usePositions();
  const { create, update, remove } = usePositionMutations();
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({ resolver: zodResolver(positionSchema) });

  const openCreate = () => {
    reset({ code: "", name: "", level: 0, description: "", is_managerial: false, is_active: true });
    setEditing("new");
  };
  const openEdit = (p) => {
    reset({ ...p, description: p.description || "" });
    setEditing(p);
  };

  const onSubmit = async (values) => {
    try {
      if (editing === "new") {
        await create.mutateAsync(values);
        toast.success("Tạo chức vụ thành công");
      } else {
        await update.mutateAsync({ id: editing.id, body: values });
        toast.success("Cập nhật chức vụ thành công");
      }
      setEditing(null);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const onDelete = async () => {
    try {
      const response = await remove.mutateAsync(deleting.id);
      const hardDeleted = response.data.data?.hard_deleted;
      toast.success(
        hardDeleted
          ? "Đã xóa chức vụ"
          : "Chức vụ đã phát sinh lịch sử nên được chuyển sang ngừng hoạt động"
      );
      setDeleting(null);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const columns = [
    { key: "code", header: "Mã" },
    { key: "name", header: "Tên chức vụ" },
    { key: "level", header: "Cấp bậc" },
    {
      key: "is_managerial",
      header: "Quản lý",
      render: (r) => (r.is_managerial ? "Có" : "Không"),
    },
    {
      key: "is_active",
      header: "Trạng thái",
      render: (r) =>
        r.is_active ? (
          <Badge className="bg-green-100 text-green-700">Hoạt động</Badge>
        ) : (
          <Badge className="bg-slate-100 text-slate-500">Ngừng</Badge>
        ),
    },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (r) =>
        canManage && (
          <div className="flex justify-end gap-1">
            <Button variant="ghost" className="px-2 py-1 text-xs" onClick={() => openEdit(r)}>
              Sửa
            </Button>
            <Button
              variant="ghost"
              className="px-2 py-1 text-xs text-red-600"
              onClick={() => setDeleting(r)}
            >
              Xóa
            </Button>
          </div>
        ),
    },
  ];

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <PageHeader
          title="Danh mục chức vụ"
          actions={canManage && <Button onClick={openCreate}>+ Thêm chức vụ</Button>}
        />
        <Card className="overflow-hidden p-0">
          {isLoading ? (
            <LoadingState />
          ) : isError ? (
            <ErrorState error={error} onRetry={refetch} />
          ) : (
            <Table columns={columns} rows={data} empty={<EmptyState title="Chưa có chức vụ" />} />
          )}
        </Card>
      </div>

      <div>
        <PageHeader title="Giới hạn chức vụ" />
        <LimitsPanel canManage={canManage} />
      </div>

      <Modal
        open={!!editing}
        onClose={() => setEditing(null)}
        title={editing === "new" ? "Thêm chức vụ" : "Sửa chức vụ"}
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
            <FormField label="Mã" required error={errors.code?.message}>
              <TextInput {...register("code")} error={errors.code} />
            </FormField>
            <FormField label="Cấp bậc" error={errors.level?.message}>
              <TextInput type="number" {...register("level")} />
            </FormField>
          </div>
          <FormField label="Tên chức vụ" required error={errors.name?.message}>
            <TextInput {...register("name")} error={errors.name} />
          </FormField>
          <FormField label="Mô tả" error={errors.description?.message}>
            <Textarea {...register("description")} />
          </FormField>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" {...register("is_managerial")} /> Là chức vụ quản lý
          </label>
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
        title="Xóa / ngừng hoạt động chức vụ"
        message={`Nếu chức vụ "${deleting?.name}" đã phát sinh lịch sử công tác, hệ thống sẽ ngừng hoạt động chức vụ thay vì xóa dữ liệu.`}
        confirmText="Tiếp tục"
      />
    </div>
  );
}
