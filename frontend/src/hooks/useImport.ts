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

// ─── Dashboard ───────────────────────────────────────────────────────────────

export interface ImportHistoryEntry {
  integration_id: number;
  integration_type: string;
  is_enabled: boolean;
  last_synced_at: string | null;
  sync_status: string;
  item_count: number;
  poll_interval: number | null;
  recent_logs: {
    id: number;
    direction: string;
    status: string;
    records_created: number;
    records_updated: number;
    errors: string[];
    started_at: string | null;
    completed_at: string | null;
  }[];
}

export function useImportDashboard(enabled = true) {
  return useQuery({
    queryKey: ["import", "dashboard"],
    queryFn: async () => {
      const { data } = await api.get<{ integrations: ImportHistoryEntry[] }>(
        "/integrations/import/dashboard/history/"
      );
      return data;
    },
    enabled,
    staleTime: 30 * 1000,
  });
}

export function useGitHubConflicts(enabled = true) {
  return useQuery({
    queryKey: ["import", "github", "conflicts"],
    queryFn: async () => {
      const { data } = await api.get<{ conflicts: Record<string, unknown>[]; count: number }>(
        "/integrations/import/github/conflicts/"
      );
      return data;
    },
    enabled,
    staleTime: 60 * 1000,
  });
}

export function useUpdateSyncSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { integration_id: number; poll_interval: number }) => {
      const { data } = await api.post("/integrations/import/dashboard/update-schedule/", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["import", "dashboard"] });
    },
  });
}

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

export function useJiraProjectIssues(projectKey: string, enabled = true) {
  return useQuery({
    queryKey: ["import", "jira", "issues", projectKey],
    queryFn: async () => {
      const { data } = await api.get<JiraPreviewResponse>(
        `/integrations/import/jira/preview/?project_key=${projectKey}`
      );
      return data;
    },
    enabled: enabled && !!projectKey,
    staleTime: 5 * 60 * 1000,
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

export function useConfluenceActionItems(pageIds: number[], enabled = true) {
  return useQuery({
    queryKey: ["import", "confluence", "action-items", pageIds],
    queryFn: async () => {
      // Lade die analysierten Seiten über die bestehende API
      const results = await Promise.all(
        pageIds.map(async (id) => {
          const { data } = await api.get(`/integrations/confluence-pages/${id}/`);
          return data as {
            id: number;
            title: string;
            ai_action_items: string[];
            ai_processed_at: string | null;
          };
        })
      );
      return results.filter((p) => p.ai_action_items && p.ai_action_items.length > 0);
    },
    enabled: enabled && pageIds.length > 0,
    refetchInterval: (query) => {
      // Solange Seiten noch nicht analysiert sind, alle 5 Sekunden pollen
      const data = query.state.data;
      if (!data || data.length < pageIds.length) return 5000;
      return false;
    },
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
