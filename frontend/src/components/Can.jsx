import { useAuth } from "../auth/AuthContext";

/**
 * Ẩn/hiện phần tử theo quyền. Dùng để ẩn hoặc khóa nút thao tác.
 * <Can permission="employee.create">...</Can>
 * <Can anyOf={["a","b"]} fallback={<Locked/>}>...</Can>
 */
export function Can({ permission, anyOf, children, fallback = null }) {
  const { hasPermission, hasAnyPermission } = useAuth();
  const ok = permission
    ? hasPermission(permission)
    : anyOf
    ? hasAnyPermission(anyOf)
    : true;
  return ok ? children : fallback;
}

export function useCan() {
  const { hasPermission, hasAnyPermission } = useAuth();
  return { can: hasPermission, canAny: hasAnyPermission };
}
