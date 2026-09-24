import { describe, it, expect, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import PublicSurveyResultsPage from "../pages/public/PublicSurveyResultsPage";
import { renderWithProviders } from "./testUtils";
import * as publicSurveyHook from "../hooks/usePublicSurvey";

vi.mock("../hooks/usePublicSurvey");

describe("PublicSurveyResultsPage", () => {
  it("hiển thị skeleton khi đang tải dữ liệu", () => {
    vi.spyOn(publicSurveyHook, "usePublicSurveyResults").mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });

    renderWithProviders(<PublicSurveyResultsPage />, { route: "/ket-qua-khao-sat/test-slug" });
    expect(screen.queryByText("Bảng Xếp Hạng Chi Nhánh")).not.toBeInTheDocument();
  });

  it("hiển thị thông báo khi khảo sát chưa công khai kết quả", () => {
    vi.spyOn(publicSurveyHook, "usePublicSurveyResults").mockReturnValue({
      data: {
        title: "Khảo sát sự hài lòng 2026",
        available: false,
        unavailable_reason: "Khảo sát chưa công khai kết quả.",
        by_branch: [],
      },
      isLoading: false,
      isError: false,
    });

    renderWithProviders(<PublicSurveyResultsPage />, { route: "/ket-qua-khao-sat/test-slug" });
    expect(screen.getByText("Khảo sát sự hài lòng 2026")).toBeInTheDocument();
    expect(screen.getByText("Khảo sát chưa công khai kết quả.")).toBeInTheDocument();
    expect(screen.getByText("Tham gia làm khảo sát")).toBeInTheDocument();
  });

  it("hiển thị thông báo lỗi khi API thất bại", () => {
    vi.spyOn(publicSurveyHook, "usePublicSurveyResults").mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: { message: "Lỗi kết nối máy chủ" },
      refetch: vi.fn(),
    });

    renderWithProviders(<PublicSurveyResultsPage />, { route: "/ket-qua-khao-sat/test-slug" });
    expect(screen.getByText("Không thể tải bảng xếp hạng")).toBeInTheDocument();
    expect(screen.getByText("Lỗi kết nối máy chủ")).toBeInTheDocument();
  });

  it("hiển thị đầy đủ bảng xếp hạng, KPI, bục vinh danh và tìm kiếm chi nhánh", () => {
    const mockData = {
      title: "Đánh giá chất lượng phục vụ Quý 3",
      slug: "quy-3-2026",
      status: "active",
      available: true,
      max_possible_score: 100,
      total_responses: 450,
      by_branch: [
        {
          branch_id: 1,
          branch_name: "Chi nhánh Quận 1",
          rank: 1,
          average_total_score: 96.5,
          average_percentage: 96.5,
          total_responses: 180,
        },
        {
          branch_id: 2,
          branch_name: "Chi nhánh Quận 3",
          rank: 2,
          average_total_score: 92.0,
          average_percentage: 92.0,
          total_responses: 150,
        },
        {
          branch_id: 3,
          branch_name: "Chi nhánh Bình Thạnh",
          rank: 3,
          average_total_score: 88.5,
          average_percentage: 88.5,
          total_responses: 120,
        },
      ],
    };

    vi.spyOn(publicSurveyHook, "usePublicSurveyResults").mockReturnValue({
      data: mockData,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
      isFetching: false,
    });

    renderWithProviders(<PublicSurveyResultsPage />, { route: "/ket-qua-khao-sat/quy-3-2026" });

    // Tiêu đề và tổng quan
    expect(screen.getByText("Đánh giá chất lượng phục vụ Quý 3")).toBeInTheDocument();
    expect(screen.getByText("450")).toBeInTheDocument();
    expect(screen.getByText("100 đ")).toBeInTheDocument();

    // Bục vinh danh
    expect(screen.getByText("Bục Vinh Danh Top Dẫn Đầu")).toBeInTheDocument();
    expect(screen.getByText("QUÁN QUÂN")).toBeInTheDocument();
    expect(screen.getByText("Á QUÂN")).toBeInTheDocument();
    expect(screen.getByText("HẠNG BA")).toBeInTheDocument();

    // Tìm kiếm chi nhánh
    const searchInput = screen.getByPlaceholderText("Tìm tên chi nhánh…");
    fireEvent.change(searchInput, { target: { value: "Quận 1" } });

    expect(screen.getByText("Hiển thị 1/3 chi nhánh được đánh giá")).toBeInTheDocument();
  });
});
