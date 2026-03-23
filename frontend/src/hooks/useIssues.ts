import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  PaginatedResponse,
  Issue,
  IssueDetail,
  ProjectStats,
} from "@/lib/types";
import type { IssueCreateInput } from "@/lib/schemas";

export function useIssues(
  projectId?: number,
  filters?: Record<string, string>
) {
  const params = new URLSearchParams(filters);
  if (projectId) params.set("project", String(projectId));

  return useQuery({
    queryKey: ["issues", projectId, filters],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Issue>>(
        `/issues/?${params.toString()}`
      );
      return data;
    },
  });
}

export function useIssue(id: number) {
  return useQuery({
    queryKey: ["issues", id],
    queryFn: async () => {
      const { data } = await api.get<IssueDetail>(`/issues/${id}/`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateIssue() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: IssueCreateInput) => {
      const { data } = await api.post<Issue>("/issues/", input);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateIssue() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...data
    }: Partial<Issue> & { id: number }) => {
      const { data: result } = await api.patch<Issue>(`/issues/${id}/`, data);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues"] });
    },
  });
}

export function useTransitionIssue() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      status,
    }: {
      id: number;
      status: string;
    }) => {
      const { data } = await api.post<IssueDetail>(
        `/issues/${id}/transition/`,
        { status }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues"] });
    },
  });
}

export function useProjectStats(projectId: number) {
  return useQuery({
    queryKey: ["projects", projectId, "stats"],
    queryFn: async () => {
      const { data } = await api.get<ProjectStats>(
        `/projects/${projectId}/stats/`
      );
      return data;
    },
    enabled: !!projectId,
  });
}
