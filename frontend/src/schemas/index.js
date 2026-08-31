import { z } from "zod";

const phoneRe = /^[0-9+()\-\s]{8,20}$/;

export const loginSchema = z.object({
  username: z.string().min(1, "Vui lòng nhập tên đăng nhập"),
  password: z.string().min(1, "Vui lòng nhập mật khẩu"),
});

export const changePasswordSchema = z
  .object({
    old_password: z.string().min(1, "Nhập mật khẩu hiện tại"),
    new_password: z.string().min(8, "Mật khẩu mới tối thiểu 8 ký tự"),
    confirm: z.string(),
  })
  .refine((d) => d.new_password === d.confirm, {
    path: ["confirm"],
    message: "Xác nhận mật khẩu không khớp",
  });

const optionalEmail = z
  .string()
  .trim()
  .email("Email không hợp lệ")
  .optional()
  .or(z.literal(""));

const optionalPhone = z
  .string()
  .trim()
  .regex(phoneRe, "Số điện thoại không hợp lệ")
  .optional()
  .or(z.literal(""));

export const employeeSchema = z.object({
  employee_code: z.string().trim().min(1, "Mã nhân sự là bắt buộc"),
  full_name: z.string().trim().min(2, "Họ tên tối thiểu 2 ký tự"),
  date_of_birth: z.string().optional().or(z.literal("")),
  gender: z.enum(["MALE", "FEMALE", "OTHER"]).optional().or(z.literal("")),
  identity_number: z.string().trim().optional().or(z.literal("")),
  phone: optionalPhone,
  email: optionalEmail,
  address: z.string().trim().optional().or(z.literal("")),
  professional_title: z.string().trim().optional().or(z.literal("")),
  employment_type: z
    .enum(["OFFICIAL", "CONTRACT", "PROBATION", "COLLABORATOR", "SECONDED"])
    .optional()
    .or(z.literal("")),
  recruitment_date: z.string().optional().or(z.literal("")),
  status: z
    .enum(["WORKING", "ON_LEAVE", "RETIRED", "RESIGNED", "TRANSFERRED", "INACTIVE"])
    .optional(),
  notes: z.string().trim().optional().or(z.literal("")),
});

export const employeeCreateSchema = employeeSchema.extend({
  unit_id: z.coerce.number({ invalid_type_error: "Chọn đơn vị" }).int().positive("Chọn đơn vị"),
  position_id: z
    .coerce.number({ invalid_type_error: "Chọn chức vụ" })
    .int()
    .positive("Chọn chức vụ"),
  recruitment_date: z.string().min(1, "Chọn ngày tuyển dụng"),
  decision_number: z.string().trim().optional().or(z.literal("")),
  decision_date: z.string().optional().or(z.literal("")),
});

export const transferSchema = z.object({
  to_unit_id: z.coerce.number().int().positive("Chọn đơn vị mới"),
  to_position_id: z.coerce.number().int().positive("Chọn chức vụ mới"),
  effective_date: z.string().min(1, "Chọn ngày hiệu lực"),
  assignment_type: z
    .enum(["TRANSFER", "APPOINTMENT", "SECONDMENT", "REASSIGNMENT"])
    .default("TRANSFER"),
  decision_number: z.string().trim().optional().or(z.literal("")),
  decision_date: z.string().optional().or(z.literal("")),
  note: z.string().trim().optional().or(z.literal("")),
});

export const unitSchema = z.object({
  code: z.string().trim().min(1, "Mã đơn vị là bắt buộc"),
  name: z.string().trim().min(1, "Tên đơn vị là bắt buộc"),
  unit_type: z.enum(["HEAD_OFFICE", "DEPARTMENT", "BRANCH", "SECTION"]),
  parent_id: z.union([z.coerce.number().int().positive(), z.literal(""), z.null()]).optional(),
  address: z.string().trim().optional().or(z.literal("")),
  phone: optionalPhone,
  email: optionalEmail,
  is_active: z.boolean().optional(),
});

export const positionSchema = z.object({
  code: z.string().trim().min(1, "Mã chức vụ là bắt buộc"),
  name: z.string().trim().min(1, "Tên chức vụ là bắt buộc"),
  level: z.coerce.number().int().min(0).default(0),
  description: z.string().trim().optional().or(z.literal("")),
  is_managerial: z.boolean().optional(),
  is_active: z.boolean().optional(),
});
