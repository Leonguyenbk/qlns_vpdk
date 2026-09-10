import axios from "axios";
import { API_BASE_URL } from "./constants";
import { tokenStore } from "./tokenStore";

// Sự kiện đăng xuất bắt buộc (khi refresh thất bại) để AuthContext lắng nghe
export const authEvents = new EventTarget();
export const emitForcedLogout = () =>
  authEvents.dispatchEvent(new Event("forced-logout"));

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Chỉ các endpoint trực tiếp phát/thu hồi token mới không được tự refresh.
// /auth/me và /auth/change-password vẫn cần retry khi access token vừa hết hạn.
const REFRESH_EXCLUDED_ENDPOINTS = ["/auth/login", "/auth/refresh", "/auth/logout"];

export function isRefreshExcludedEndpoint(url = "") {
  const path = String(url).split("?", 1)[0].replace(/\/+$/, "");
  return REFRESH_EXCLUDED_ENDPOINTS.some((endpoint) => path.endsWith(endpoint));
}

// --- Request interceptor: gắn access token ---
api.interceptors.request.use((config) => {
  const token = tokenStore.getAccess();
  if (token && !config._skipAuth) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- Response interceptor: tự động refresh khi 401 ---
let refreshing = null;

async function doRefresh() {
  const refreshToken = tokenStore.getRefresh();
  if (!refreshToken) throw new Error("no-refresh-token");
  const resp = await axios.post(
    `${API_BASE_URL}/auth/refresh`,
    {},
    { headers: { Authorization: `Bearer ${refreshToken}` } }
  );
  const data = resp.data?.data || {};
  tokenStore.set(data);
  return data.access_token;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;
    if (!response) return Promise.reject(error);

    const refreshExcluded = isRefreshExcludedEndpoint(config?.url);
    if (response.status === 401 && !config._retry && !refreshExcluded) {
      config._retry = true;
      try {
        refreshing = refreshing || doRefresh();
        const newAccess = await refreshing;
        refreshing = null;
        config.headers.Authorization = `Bearer ${newAccess}`;
        return api(config);
      } catch (e) {
        refreshing = null;
        tokenStore.clear();
        emitForcedLogout();
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);

// Chuẩn hóa thông báo lỗi tiếng Việt từ backend
export function apiErrorMessage(error, fallback = "Đã xảy ra lỗi, vui lòng thử lại.") {
  return (
    error?.response?.data?.message ||
    error?.message ||
    fallback
  );
}

// Trích payload xung đột (giới hạn chức vụ) từ lỗi 409
export function conflictPayload(error) {
  if (error?.response?.status === 409) return error.response.data?.data || null;
  return null;
}

export function unwrap(promise) {
  return promise.then((r) => r.data?.data);
}
