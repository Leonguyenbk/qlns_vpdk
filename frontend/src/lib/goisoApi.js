/* Client cho API quản trị Gọi số (/api/admin/*, /api/branches...).
 * Khác với nhân sự: response KHÔNG bọc {success,data,message} — trả thẳng
 * {branches:[...]}, {ok:true,...} hoặc lỗi {error:"..."}. */
import { api } from "./api";

const d = (p) => p.then((r) => r.data);

export const goisoApi = {
  listBranches: () => d(api.get("/admin/branches")).then((r) => r.branches),
  createBranch: (body) => d(api.post("/admin/branches", { action: "create", ...body })),
  updateBranch: (code, body) => d(api.post("/admin/branches", { action: "update", code, ...body })),
  deleteBranch: (code) => d(api.post("/admin/branches", { action: "delete", code })),
  regenKey: (code) => d(api.post("/admin/branches", { action: "regen_key", code })),
  regenDisplayToken: (code) => d(api.post("/admin/branches", { action: "regen_display_token", code })),

  getBranchConfig: (code) => d(api.get(`/admin/b/${code}/config`)),
  setBranchConfig: (code, patch) => d(api.post(`/admin/b/${code}/config`, patch)),

  getStats: (branch = "all") => d(api.get("/admin/stats", { params: { branch } })),
  resetToday: (code) => d(api.post(`/admin/b/${code}/reset-today`)),

  getAppointments: (code, date) => d(api.get(`/admin/b/${code}/appointments`, { params: date ? { date } : {} })),
  cancelAppointment: (code, token) => d(api.post(`/admin/b/${code}/appointments/cancel`, { token })),

  listDevices: () => d(api.get("/admin/devices")),
  setKioskRelease: (payload) => d(api.post("/admin/kiosk-release", payload)),
};

export function goisoErrorMessage(error, fallback = "Đã xảy ra lỗi, vui lòng thử lại.") {
  return error?.response?.data?.error || error?.message || fallback;
}
