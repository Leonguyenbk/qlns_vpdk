import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

export function usePositions(params = {}) {
  return useQuery({
    queryKey: ["positions", params],
    queryFn: () => api.get("/positions", { params }).then((r) => r.data.data),
  });
}

export function usePositionMutations() {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["positions"] });
  return {
    create: useMutation({ mutationFn: (body) => api.post("/positions", body), onSuccess: invalidate }),
    update: useMutation({
      mutationFn: ({ id, body }) => api.put(`/positions/${id}`, body),
      onSuccess: invalidate,
    }),
    remove: useMutation({ mutationFn: (id) => api.delete(`/positions/${id}`), onSuccess: invalidate }),
  };
}

export function usePositionLimits(unitId) {
  return useQuery({
    queryKey: ["units", unitId, "position-limits"],
    queryFn: () => api.get(`/units/${unitId}/position-limits`).then((r) => r.data.data),
    enabled: !!unitId,
  });
}

export function usePositionLimitMutations(unitId) {
  const qc = useQueryClient();
  const invalidate = () =>
    qc.invalidateQueries({ queryKey: ["units", unitId, "position-limits"] });
  return {
    create: useMutation({
      mutationFn: (body) => api.post(`/units/${unitId}/position-limits`, body),
      onSuccess: invalidate,
    }),
    update: useMutation({
      mutationFn: ({ id, body }) => api.put(`/units/${unitId}/position-limits/${id}`, body),
      onSuccess: invalidate,
    }),
  };
}
