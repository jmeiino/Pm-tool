import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  AdminDashboardStats,
  AdminIntegration,
  AdminSyncLog,
  AdminUser,
  AgentOverview,
  AIStats,
  PaginatedResponse,
  SystemHealth,
} from "@/lib/types";

// ─── Dashboard ───────────────────────────────────────────────────────────────

export function useAdminDashboard() {
  return useQuery({
    queryKey: ["admin-dashboard"],
    queryFn: async () => {
      const { data } = await api.get<AdminDashboardStats>("/admin/dashboard/");
      return data;
    },
    refetchInterval: 30000,
  });
}

// ─── Benutzerverwaltung ──────────────────────────────────────────────────────

export function useAdminUsers() {
  return useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<AdminUser>>("/admin/users/");
      return data;
    },
  });
}

export function useCreateAdminUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      username: string;
      email: string;
      first_name: string;
      last_name: string;
      password: string;
      is_staff: boolean;
      timezone?: string;
    }) => {
      const { data } = await api.post("/admin/users/", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] });
    },
  });
}

export function useUpdateAdminUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: Partial<AdminUser> & { id: number }) => {
      const { data } = await api.patch(`/admin/users/${id}/`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });
}

export function useDeactivateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/admin/users/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] });
    },
  });
}

// ─── System & Integrationen ──────────────────────────────────────────────────

export function useSystemHealth() {
  return useQuery({
    queryKey: ["admin-system-health"],
    queryFn: async () => {
      const { data } = await api.get<SystemHealth>("/admin/system-health/");
      return data;
    },
    refetchInterval: 30000,
  });
}

export function useAdminIntegrations() {
  return useQuery({
    queryKey: ["admin-integrations"],
    queryFn: async () => {
      const { data } = await api.get<AdminIntegration[]>("/admin/integrations/");
      return data;
    },
  });
}

export function useForceSync() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (integrationId: number) => {
      const { data } = await api.post(
        `/admin/integrations/${integrationId}/force-sync/`
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-integrations"] });
    },
  });
}

export function useAdminSyncLogs(params?: { status?: string }) {
  return useQuery({
    queryKey: ["admin-sync-logs", params],
    queryFn: async () => {
      const { data } = await api.get<AdminSyncLog[]>("/admin/sync-logs/", {
        params,
      });
      return data;
    },
  });
}

// ─── AI & Agents ─────────────────────────────────────────────────────────────

export function useAIStats() {
  return useQuery({
    queryKey: ["admin-ai-stats"],
    queryFn: async () => {
      const { data } = await api.get<AIStats>("/admin/ai-stats/");
      return data;
    },
  });
}

export function useAgentOverview() {
  return useQuery({
    queryKey: ["admin-agent-overview"],
    queryFn: async () => {
      const { data } = await api.get<AgentOverview>("/admin/agent-overview/");
      return data;
    },
  });
}
