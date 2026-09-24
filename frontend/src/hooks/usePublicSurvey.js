import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function usePublicSurvey(slug) {
  return useQuery({
    queryKey: ["public-survey", slug],
    queryFn: () => api.get(`/public/surveys/${slug}`).then((r) => r.data.data),
    enabled: !!slug,
    retry: false,
  });
}

export function usePublicSurveyResults(slug) {
  return useQuery({
    queryKey: ["public-survey-results", slug],
    queryFn: () => api.get(`/public/surveys/${slug}/results`).then((r) => r.data.data),
    enabled: !!slug,
    retry: false,
  });
}

export function useSubmitSurveyResponse(surveyId) {
  return useMutation({
    mutationFn: (body) => api.post(`/public/surveys/${surveyId}/submit`, body).then((r) => r.data),
  });
}
