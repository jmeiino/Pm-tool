import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, PersonalTodo, DailyPlan } from "@/lib/types";

export function useTodos(filters?: Record<string, string>) {
  const params = new URLSearchParams(filters);
  return useQuery({
    queryKey: ["todos", filters],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<PersonalTodo>>(
        `/todos/?${params.toString()}`
      );
      return data;
    },
  });
}

export function useDailyPlan(date: string) {
  return useQuery({
    queryKey: ["daily-plan", date],
    queryFn: async () => {
      const { data } = await api.get<DailyPlan>(`/daily-plans/${date}/`);
      return data;
    },
    enabled: !!date,
  });
}

export function useUpdateTodo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...data }: Partial<PersonalTodo> & { id: number }) => {
      const { data: result } = await api.patch<PersonalTodo>(`/todos/${id}/`, data);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}

export function useAiDailyPlanSuggestion(date: string) {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<DailyPlan>(
        `/daily-plans/${date}/ai_suggest/`
      );
      return data;
    },
  });
}
