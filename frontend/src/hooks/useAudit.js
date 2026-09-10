import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function useAuditLogs(params) {
  return useQuery({
    queryKey: ["audit-logs", params],
    queryFn: () => api.get("/audit-logs", { params }).then((r) => r.data.data),
    keepPreviousData: true,
  });
}
