import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

export function useAnnouncements(params = {}) {
  return useQuery({
    queryKey: ["announcements", params],
    queryFn: () => api.get("/announcements", { params }).then((r) => r.data.data),
    keepPreviousData: true,
  });
}

export function useAnnouncementAudienceOptions(enabled = true) {
  return useQuery({
    queryKey: ["announcements", "audience-options"],
    queryFn: () => api.get("/announcements/audience-options").then((r) => r.data.data),
    enabled,
  });
}

export function useAnnouncementMutations() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["announcements"] });
  return {
    create: useMutation({
      mutationFn: (body) => api.post("/announcements", body),
      onSuccess: invalidate,
    }),
    update: useMutation({
      mutationFn: ({ id, body }) => api.put(`/announcements/${id}`, body),
      onSuccess: invalidate,
    }),
    remove: useMutation({
      mutationFn: (id) => api.delete(`/announcements/${id}`),
      onSuccess: invalidate,
    }),
    setStatus: useMutation({
      mutationFn: ({ id, status }) => api.post(`/announcements/${id}/status`, { status }),
      onSuccess: invalidate,
    }),
    markRead: useMutation({
      mutationFn: (id) => api.post(`/announcements/${id}/read`),
      onSuccess: invalidate,
    }),
  };
}
