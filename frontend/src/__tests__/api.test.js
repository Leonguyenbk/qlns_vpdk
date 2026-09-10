import { describe, it, expect } from "vitest";
import {
  apiErrorMessage,
  conflictPayload,
  isRefreshExcludedEndpoint,
} from "../lib/api";

describe("Xử lý lỗi API", () => {
  it("apiErrorMessage lấy message tiếng Việt từ backend", () => {
    const err = { response: { data: { message: "Mã nhân sự đã tồn tại." } } };
    expect(apiErrorMessage(err)).toBe("Mã nhân sự đã tồn tại.");
  });

  it("apiErrorMessage dùng fallback khi không có response", () => {
    expect(apiErrorMessage({}, "Lỗi mạng")).toBe("Lỗi mạng");
  });

  it("conflictPayload trả payload khi status 409", () => {
    const err = {
      response: {
        status: 409,
        data: { data: { conflict: "POSITION_LIMIT_REACHED", current_holders: [] } },
      },
    };
    expect(conflictPayload(err)?.conflict).toBe("POSITION_LIMIT_REACHED");
  });

  it("conflictPayload trả null khi không phải 409", () => {
    expect(conflictPayload({ response: { status: 400 } })).toBeNull();
  });
});

describe("Phân loại endpoint khi access token hết hạn", () => {
  it("cho phép refresh khi tải thông tin phiên và đổi mật khẩu", () => {
    expect(isRefreshExcludedEndpoint("/auth/me")).toBe(false);
    expect(isRefreshExcludedEndpoint("/auth/change-password")).toBe(false);
  });

  it("không tự refresh tại các endpoint trực tiếp xử lý token", () => {
    expect(isRefreshExcludedEndpoint("/auth/login")).toBe(true);
    expect(isRefreshExcludedEndpoint("/auth/refresh?source=retry")).toBe(true);
    expect(isRefreshExcludedEndpoint("http://localhost:5000/api/auth/logout/")).toBe(true);
  });
});
