import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

export function useCatalogGroups() {
  return useQuery({
    queryKey: ["kpi", "catalog-groups"],
    queryFn: () => api.get("/kpi/catalog-groups").then((r) => r.data.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useProducts(params) {
  return useQuery({
    queryKey: ["kpi", "products", params],
    queryFn: () => api.get("/kpi/products", { params }).then((r) => r.data.data),
  });
}

export function useCriteriaSets() {
  return useQuery({
    queryKey: ["kpi", "criteria-sets"],
    queryFn: () => api.get("/kpi/criteria-sets").then((r) => r.data.data),
  });
}

export function useCriteriaSet(id) {
  return useQuery({
    queryKey: ["kpi", "criteria-sets", id],
    queryFn: () => api.get(`/kpi/criteria-sets/${id}`).then((r) => r.data.data),
    enabled: !!id,
  });
}

export function usePeriods() {
  return useQuery({
    queryKey: ["kpi", "periods"],
    queryFn: () => api.get("/kpi/periods").then((r) => r.data.data),
  });
}

export function usePeriodScores(periodId) {
  return useQuery({
    queryKey: ["kpi", "periods", periodId, "scores"],
    queryFn: () => api.get(`/kpi/periods/${periodId}/scores`).then((r) => r.data.data),
    enabled: !!periodId,
  });
}

export function useMyScores() {
  return useQuery({
    queryKey: ["kpi", "scores", "mine"],
    queryFn: () => api.get("/kpi/scores/mine").then((r) => r.data.data),
  });
}

export function useScore(id) {
  return useQuery({
    queryKey: ["kpi", "scores", id],
    queryFn: () => api.get(`/kpi/scores/${id}`).then((r) => r.data.data),
    enabled: !!id,
  });
}

export function useKpiAdminMutations() {
  const qc = useQueryClient();
  const invalidateCatalog = () => qc.invalidateQueries({ queryKey: ["kpi", "products"] });
  const invalidatePeriods = () => qc.invalidateQueries({ queryKey: ["kpi", "periods"] });
  return {
    createProduct: useMutation({ mutationFn: (body) => api.post("/kpi/products", body), onSuccess: invalidateCatalog }),
    createConversion: useMutation({
      mutationFn: ({ productId, body }) => api.post(`/kpi/products/${productId}/conversions`, body),
      onSuccess: invalidateCatalog,
    }),
    createCriteriaSet: useMutation({
      mutationFn: (body) => api.post("/kpi/criteria-sets", body),
      onSuccess: () => qc.invalidateQueries({ queryKey: ["kpi", "criteria-sets"] }),
    }),
    createDefaultCriteriaSet: useMutation({
      mutationFn: (body) => api.post("/kpi/criteria-sets/default", body),
      onSuccess: () => qc.invalidateQueries({ queryKey: ["kpi", "criteria-sets"] }),
    }),
    createPeriod: useMutation({ mutationFn: (body) => api.post("/kpi/periods", body), onSuccess: invalidatePeriods }),
    lockPeriod: useMutation({
      mutationFn: (periodId) => api.post(`/kpi/periods/${periodId}/lock`),
      onSuccess: invalidatePeriods,
    }),
    reopenPeriod: useMutation({
      mutationFn: ({ periodId, body }) => api.post(`/kpi/periods/${periodId}/reopen`, body),
      onSuccess: invalidatePeriods,
    }),
    computeScore: useMutation({
      mutationFn: ({ periodId, userId }) => api.post(`/kpi/periods/${periodId}/scores/${userId}/compute`),
      onSuccess: (_d, vars) => {
        invalidatePeriods();
        qc.invalidateQueries({ queryKey: ["kpi", "periods", vars.periodId, "scores"] });
      },
    }),
  };
}

export function useScoreMutations(scoreId) {
  const qc = useQueryClient();
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["kpi", "scores"] });
  };
  const on = { onSuccess: invalidate };
  return {
    selfAssess: useMutation({ mutationFn: (body) => api.post(`/kpi/scores/${scoreId}/self-assess`, body), ...on }),
    review: useMutation({ mutationFn: (body) => api.post(`/kpi/scores/${scoreId}/review`, body), ...on }),
    aggregate: useMutation({ mutationFn: (body) => api.post(`/kpi/scores/${scoreId}/aggregate`, body), ...on }),
    approve: useMutation({ mutationFn: (body) => api.post(`/kpi/scores/${scoreId}/approve`, body), ...on }),
    markNotRated: useMutation({ mutationFn: (body) => api.post(`/kpi/scores/${scoreId}/not-rated`, body), ...on }),
    adjust: useMutation({ mutationFn: (body) => api.post(`/kpi/scores/${scoreId}/adjust`, body), ...on }),
    addComment: useMutation({ mutationFn: (body) => api.post(`/kpi/scores/${scoreId}/comments`, body), ...on }),
  };
}
