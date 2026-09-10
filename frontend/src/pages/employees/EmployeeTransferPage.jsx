import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { useEmployee, useEmployeeMutations } from "../../hooks/useEmployees";
import { useUnits } from "../../hooks/useUnits";
import { usePositions } from "../../hooks/usePositions";
import { transferSchema } from "../../schemas";
import { apiErrorMessage, conflictPayload } from "../../lib/api";
import { todayISO } from "../../lib/format";
import { ASSIGNMENT_TYPE_LABELS } from "../../lib/constants";
import { PageHeader, Button, Card, FormField, Select, TextInput, Textarea } from "../../components/ui/primitives";
import { LoadingState, ErrorState } from "../../components/ui/DataStates";
import { ConfirmDialog } from "../../components/ui/Modal";
import { UnitPicker } from "../../components/units/UnitPicker";

export default function EmployeeTransferPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: emp, isLoading, isError, error, refetch } = useEmployee(id);
  const { data: units } = useUnits({ only_active: true });
  const { data: positions } = usePositions({ only_active: true });
  const { transfer } = useEmployeeMutations();
  const [conflict, setConflict] = useState(null);
  const [pending, setPending] = useState(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(transferSchema),
    defaultValues: { effective_date: todayISO(), assignment_type: "TRANSFER" },
  });

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const send = async (values, replace = false) => {
    const body = { ...values };
    Object.keys(body).forEach((k) => body[k] === "" && delete body[k]);
    if (replace) body.replace_existing = true;
    try {
      await transfer.mutateAsync({ id, body });
      toast.success("Chuyển đơn vị thành công");
      navigate(`/employees/${id}`);
    } catch (err) {
      const p = conflictPayload(err);
      if (p?.conflict === "POSITION_LIMIT_REACHED") {
        setPending(values);
        setConflict(p);
        return;
      }
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Chuyển đơn vị"
        subtitle={`Nhân sự: ${emp.full_name} (${emp.employee_code})`}
        actions={<Button variant="secondary" onClick={() => navigate(-1)}>Quay lại</Button>}
      />

      <Card className="mb-4 grid gap-2 md:grid-cols-2">
        <div className="text-sm">
          <span className="text-slate-500">Đơn vị hiện tại: </span>
          <span className="font-medium">{emp.current_unit?.path || emp.current_unit?.name || "—"}</span>
        </div>
        <div className="text-sm">
          <span className="text-slate-500">Chức vụ hiện tại: </span>
          <span className="font-medium">{emp.current_position?.name || "—"}</span>
        </div>
      </Card>

      <form onSubmit={handleSubmit((v) => send(v, false))} className="card space-y-4 p-5">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <FormField label="Đơn vị mới" required error={errors.to_unit_id?.message}>
              <input type="hidden" {...register("to_unit_id")} />
              <UnitPicker
                units={units || []}
                value={watch("to_unit_id")}
                error={errors.to_unit_id ? " " : undefined}
                onChange={(id) => setValue("to_unit_id", id, { shouldValidate: true })}
              />
            </FormField>
          </div>
          <FormField label="Chức vụ mới" required error={errors.to_position_id?.message}>
            <Select {...register("to_position_id")} error={errors.to_position_id}>
              <option value="">-- Chọn chức vụ --</option>
              {positions?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Hình thức" error={errors.assignment_type?.message}>
            <Select {...register("assignment_type")}>
              {["TRANSFER", "APPOINTMENT", "SECONDMENT", "REASSIGNMENT"].map((k) => (
                <option key={k} value={k}>
                  {ASSIGNMENT_TYPE_LABELS[k]}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Ngày hiệu lực" required error={errors.effective_date?.message}>
            <TextInput type="date" {...register("effective_date")} error={errors.effective_date} />
          </FormField>
          <FormField label="Số quyết định" error={errors.decision_number?.message}>
            <TextInput {...register("decision_number")} />
          </FormField>
          <FormField label="Ngày quyết định" error={errors.decision_date?.message}>
            <TextInput type="date" {...register("decision_date")} />
          </FormField>
        </div>
        <FormField label="Ghi chú" error={errors.note?.message}>
          <Textarea {...register("note")} />
        </FormField>
        <div className="flex justify-end">
          <Button type="submit" disabled={transfer.isPending}>
            {transfer.isPending ? "Đang xử lý..." : "Thực hiện chuyển đơn vị"}
          </Button>
        </div>
      </form>

      <ConfirmDialog
        open={!!conflict}
        onClose={() => setConflict(null)}
        onConfirm={() => {
          setConflict(null);
          send(pending, true);
        }}
        loading={transfer.isPending}
        variant="primary"
        title="Chức vụ tại đơn vị mới đã đủ người"
        confirmText="Xác nhận thay thế"
        message={
          conflict
            ? `Chức vụ "${conflict.position?.name}" đã đạt giới hạn. Người đang giữ: ` +
              conflict.current_holders
                .map((h) => `${h.full_name} (${h.employee_code})`)
                .join(", ") +
              ". Xác nhận kết thúc phân công của người cũ để chuyển người này vào?"
            : ""
        }
      />
    </div>
  );
}
