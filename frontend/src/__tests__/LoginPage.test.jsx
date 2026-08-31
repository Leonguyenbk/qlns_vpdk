import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LoginPage from "../pages/LoginPage";
import { renderWithProviders } from "./testUtils";


describe("LoginPage", () => {
  it("gửi đúng username/password khi nhập và nhấn Enter", async () => {
    const login = vi.fn().mockResolvedValue({});
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, {
      route: "/login",
      authValue: { login, loading: false, isAuthenticated: false },
    });

    await user.type(screen.getByLabelText("Tên đăng nhập *"), "admin");
    await user.type(screen.getByLabelText("Mật khẩu *"), "Secret@123{Enter}");

    expect(login).toHaveBeenCalledWith("admin", "Secret@123");
    expect(screen.queryByText("Vui lòng nhập tên đăng nhập")).not.toBeInTheDocument();
    expect(screen.queryByText("Vui lòng nhập mật khẩu")).not.toBeInTheDocument();
  });
});
