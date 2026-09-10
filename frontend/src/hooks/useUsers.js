import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

export function useUsers(params) {
  return useQuery({
    queryKey: ["users", params],
    queryFn: () => api.get("/users", { params }).then((r) => r.data.data),
    keepPreviousData: true,
  });
}

export function useUserMutations() {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["users"] });
  return {
    create: useMutation({ mutationFn: (body) => api.post("/users", body), onSuccess: invalidate }),
    update: useMutation({
      mutationFn: ({ id, body }) => api.put(`/users/${id}`, body),
      onSuccess: invalidate,
    }),
    resetPassword: useMutation({
      mutationFn: ({ id, body }) => api.post(`/users/${id}/reset-password`, body || {}),
    }),
    setRoles: useMutation({
      mutationFn: ({ id, role_ids }) => api.post(`/users/${id}/roles`, { role_ids }),
      onSuccess: invalidate,
    }),
    setScopes: useMutation({
      mutationFn: ({ id, scopes }) => api.post(`/users/${id}/unit-scopes`, { scopes }),
      onSuccess: invalidate,
    }),
  };
}
