import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";

export function useEmployees(params) {
  return useQuery({
    queryKey: ["employees", params],
    queryFn: () => api.get("/employees", { params }).then((r) => r.data.data),
    keepPreviousData: true,
  });
}

export function useEmployee(id, { includeDeleted = false } = {}) {
  return useQuery({
    queryKey: ["employees", id, { includeDeleted }],
    queryFn: () =>
      api
        .get(`/employees/${id}`, { params: { include_deleted: includeDeleted } })
        .then((r) => r.data.data),
    enabled: !!id,
  });
}

export function useEmployeeAssignments(id) {
  return useQuery({
    queryKey: ["employees", id, "assignments"],
    queryFn: () => api.get(`/employees/${id}/assignments`).then((r) => r.data.data),
    enabled: !!id,
  });
}

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get("/employees/dashboard").then((r) => r.data.data),
  });
}

export function useEmployeeMutations() {
  const qc = useQueryClient();
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["employees"] });
    qc.invalidateQueries({ queryKey: ["dashboard"] });
  };
  return {
    create: useMutation({ mutationFn: (body) => api.post("/employees", body), onSuccess: invalidate }),
    update: useMutation({
      mutationFn: ({ id, body }) => api.put(`/employees/${id}`, body),
      onSuccess: invalidate,
    }),
    remove: useMutation({ mutationFn: (id) => api.delete(`/employees/${id}`), onSuccess: invalidate }),
    restore: useMutation({
      mutationFn: (id) => api.post(`/employees/${id}/restore`),
      onSuccess: invalidate,
    }),
    transfer: useMutation({
      mutationFn: ({ id, body }) => api.post(`/employees/${id}/transfer`, body),
      onSuccess: invalidate,
    }),
  };
}
