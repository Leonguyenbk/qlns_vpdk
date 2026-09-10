import { AuthContext } from "../auth/AuthContext";

// Provider giả lập cho test: cho phép truyền thẳng giá trị context.
export function AuthContextTestProvider({ value, children }) {
  const permissions = new Set(value.permissions || []);
  const merged = {
    user: value.user ?? (value.isAuthenticated ? { full_name: "Test User", roles: [] } : null),
    loading: value.loading ?? false,
    isAuthenticated: value.isAuthenticated ?? false,
    permissions,
    hasPermission: (c) => permissions.has(c),
    hasAnyPermission: (codes) => codes.some((c) => permissions.has(c)),
    login: value.login ?? (async () => {}),
    logout: value.logout ?? (async () => {}),
    refreshMe: async () => {},
    ...value,
    // đảm bảo hasPermission luôn phản ánh permissions truyền vào
    ...(value.permissions
      ? {
          hasPermission: (c) => permissions.has(c),
          hasAnyPermission: (codes) => codes.some((c) => permissions.has(c)),
        }
      : {}),
  };
  return <AuthContext.Provider value={merged}>{children}</AuthContext.Provider>;
}
