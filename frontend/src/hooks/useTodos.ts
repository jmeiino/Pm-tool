import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, PersonalTodo, DailyPlan } from "@/lib/types";
import type { TodoCreateInput } from "@/lib/schemas";

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
    retry: false,
  });
}

export function useCreateTodo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: TodoCreateInput) => {
      const { data } = await api.post<PersonalTodo>("/todos/", input);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
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

export function useDeleteTodo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/todos/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}

export function useAiDailyPlanSuggestion(date: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      // First ensure a daily plan exists for this date
      try {
        await api.get(`/daily-plans/${date}/`);
      } catch {
        await api.post("/daily-plans/", { date });
      }
      const { data } = await api.post<DailyPlan>(
        `/daily-plans/${date}/ai-suggest/`
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["daily-plan", date] });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}

export function useReorderDailyPlan(date: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (items: { id: number; order: number }[]) => {
      const { data } = await api.post<DailyPlan>(
        `/daily-plans/${date}/reorder/`,
        { items }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["daily-plan", date] });
    },
  });
}

export function useAddToDailyPlan(date: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { todo: number; order?: number; scheduled_start?: string; time_block_minutes?: number }) => {
      const { data } = await api.post<DailyPlan>(
        `/daily-plans/${date}/add-item/`,
        input
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["daily-plan", date] });
    },
  });
}
