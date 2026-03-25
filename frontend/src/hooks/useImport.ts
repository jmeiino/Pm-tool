import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  JiraPreviewResponse,
  GitHubPreviewResponse,
  ConfluencePreviewResponse,
  ImportConfirmResponse,
  JiraConfirmProject,
  GitHubConfirmRepo,
  ConfluenceConfirmPage,
} from "@/lib/types";

// ─── Jira ────────────────────────────────────────────────────────────────────

export function useJiraPreview(enabled = true) {
  return useQuery({
    queryKey: ["import", "jira", "preview"],
    queryFn: async () => {
      const { data } = await api.get<JiraPreviewResponse>(
        "/integrations/import/jira/preview/"
      );
      return data;
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 Minuten Cache
  });
}

export function useJiraConfirmImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (projects: JiraConfirmProject[]) => {
      const { data } = await api.post<ImportConfirmResponse>(
        "/integrations/import/jira/confirm/",
        { projects }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["import", "jira"] });
    },
  });
}

// ─── GitHub ──────────────────────────────────────────────────────────────────

export function useGitHubPreview(mineOnly: boolean, enabled = true) {
  return useQuery({
    queryKey: ["import", "github", "preview", mineOnly],
    queryFn: async () => {
      const params = mineOnly ? "?mine_only=true" : "";
      const { data } = await api.get<GitHubPreviewResponse>(
        `/integrations/import/github/preview/${params}`
      );
      return data;
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useGitHubConfirmImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (repos: GitHubConfirmRepo[]) => {
      const { data } = await api.post<ImportConfirmResponse>(
        "/integrations/import/github/confirm/",
        { repos }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["import", "github"] });
    },
  });
}

// ─── Confluence ──────────────────────────────────────────────────────────────

export function useConfluenceSpacesPreview(enabled = true) {
  return useQuery({
    queryKey: ["import", "confluence", "spaces"],
    queryFn: async () => {
      const { data } = await api.get<ConfluencePreviewResponse>(
        "/integrations/import/confluence/preview/"
      );
      return data;
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useConfluencePagesPreview(
  spaceKey: string,
  myPagesOnly: boolean,
  enabled = true
) {
  return useQuery({
    queryKey: ["import", "confluence", "pages", spaceKey, myPagesOnly],
    queryFn: async () => {
      const params = new URLSearchParams({ space_key: spaceKey });
      if (myPagesOnly) params.set("my_pages_only", "true");
      const { data } = await api.get<ConfluencePreviewResponse>(
        `/integrations/import/confluence/preview/?${params}`
      );
      return data;
    },
    enabled: enabled && !!spaceKey,
    staleTime: 5 * 60 * 1000,
  });
}

export function useConfluenceConfirmImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      pages: ConfluenceConfirmPage[];
      selected_action_item_indices?: number[];
    }) => {
      const { data } = await api.post<ImportConfirmResponse>(
        "/integrations/import/confluence/confirm/",
        payload
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["confluence-pages"] });
      queryClient.invalidateQueries({ queryKey: ["import", "confluence"] });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}
