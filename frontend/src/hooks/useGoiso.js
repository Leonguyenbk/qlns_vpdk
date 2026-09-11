import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { goisoApi } from "../lib/goisoApi";

export function useGoisoBranches() {
  return useQuery({ queryKey: ["goiso", "branches"], queryFn: goisoApi.listBranches });
}

export function useGoisoBranchMutations() {
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({ queryKey: ["goiso", "branches"] });
  return {
    create: useMutation({ mutationFn: goisoApi.createBranch, onSuccess: invalidate }),
    update: useMutation({
      mutationFn: ({ code, body }) => goisoApi.updateBranch(code, body),
      onSuccess: invalidate,
    }),
    remove: useMutation({ mutationFn: goisoApi.deleteBranch, onSuccess: invalidate }),
    regenKey: useMutation({ mutationFn: goisoApi.regenKey, onSuccess: invalidate }),
    regenDisplayToken: useMutation({ mutationFn: goisoApi.regenDisplayToken, onSuccess: invalidate }),
  };
}

export function useGoisoBranchConfig(code) {
  return useQuery({
    queryKey: ["goiso", "branch-config", code],
    queryFn: () => goisoApi.getBranchConfig(code),
    enabled: !!code,
  });
}

export function useGoisoBranchConfigMutation(code) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch) => goisoApi.setBranchConfig(code, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goiso", "branch-config", code] }),
  });
}

export function useGoisoStats(branch = "all") {
  return useQuery({ queryKey: ["goiso", "stats", branch], queryFn: () => goisoApi.getStats(branch) });
}

export function useGoisoDevices() {
  return useQuery({ queryKey: ["goiso", "devices"], queryFn: goisoApi.listDevices });
}

export function useGoisoKioskReleaseMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: goisoApi.setKioskRelease,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goiso", "devices"] }),
  });
}
