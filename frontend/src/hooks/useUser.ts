import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  timezone: string;
  daily_capacity_hours: number;
  preferences: Record<string, unknown>;
  is_staff: boolean;
  is_active: boolean;
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ["current-user"],
    queryFn: async () => {
      const { data } = await api.get<UserProfile>("/users/me/");
      return data;
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (update: Partial<UserProfile>) => {
      const { data } = await api.patch<UserProfile>("/users/me/", update);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["current-user"] });
    },
  });
}
