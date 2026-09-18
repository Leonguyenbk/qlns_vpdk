import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

export function useTasks(params) {
  return useQuery({
    queryKey: ["tasks", params],
    queryFn: () => api.get("/tasks", { params }).then((r) => r.data.data),
    keepPreviousData: true,
  });
}

export function useTask(id) {
  return useQuery({
    queryKey: ["tasks", id],
    queryFn: () => api.get(`/tasks/${id}`).then((r) => r.data.data),
    enabled: !!id,
  });
}

export function useTaskDashboard(params) {
  return useQuery({
    queryKey: ["tasks", "dashboard", params],
    queryFn: () => api.get("/tasks/dashboard", { params }).then((r) => r.data.data),
  });
}

export function useAssignablePeople(params) {
  return useQuery({
    queryKey: ["tasks", "assignable-people", params],
    queryFn: () => api.get("/tasks/assignable-people", { params }).then((r) => r.data.data),
  });
}

export function useWorkload(userId) {
  return useQuery({
    queryKey: ["tasks", "workload", userId],
    queryFn: () => api.get(`/tasks/workload/${userId}`).then((r) => r.data.data),
    enabled: !!userId,
  });
}

export function useSelfReportQuantity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) => api.post("/tasks/self-report", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useTaskMutations(taskId) {
  const qc = useQueryClient();
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["tasks"] });
  };
  const on = { onSuccess: invalidate };
  return {
    create: useMutation({ mutationFn: (body) => api.post("/tasks", body), ...on }),
    updateProgress: useMutation({
      mutationFn: (body) => api.put(`/tasks/${taskId}/progress`, body), ...on,
    }),
    submit: useMutation({ mutationFn: (body) => api.post(`/tasks/${taskId}/submit`, body), ...on }),
    accept: useMutation({ mutationFn: (body) => api.post(`/tasks/${taskId}/accept`, body), ...on }),
    returnForRevision: useMutation({
      mutationFn: (body) => api.post(`/tasks/${taskId}/return`, body), ...on,
    }),
    extendDeadline: useMutation({
      mutationFn: (body) => api.put(`/tasks/${taskId}/deadline`, body), ...on,
    }),
    adjustWorkload: useMutation({
      mutationFn: (body) => api.put(`/tasks/${taskId}/workload`, body), ...on,
    }),
    cancel: useMutation({ mutationFn: (body) => api.post(`/tasks/${taskId}/cancel`, body), ...on }),
    addComment: useMutation({ mutationFn: (body) => api.post(`/tasks/${taskId}/comments`, body), ...on }),
    addWorkLog: useMutation({ mutationFn: (body) => api.post(`/tasks/${taskId}/work-logs`, body), ...on }),
    reportBlocker: useMutation({ mutationFn: (body) => api.post(`/tasks/${taskId}/blockers`, body), ...on }),
    confirmPause: useMutation({
      mutationFn: (pauseId) => api.post(`/tasks/${taskId}/pauses/${pauseId}/confirm`), ...on,
    }),
    resume: useMutation({ mutationFn: (body) => api.post(`/tasks/${taskId}/resume`, body || {}), ...on }),
    addAssignment: useMutation({ mutationFn: (body) => api.post(`/tasks/${taskId}/assignments`, body), ...on }),
    removeAssignment: useMutation({
      mutationFn: ({ assignmentId, body }) => api.delete(`/tasks/${taskId}/assignments/${assignmentId}`, { data: body }),
      ...on,
    }),
    uploadAttachment: useMutation({
      mutationFn: ({ file, kind }) => {
        const form = new FormData();
        form.append("file", file);
        form.append("kind", kind || "EVIDENCE");
        return api.post(`/tasks/${taskId}/attachments`, form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      },
      ...on,
    }),
  };
}
