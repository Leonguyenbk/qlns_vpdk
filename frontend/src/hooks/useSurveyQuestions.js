import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

export function useSurveyQuestions(surveyId, { includeInactive = false } = {}) {
  return useQuery({
    queryKey: ["surveys", surveyId, "questions", { includeInactive }],
    queryFn: () =>
      api
        .get(`/surveys/${surveyId}/questions`, { params: { include_inactive: includeInactive ? 1 : 0 } })
        .then((r) => r.data.data),
    enabled: !!surveyId,
  });
}

export function useSurveySections(surveyId) {
  return useQuery({
    queryKey: ["surveys", surveyId, "sections"],
    queryFn: () => api.get(`/surveys/${surveyId}/sections`).then((r) => r.data.data),
    enabled: !!surveyId,
  });
}

export function useSurveySectionMutations(surveyId) {
  const qc = useQueryClient();
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["surveys", surveyId, "sections"] });
    qc.invalidateQueries({ queryKey: ["surveys", surveyId, "questions"] });
  };
  return {
    create: useMutation({
      mutationFn: (body) => api.post(`/surveys/${surveyId}/sections`, body),
      onSuccess: invalidate,
    }),
    update: useMutation({
      mutationFn: ({ id, body }) => api.put(`/survey-sections/${id}`, body),
      onSuccess: invalidate,
    }),
    remove: useMutation({
      mutationFn: (id) => api.delete(`/survey-sections/${id}`),
      onSuccess: invalidate,
    }),
    reorder: useMutation({
      mutationFn: (items) => api.post(`/surveys/${surveyId}/sections/reorder`, { items }),
      onSuccess: invalidate,
    }),
  };
}

export function useSurveyQuestionMutations(surveyId) {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["surveys", surveyId, "questions"] });
  return {
    create: useMutation({
      mutationFn: (body) => api.post(`/surveys/${surveyId}/questions`, body),
      onSuccess: invalidate,
    }),
    update: useMutation({
      mutationFn: ({ id, body }) => api.put(`/survey-questions/${id}`, body),
      onSuccess: invalidate,
    }),
    remove: useMutation({
      mutationFn: (id) => api.delete(`/survey-questions/${id}`),
      onSuccess: invalidate,
    }),
    duplicate: useMutation({
      mutationFn: (id) => api.post(`/survey-questions/${id}/duplicate`),
      onSuccess: invalidate,
    }),
    reorder: useMutation({
      mutationFn: (items) => api.post(`/surveys/${surveyId}/questions/reorder`, { items }),
      onSuccess: invalidate,
    }),
    createOption: useMutation({
      mutationFn: ({ questionId, body }) => api.post(`/survey-questions/${questionId}/options`, body),
      onSuccess: invalidate,
    }),
    updateOption: useMutation({
      mutationFn: ({ id, body }) => api.put(`/survey-options/${id}`, body),
      onSuccess: invalidate,
    }),
    removeOption: useMutation({
      mutationFn: (id) => api.delete(`/survey-options/${id}`),
      onSuccess: invalidate,
    }),
    reorderOptions: useMutation({
      mutationFn: ({ questionId, items }) =>
        api.post(`/survey-questions/${questionId}/options/reorder`, { items }),
      onSuccess: invalidate,
    }),
  };
}
