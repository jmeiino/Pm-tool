import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, IntegrationConfig, SyncLog } from "@/lib/types";

export function useIntegrations() {
  return useQuery({
    queryKey: ["integrations"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<IntegrationConfig>>(
        "/integrations/configs/"
      );
      return data;
    },
  });
}

export function useCreateIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: {
      integration_type: string;
      credentials: Record<string, string>;
      is_enabled: boolean;
      settings?: Record<string, unknown>;
    }) => {
      const { data } = await api.post<IntegrationConfig>(
        "/integrations/configs/",
        input
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });
}

export function useUpdateIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...data
    }: Partial<IntegrationConfig> & { id: number }) => {
      const { data: result } = await api.patch<IntegrationConfig>(
        `/integrations/configs/${id}/`,
        data
      );
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });
}

export function useSyncIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post(`/integrations/configs/${id}/sync/`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });
}

export function useDeleteIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/integrations/configs/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });
}

export function useRegisterWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, callback_url }: { id: number; callback_url: string }) => {
      const { data } = await api.post(
        `/integrations/configs/${id}/register-webhooks/`,
        { callback_url }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });
}

export function useSyncLogs(integrationId?: number) {
  const params = integrationId ? `?integration=${integrationId}` : "";
  return useQuery({
    queryKey: ["sync-logs", integrationId],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<SyncLog>>(
        `/integrations/sync-logs/${params}`
      );
      return data;
    },
  });
}
