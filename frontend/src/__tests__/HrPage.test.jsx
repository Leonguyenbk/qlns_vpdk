import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import HrPage, { LegacyEmployeeRedirect } from "../pages/hr/HrPage";
import { renderWithProviders } from "./testUtils";

function Tree() {
  return (
    <Routes>
      <Route path="/nhan-su" element={<HrPage />}>
        <Route index element={<div>Nội dung tổng quan</div>} />
        <Route path="nhan-vien" element={<div>Nội dung danh sách</div>} />
        <Route path="nhan-vien/:id" element={<div>Nội dung hồ sơ</div>} />
        <Route path="co-cau" element={<div>Nội dung cơ cấu</div>} />
        <Route path="chuc-vu" element={<div>Nội dung chức vụ</div>} />
      </Route>
      <Route path="employees/*" element={<LegacyEmployeeRedirect />} />
    </Routes>
  );
}

const ALL = ["employee.view", "unit.view", "position.view"];

describe("HrPage", () => {
  it("hiện đủ 4 tab và nội dung tổng quan ở trang gốc khi có đủ quyền", () => {
    renderWithProviders(<Tree />, { route: "/nhan-su", authValue: { isAuthenticated: true, permissions: ALL } });
    for (const label of ["Tổng quan nhân sự", "Danh sách nhân sự", "Cơ cấu đơn vị", "Chức vụ"]) {
      expect(screen.getByRole("link", { name: label })).toBeInTheDocument();
    }
    expect(screen.getByText("Nội dung tổng quan")).toBeInTheDocument();
  });

  it("chỉ hiện tab mà tài khoản có quyền", () => {
    renderWithProviders(<Tree />, {
      route: "/nhan-su/co-cau",
      authValue: { isAuthenticated: true, permissions: ["unit.view"] },
    });
    expect(screen.getByRole("link", { name: "Cơ cấu đơn vị" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Danh sách nhân sự" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Chức vụ" })).toBeNull();
  });

  it("tab Danh sách vẫn sáng khi đang xem hồ sơ, tab Tổng quan thì không", () => {
    renderWithProviders(<Tree />, {
      route: "/nhan-su/nhan-vien/12",
      authValue: { isAuthenticated: true, permissions: ALL },
    });
    expect(screen.getByRole("link", { name: "Danh sách nhân sự" }).className).toContain("border-[color:var(--color-accent)]");
    expect(screen.getByRole("link", { name: "Tổng quan nhân sự" }).className).not.toContain("border-[color:var(--color-accent)]");
  });

  it("chuyển link cũ /employees/12 sang /nhan-su/nhan-vien/12", () => {
    renderWithProviders(<Tree />, {
      route: "/employees/12",
      authValue: { isAuthenticated: true, permissions: ALL },
    });
    expect(screen.getByText("Nội dung hồ sơ")).toBeInTheDocument();
  });
});
