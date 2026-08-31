import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { employeeCreateSchema, employeeSchema } from "../../schemas";
import { useUnits } from "../../hooks/useUnits";
import { usePositions } from "../../hooks/usePositions";
import {
  EMPLOYEE_STATUS_LABELS,
  EMPLOYMENT_TYPE_LABELS,
  GENDER_LABELS,
} from "../../lib/constants";
import { Button, FormField, Select, TextInput, Textarea } from "../ui/primitives";

export function EmployeeForm({ mode, defaultValues, onSubmit, submitting }) {
  const isCreate = mode === "create";
  const { data: units } = useUnits({ only_active: true });
  const { data: positions } = usePositions({ only_active: true });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(isCreate ? employeeCreateSchema : employeeSchema),
    defaultValues,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <section className="card p-5">
        <h3 className="mb-4 font-semibold text-slate-800">Thông tin cơ bản</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <FormField label="Mã nhân sự" required error={errors.employee_code?.message}>
            <TextInput {...register("employee_code")} error={errors.employee_code} />
          </FormField>
          <FormField label="Họ và tên" required error={errors.full_name?.message}>
            <TextInput {...register("full_name")} error={errors.full_name} />
          </FormField>
          <FormField label="Ngày sinh" error={errors.date_of_birth?.message}>
            <TextInput type="date" {...register("date_of_birth")} />
          </FormField>
          <FormField label="Giới tính" error={errors.gender?.message}>
            <Select {...register("gender")}>
              <option value="">-- Chọn --</option>
              {Object.entries(GENDER_LABELS).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Số CCCD" error={errors.identity_number?.message} hint="Trường nhạy cảm">
            <TextInput {...register("identity_number")} />
          </FormField>
          <FormField label="Số điện thoại" error={errors.phone?.message}>
            <TextInput {...register("phone")} error={errors.phone} />
          </FormField>
          <FormField label="Email" error={errors.email?.message}>
            <TextInput {...register("email")} error={errors.email} />
          </FormField>
          <FormField label="Địa chỉ" error={errors.address?.message}>
            <TextInput {...register("address")} />
          </FormField>
        </div>
      </section>

      <section className="card p-5">
        <h3 className="mb-4 font-semibold text-slate-800">Thông tin công tác</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <FormField label="Chức danh chuyên môn" error={errors.professional_title?.message}>
            <TextInput {...register("professional_title")} />
          </FormField>
          <FormField label="Loại nhân sự" error={errors.employment_type?.message}>
            <Select {...register("employment_type")}>
              <option value="">-- Chọn --</option>
              {Object.entries(EMPLOYMENT_TYPE_LABELS).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField
            label={isCreate ? "Ngày tuyển dụng" : "Ngày tuyển dụng"}
            required={isCreate}
            error={errors.recruitment_date?.message}
          >
            <TextInput type="date" {...register("recruitment_date")} error={errors.recruitment_date} />
          </FormField>
          {!isCreate && (
            <FormField label="Trạng thái" error={errors.status?.message}>
              <Select {...register("status")}>
                {Object.entries(EMPLOYEE_STATUS_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </Select>
            </FormField>
          )}

          {isCreate && (
            <>
              <FormField label="Đơn vị công tác" required error={errors.unit_id?.message}>
                <Select {...register("unit_id")} error={errors.unit_id}>
                  <option value="">-- Chọn đơn vị --</option>
                  {units?.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.code} – {u.name}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Chức vụ" required error={errors.position_id?.message}>
                <Select {...register("position_id")} error={errors.position_id}>
                  <option value="">-- Chọn chức vụ --</option>
                  {positions?.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Số quyết định" error={errors.decision_number?.message}>
                <TextInput {...register("decision_number")} />
              </FormField>
              <FormField label="Ngày quyết định" error={errors.decision_date?.message}>
                <TextInput type="date" {...register("decision_date")} />
              </FormField>
            </>
          )}
        </div>
        <div className="mt-4">
          <FormField label="Ghi chú" error={errors.notes?.message}>
            <Textarea {...register("notes")} />
          </FormField>
        </div>
      </section>

      <div className="flex justify-end gap-2">
        <Button type="submit" disabled={submitting}>
          {submitting ? "Đang lưu..." : isCreate ? "Thêm nhân sự" : "Lưu thay đổi"}
        </Button>
      </div>
    </form>
  );
}
