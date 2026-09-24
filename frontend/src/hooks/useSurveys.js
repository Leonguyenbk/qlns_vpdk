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
    setResultsPublic: useMutation({
      mutationFn: ({ id, is_results_public }) =>
        api.put(`/surveys/${id}/results-public`, { is_results_public }),
      onSuccess: invalidate,
    }),
  };
}

export function exportSurvey(id, params) {
  return downloadFile(`/surveys/${id}/export`, { params, fallbackName: `khao-sat-${id}.xlsx` });
}

/** Xuất bảng TỔNG HỢP tỷ lệ theo câu hỏi (toàn hệ thống hoặc theo chi nhánh nếu
 * có lọc) — không có thông tin người trả lời, khác với `exportSurvey`. */
export function exportSurveySummary(id, params) {
  return downloadFile(`/surveys/${id}/statistics/export`, {
    params,
    fallbackName: `tong-hop-khao-sat-${id}.xlsx`,
  });
}

export function useSurveyBranchLimits(surveyId) {
  return useQuery({
    queryKey: ["surveys", surveyId, "branch-limits"],
    queryFn: () => api.get(`/surveys/${surveyId}/branch-limits`).then((r) => r.data.data),
    enabled: !!surveyId,
  });
}

export function useSetSurveyBranchLimits(surveyId) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (items) => api.put(`/surveys/${surveyId}/branch-limits`, { items }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["surveys", surveyId, "branch-limits"] }),
  });
}
