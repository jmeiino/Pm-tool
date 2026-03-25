import { useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  AgentTask,
  AgentProfile,
  AgentCompanyStatus,
  PaginatedResponse,
} from "@/lib/types";

export function useAgentTasks() {
  return useQuery({
    queryKey: ["agent-tasks"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<AgentTask>>("/agents/tasks/");
      return data;
    },
    refetchInterval: 15000,
  });
}

export function useAgentTask(taskId: number) {
  return useQuery({
    queryKey: ["agent-task", taskId],
    queryFn: async () => {
      const { data } = await api.get<AgentTask>(`/agents/tasks/${taskId}/`);
      return data;
    },
    enabled: !!taskId,
    refetchInterval: 5000,
  });
}

export function useAgentProfiles() {
  return useQuery({
    queryKey: ["agent-profiles"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<AgentProfile>>("/agents/profiles/");
      return data;
    },
  });
}

export function useAgentCompanyStatus() {
  return useQuery({
    queryKey: ["agent-company-status"],
    queryFn: async () => {
      const { data } = await api.get<AgentCompanyStatus>("/agents/company/status/");
      return data;
    },
    refetchInterval: 10000,
  });
}

export function useDelegateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      issue_id: number;
      priority?: number;
      task_type?: string;
      instructions?: string;
    }) => {
      const { data } = await api.post<AgentTask>("/agents/tasks/delegate/", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-tasks"] });
    },
  });
}

export function useReplyToAgent(taskId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { content: string; decision_option?: string }) => {
      const { data } = await api.post(`/agents/tasks/${taskId}/reply/`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-task", taskId] });
    },
  });
}

export function useCancelTask(taskId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/agents/tasks/${taskId}/cancel/`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["agent-task", taskId] });
    },
  });
}

export function useAgentTaskStream(taskId: number, enabled = true) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!enabled || !taskId) return;

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const es = new EventSource(`${baseUrl}/agents/tasks/${taskId}/stream/`);

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "new_message") {
          queryClient.setQueryData<AgentTask>(
            ["agent-task", taskId],
            (old) => {
              if (!old?.messages) return old;
              return {
                ...old,
                messages: [...old.messages, data.message],
              };
            }
          );
        } else if (data.type === "status_changed") {
          queryClient.setQueryData<AgentTask>(
            ["agent-task", taskId],
            (old) => {
              if (!old) return old;
              return { ...old, status: data.new_status };
            }
          );
        }
      } catch {
        // Ignore parse errors
      }
    };

    es.onerror = () => {
      es.close();
    };

    return () => es.close();
  }, [taskId, enabled, queryClient]);
}
