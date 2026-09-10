import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

export function useUnits(params = {}) {
  return useQuery({
    queryKey: ["units", params],
    queryFn: () => api.get("/units", { params }).then((r) => r.data.data),
  });
}

export function useUnitTree() {
  return useQuery({
    queryKey: ["units", "tree"],
    queryFn: () => api.get("/units/tree").then((r) => r.data.data),
  });
}

export function useUnit(id) {
  return useQuery({
    queryKey: ["units", id],
    queryFn: () => api.get(`/units/${id}`).then((r) => r.data.data),
    enabled: !!id,
  });
}

export function useUnitMutations() {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["units"] });
  return {
    create: useMutation({ mutationFn: (body) => api.post("/units", body), onSuccess: invalidate }),
    update: useMutation({
      mutationFn: ({ id, body }) => api.put(`/units/${id}`, body),
      onSuccess: invalidate,
    }),
    remove: useMutation({ mutationFn: (id) => api.delete(`/units/${id}`), onSuccess: invalidate }),
  };
}
