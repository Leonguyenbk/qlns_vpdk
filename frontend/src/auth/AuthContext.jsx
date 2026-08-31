import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, authEvents } from "../lib/api";
import { tokenStore } from "../lib/tokenStore";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadMe = useCallback(async () => {
    if (!tokenStore.getAccess()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const resp = await api.get("/auth/me");
      setUser(resp.data.data);
    } catch {
      tokenStore.clear();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  useEffect(() => {
    const handler = () => {
      setUser(null);
    };
    authEvents.addEventListener("forced-logout", handler);
    return () => authEvents.removeEventListener("forced-logout", handler);
  }, []);

  const login = useCallback(async (username, password) => {
    const resp = await api.post("/auth/login", { username, password });
    const data = resp.data.data;
    tokenStore.set(data);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    const refresh = tokenStore.getRefresh();
    try {
      if (refresh) {
        await api.post(
          "/auth/logout",
          {},
          { headers: { Authorization: `Bearer ${refresh}` }, _skipAuth: true }
        );
      }
    } catch {
      /* bỏ qua lỗi mạng khi đăng xuất */
    } finally {
      tokenStore.clear();
      setUser(null);
    }
  }, []);

  const value = useMemo(() => {
    const permissions = new Set(user?.permissions || []);
    return {
      user,
      loading,
      isAuthenticated: !!user,
      permissions,
      hasPermission: (code) => permissions.has(code),
      hasAnyPermission: (codes) => codes.some((c) => permissions.has(c)),
      login,
      logout,
      refreshMe: loadMe,
    };
  }, [user, loading, login, logout, loadMe]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth phải được dùng bên trong <AuthProvider>");
  return ctx;
}
