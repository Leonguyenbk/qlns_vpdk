import { describe, it, expect } from "vitest";
import { employeeCreateSchema, transferSchema, loginSchema } from "../schemas";

describe("Kiểm tra dữ liệu biểu mẫu (zod)", () => {
  it("login: bắt buộc nhập username/password", () => {
    const r = loginSchema.safeParse({ username: "", password: "" });
    expect(r.success).toBe(false);
  });

  it("employeeCreate: thiếu đơn vị/chức vụ -> lỗi", () => {
    const r = employeeCreateSchema.safeParse({
      employee_code: "NV01",
      full_name: "Nguyễn Văn A",
      recruitment_date: "2024-01-01",
    });
    expect(r.success).toBe(false);
    const fields = r.error.issues.map((i) => i.path[0]);
    expect(fields).toContain("unit_id");
    expect(fields).toContain("position_id");
  });

  it("employeeCreate: email sai định dạng -> lỗi", () => {
    const r = employeeCreateSchema.safeParse({
      employee_code: "NV01",
      full_name: "Nguyễn Văn A",
      recruitment_date: "2024-01-01",
      unit_id: 1,
      position_id: 2,
      email: "khong-hop-le",
    });
    expect(r.success).toBe(false);
    expect(r.error.issues.some((i) => i.path[0] === "email")).toBe(true);
  });

  it("employeeCreate: dữ liệu hợp lệ -> pass và ép kiểu số", () => {
    const r = employeeCreateSchema.safeParse({
      employee_code: "NV01",
      full_name: "Nguyễn Văn A",
      recruitment_date: "2024-01-01",
      unit_id: "3",
      position_id: "5",
      email: "",
    });
    expect(r.success).toBe(true);
    expect(r.data.unit_id).toBe(3);
    expect(r.data.position_id).toBe(5);
  });

  it("transfer: thiếu ngày hiệu lực -> lỗi", () => {
    const r = transferSchema.safeParse({ to_unit_id: 1, to_position_id: 2, effective_date: "" });
    expect(r.success).toBe(false);
    expect(r.error.issues.some((i) => i.path[0] === "effective_date")).toBe(true);
  });
});
