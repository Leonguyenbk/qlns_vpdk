/* Client cho API gọi số công khai / bàn gọi số (/api/b/<code>/*, /api/booking/*,
 * /api/ping, /api/branches). Response KHÔNG bọc {success,data,message} — trả
 * thẳng {..} hoặc lỗi {error:"..."}, giống lib/goisoApi.js (quản trị). */
import { api } from "./api";

const d = (p) => p.then((r) => r.data);

export function branchApi(code) {
  const base = `/b/${encodeURIComponent(code)}`;
  return {
    state: () => d(api.get(`${base}/state`)),
    configPublic: () => d(api.get(`${base}/config/public`)),
    screens: () => d(api.get(`${base}/screens`)).then((r) => r.screens),
    counters: () => d(api.get(`${base}/counters`)).then((r) => r.counters),
    checkin: (code_) => d(api.post(`${base}/checkin`, { code: code_ })),
    counter(counterId) {
      const cb = `${base}/counter/${encodeURIComponent(counterId)}`;
      return {
        view: () => d(api.get(`${cb}/view`)),
        login: () => d(api.post(`${cb}/login`, {})),
        next: () => d(api.post(`${cb}/next`, {})),
        recall: () => d(api.post(`${cb}/recall`, {})),
        done: () => d(api.post(`${cb}/done`, {})),
        missed: () => d(api.post(`${cb}/missed`, {})),
        call: (full_no) => d(api.post(`${cb}/call`, { full_no })),
        status: (status) => d(api.post(`${cb}/status`, { status })),
      };
    },
  };
}

export const goisoPublicApi = {
  ping: () => d(api.get("/ping")),
  branches: () => d(api.get("/branches")).then((r) => r.branches),
  bookingBranches: () => d(api.get("/booking/branches")).then((r) => r.branches),
  bookingSlots: (code, date, prefix) =>
    d(api.get(`/booking/${code}/slots`, { params: { date, prefix } })).then((r) => r.slots),
  bookingBook: (code, body) => d(api.post(`/booking/${code}/book`, body)),
  bookingAppt: (token) => d(api.get(`/booking/appt/${token}`)),
  bookingCancel: (token) => d(api.post(`/booking/appt/${token}/cancel`)),
  turnstileKey: () => d(api.get("/booking/turnstile-key")).then((r) => r.site_key),
};

export function goisoErr(err, fallback = "Đã xảy ra lỗi, vui lòng thử lại.") {
  return err?.response?.data?.error || err?.message || fallback;
}
