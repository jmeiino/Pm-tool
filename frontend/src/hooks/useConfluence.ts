import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, ConfluencePage } from "@/lib/types";

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
