import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export function useSurveyResponses(surveyId, params) {
  return useQuery({
    queryKey: ["surveys", surveyId, "responses", params],
    queryFn: () => api.get(`/surveys/${surveyId}/responses`, { params }).then((r) => r.data.data),
    enabled: !!surveyId,
    keepPreviousData: true,
  });
}

export function useSurveyStatistics(surveyId, params) {
  return useQuery({
    queryKey: ["surveys", surveyId, "statistics", params],
    queryFn: () => api.get(`/surveys/${surveyId}/statistics`, { params }).then((r) => r.data.data),
    enabled: !!surveyId,
  });
}
