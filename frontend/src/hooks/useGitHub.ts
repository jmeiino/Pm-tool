import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, GitActivity, GitRepoAnalysis } from "@/lib/types";

interface GitHubProjectItem {
  id: string;
  content: {
    title: string;
    number: number;
    state: string;
    url: string;
    repository?: { nameWithOwner: string };
  } | null;
}

interface GitHubProject {
  id: string;
  title: string;
  shortDescription: string;
  url: string;
  closed: boolean;
  items: { totalCount: number; nodes: GitHubProjectItem[] };
  fields?: { nodes: { id: string; name: string; options?: { id: string; name: string }[] }[] };
}

export function useGitActivities(filters?: {
  project?: number;
  event_type?: string;
}) {
  const params = new URLSearchParams();
  if (filters?.project) params.set("project", String(filters.project));
  if (filters?.event_type) params.set("event_type", filters.event_type);

  return useQuery({
    queryKey: ["git-activities", filters],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<GitActivity>>(
        `/integrations/git-activities/?${params.toString()}`
      );
      return data;
    },
  });
}

export function useRepoAnalyses() {
  return useQuery({
    queryKey: ["repo-analyses"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<GitRepoAnalysis>>(
        "/integrations/repo-analyses/"
      );
      return data;
    },
  });
}

export function useRepoAnalysis(id: number) {
  return useQuery({
    queryKey: ["repo-analyses", id],
    queryFn: async () => {
      const { data } = await api.get<GitRepoAnalysis>(
        `/integrations/repo-analyses/${id}/`
      );
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateRepoAnalysis() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (repoFullName: string) => {
      const { data } = await api.post<GitRepoAnalysis>(
        "/integrations/repo-analyses/",
        { repo_full_name: repoFullName }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repo-analyses"] });
    },
  });
}

export function useAnalyzeRepo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post(
        `/integrations/repo-analyses/${id}/analyze/`
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repo-analyses"] });
    },
  });
}

export function useGitHubProjects(login?: string, org?: string) {
  const params = new URLSearchParams();
  if (login) params.set("login", login);
  if (org) params.set("org", org);

  return useQuery({
    queryKey: ["github-projects", login, org],
    queryFn: async () => {
      const { data } = await api.get<{ projects: GitHubProject[] }>(
        `/integrations/github-projects/list_projects/?${params.toString()}`
      );
      return data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateTodosFromRepo() {
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<{ detail: string; count: number }>(
        `/integrations/repo-analyses/${id}/create-todos/`
      );
      return data;
    },
  });
}
