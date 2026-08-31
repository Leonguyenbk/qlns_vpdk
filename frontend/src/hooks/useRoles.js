import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

export function useRoles() {
  return useQuery({
    queryKey: ["roles"],
    queryFn: () => api.get("/roles").then((r) => r.data.data),
  });
}

export function usePermissions() {
  return useQuery({
    queryKey: ["permissions"],
    queryFn: () => api.get("/permissions").then((r) => r.data.data),
  });
}

export function useRoleMutations() {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["roles"] });
  return {
    create: useMutation({ mutationFn: (body) => api.post("/roles", body), onSuccess: invalidate }),
    update: useMutation({
      mutationFn: ({ id, body }) => api.put(`/roles/${id}`, body),
      onSuccess: invalidate,
    }),
    remove: useMutation({ mutationFn: (id) => api.delete(`/roles/${id}`), onSuccess: invalidate }),
  };
}
