import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { Can } from "../components/Can";
import { renderWithProviders } from "./testUtils";

describe("Can – ẩn/hiện nút theo quyền", () => {
  it("ẩn nút khi không có quyền", () => {
    renderWithProviders(
      <Can permission="employee.create">
        <button>Thêm nhân sự</button>
      </Can>,
      { authValue: { isAuthenticated: true, permissions: ["employee.view"] } }
    );
    expect(screen.queryByText("Thêm nhân sự")).not.toBeInTheDocument();
  });

  it("hiện nút khi có quyền", () => {
    renderWithProviders(
      <Can permission="employee.create">
        <button>Thêm nhân sự</button>
      </Can>,
      { authValue: { isAuthenticated: true, permissions: ["employee.create"] } }
    );
    expect(screen.getByText("Thêm nhân sự")).toBeInTheDocument();
  });

  it("hiển thị fallback khi không đủ quyền anyOf", () => {
    renderWithProviders(
      <Can anyOf={["role.manage", "user.manage"]} fallback={<span>Bị khóa</span>}>
        <button>Quản trị</button>
      </Can>,
      { authValue: { isAuthenticated: true, permissions: ["employee.view"] } }
    );
    expect(screen.getByText("Bị khóa")).toBeInTheDocument();
    expect(screen.queryByText("Quản trị")).not.toBeInTheDocument();
  });
});
