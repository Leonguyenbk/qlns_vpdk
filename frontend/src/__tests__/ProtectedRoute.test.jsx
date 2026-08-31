import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "../components/ProtectedRoute";
import { renderWithProviders } from "./testUtils";

function Tree() {
  return (
    <Routes>
      <Route path="/login" element={<div>Trang đăng nhập</div>} />
      <Route path="/403" element={<div>Không có quyền</div>} />
      <Route
        path="/secret"
        element={
          <ProtectedRoute permission="employee.view">
            <div>Nội dung bí mật</div>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

describe("ProtectedRoute", () => {
  it("chuyển hướng về /login khi chưa đăng nhập", () => {
    renderWithProviders(<Tree />, { route: "/secret", authValue: { isAuthenticated: false } });
    expect(screen.getByText("Trang đăng nhập")).toBeInTheDocument();
  });

  it("chuyển hướng về /403 khi thiếu permission", () => {
    renderWithProviders(<Tree />, {
      route: "/secret",
      authValue: { isAuthenticated: true, permissions: [] },
    });
    expect(screen.getByText("Không có quyền")).toBeInTheDocument();
  });

  it("hiển thị nội dung khi có đủ quyền", () => {
    renderWithProviders(<Tree />, {
      route: "/secret",
      authValue: { isAuthenticated: true, permissions: ["employee.view"] },
    });
    expect(screen.getByText("Nội dung bí mật")).toBeInTheDocument();
  });
});
