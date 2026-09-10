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
import { UnitPicker } from "../units/UnitPicker";

export function EmployeeForm({ mode, defaultValues, onSubmit, submitting }) {
  const isCreate = mode === "create";
  const { data: units } = useUnits({ only_active: true });
  const { data: positions } = usePositions({ only_active: true });

  const {
    register,
    handleSubmit,
    setValue,
    watch,
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

          <div className="md:col-span-2">
            <FormField label="Đơn vị công tác" required={isCreate} error={errors.unit_id?.message}>
              <input type="hidden" {...register("unit_id")} />
              <UnitPicker
                units={units || []}
                value={watch("unit_id")}
                error={errors.unit_id ? " " : undefined}
                onChange={(id) => setValue("unit_id", id, { shouldValidate: true })}
              />
            </FormField>
          </div>
          <FormField label="Chức vụ / chức danh" required={isCreate} error={errors.position_id?.message}>
            <Select {...register("position_id")} error={errors.position_id}>
              <option value="">-- Chọn chức vụ --</option>
              {positions?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </Select>
          </FormField>
          {isCreate && (
            <>
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

      <section className="card p-5">
        <h3 className="mb-4 font-semibold text-slate-800">Hồ sơ mở rộng</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <FormField label="Quê quán" error={errors.place_of_origin?.message}>
            <TextInput {...register("place_of_origin")} />
          </FormField>
          <FormField label="Nơi cấp CCCD" error={errors.identity_issued_place?.message}>
            <TextInput {...register("identity_issued_place")} />
          </FormField>
          <FormField label="Ngày cấp CCCD" error={errors.identity_issued_date?.message}>
            <TextInput type="date" {...register("identity_issued_date")} />
          </FormField>
          <FormField label="Ngày vào biên chế" error={errors.tenure_date?.message}>
            <TextInput type="date" {...register("tenure_date")} />
          </FormField>
          <FormField label="Loại hợp đồng" error={errors.contract_type?.message}>
            <TextInput {...register("contract_type")} />
          </FormField>
          <FormField label="Ngạch / CDNN" error={errors.job_grade_code?.message}>
            <TextInput {...register("job_grade_code")} />
          </FormField>
          <FormField label="Trình độ" error={errors.education_level?.message}>
            <TextInput {...register("education_level")} />
          </FormField>
          <FormField label="Ngành đào tạo" error={errors.education_major?.message}>
            <TextInput {...register("education_major")} />
          </FormField>
          <FormField label="Hệ đào tạo" error={errors.education_mode?.message}>
            <TextInput {...register("education_mode")} />
          </FormField>
          <FormField label="Chứng chỉ ngoại ngữ" error={errors.foreign_language_cert?.message}>
            <TextInput {...register("foreign_language_cert")} />
          </FormField>
          <FormField label="Chứng chỉ tin học" error={errors.it_cert?.message}>
            <TextInput {...register("it_cert")} />
          </FormField>
        </div>
        <div className="mt-4">
          <FormField label="Nhiệm vụ đang đảm nhận" error={errors.job_duties?.message}>
            <Textarea {...register("job_duties")} />
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
