import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { downloadFile } from "../lib/download";

export function useSurveys(params) {
  return useQuery({
    queryKey: ["surveys", params],
    queryFn: () => api.get("/surveys", { params }).then((r) => r.data.data),
    keepPreviousData: true,
  });
}

export function useSurvey(id) {
  return useQuery({
    queryKey: ["surveys", id],
    queryFn: () => api.get(`/surveys/${id}`).then((r) => r.data.data),
    enabled: !!id,
  });
}

export function useSurveyMutations() {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["surveys"] });
  return {
    create: useMutation({ mutationFn: (body) => api.post("/surveys", body), onSuccess: invalidate }),
    update: useMutation({
      mutationFn: ({ id, body }) => api.put(`/surveys/${id}`, body),
      onSuccess: invalidate,
    }),
    remove: useMutation({ mutationFn: (id) => api.delete(`/surveys/${id}`), onSuccess: invalidate }),
    changeStatus: useMutation({
      mutationFn: ({ id, status }) => api.post(`/surveys/${id}/status`, { status }),
      onSuccess: invalidate,
    }),
    duplicate: useMutation({
      mutationFn: (id) => api.post(`/surveys/${id}/duplicate`),
      onSuccess: invalidate,
    }),
  };
}

export function exportSurvey(id, params) {
  return downloadFile(`/surveys/${id}/export`, { params, fallbackName: `khao-sat-${id}.xlsx` });
}
