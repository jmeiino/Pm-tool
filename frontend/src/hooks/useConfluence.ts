import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse } from "@/lib/types";

export interface ConfluencePage {
  id: number;
  confluence_page_id: string;
  space_key: string;
  title: string;
  content_text: string;
  last_confluence_update: string;
  ai_summary: string;
  ai_action_items: string[];
  ai_decisions: string[];
  ai_risks: string[];
  ai_processed_at: string | null;
  created_at: string;
  updated_at: string;
}

export function useConfluencePages(filters?: Record<string, string>) {
  const params = new URLSearchParams(filters);
  return useQuery({
    queryKey: ["confluence-pages", filters],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<ConfluencePage>>(
        `/integrations/confluence-pages/?${params.toString()}`
      );
      return data;
    },
  });
}

export function useConfluencePage(id: number) {
  return useQuery({
    queryKey: ["confluence-pages", id],
    queryFn: async () => {
      const { data } = await api.get<ConfluencePage>(
        `/integrations/confluence-pages/${id}/`
      );
      return data;
    },
    enabled: !!id,
  });
}

export function useAnalyzeConfluencePage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post(
        `/integrations/confluence-pages/${id}/analyze/`
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["confluence-pages"] });
    },
  });
}

export function useCreateTodosFromPage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post(
        `/integrations/confluence-pages/${id}/create-todos/`
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}
